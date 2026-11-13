#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gama_decision_l0.py — GAMA + BH-Decision 3-Gate Closed-Loop Runtime (L0 Engine)

Ujedinjuje:
  1. Gate 1 (Pre-Action Decision Intelligence):
     - Deterministički precheck (0 ms, 0 tokena) sa zaštitom od citiranih lažnih pozitiva
       (npr. `echo "rm -rf /"`) i detekcijom obfusciranih injekcija (`base64 -d | sh`, `dd of=/dev/`).
     - 4-Tier Action & Risk klasifikacija: READ | DRAFT | SEND | IRREVERSIBLE.
     - Kaskadni izbor modela (zamjenjuje udaljeni MCP `cascade_pick` u 0 dodatnih LLM turnova).
     - Prediktivni ugovor o dokazu (`expected_evidence_spec`) koji programira Gate 3.
     - Kalibracija vjerovatnoća (Temperature Scaling T* nad logitima + abstention prag).
  2. Gate 2 (In-Action Execution & Risk-Adaptive Sandboxing):
     - Verdict: allow | sandbox | ask | deny.
     - Za srednji rizik/nesigurnost preporučuje `srt` offline sandbox ili `fsundo` checkpoint.
  3. Gate 3 (Post-Action Evidence Gate / ProofGate):
     - `verify_evidence(envelope, tool_result)` provjerava `expected_evidence_spec` i izdaje
       kriptografski vezan `EvidenceReceipt` sa `decision_hash`.

Flag: GAMA_DECISION_L0=1 (default ON; "0" gasi).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

# Optional host-provided classifiers. In the public core these are absent, so the
# engine falls back to its deterministic heuristics. Integrators may inject their
# own modules by assigning to these names before calling decide_request().
_R2 = None
_RG = None
_GI = None

# ---------------------------------------------------------------------------
# Konfiguracija i kalibracioni parametri (Temperature Scaling T*)
# ---------------------------------------------------------------------------
DEFAULT_CALIB_FILE = os.environ.get("BH_DECISION_CALIB_FILE", "calibration.json")


def _resolve_calib_temp(env_default: float = 1.45) -> float:
    """T* iz calibration.json ako postoji; inace fallback na env BH_DECISION_TEMP."""
    env_raw = os.environ.get("BH_DECISION_TEMP")
    env_temp = float(env_raw) if env_raw not in (None, "") else env_default
    calib_path = os.environ.get("BH_DECISION_CALIB_FILE", DEFAULT_CALIB_FILE)
    try:
        if calib_path and os.path.exists(calib_path):
            with open(calib_path, encoding="utf-8") as handle:
                value = float(json.load(handle).get("temperature"))
            if value > 0:
                return value
    except Exception:
        pass
    return env_temp


CALIB_TEMP = _resolve_calib_temp()
THRESH_CONFIDENCE = float(os.environ.get("BH_DECISION_CONFIDENCE", "0.80"))
THRESH_ESCALATION = float(os.environ.get("BH_DECISION_ESCALATION", "0.65"))
THRESH_ABSTAIN = float(os.environ.get("BH_DECISION_ABSTAIN", "0.40"))
CACHE_TTL_S = float(os.environ.get("BH_DECISION_CACHE_TTL_S", "300"))

# ---------------------------------------------------------------------------
# Deterministička pravila (Precheck v2 — prošireni bh-decision + anti-injection)
# ---------------------------------------------------------------------------
_BENIGN_ECHO_RE = re.compile(
    r"^\s*(?:echo|printf)\s+(['\"])(?:(?!\1).)*\1\s*$", re.I
)
_DANGEROUS_CHAIN_RE = re.compile(
    r"[;|`]|(\$\()|\|\s*(?:sh|bash|zsh|dash|ksh|python\d*|perl|ruby|node|dd|sudo)\b",
    re.I,
)
_EXPLAIN_ONLY_RE = re.compile(
    r"^\s*(?:sta\s+radi|šta\s+radi|objasni|explain|what\s+does|kako\s+radi|sta\s+znaci|šta\s+znači)\b",
    re.I,
)

_DESTRUCTIVE_RULES: List[Tuple[re.Pattern[str], str, float]] = [
    (re.compile(r"\brm\s+[^;|&]*-[a-zA-Z]*[rR][a-zA-Z]*f|\brm\s+[^;|&]*-[a-zA-Z]*f[a-zA-Z]*[rR]|\brm\s+-rf\s+/", re.I), "rm-recursive", 0.95),
    (re.compile(r"\bdrop\s+(?:table|database|schema)\b|\btruncate\s+table\b", re.I), "sql-drop", 0.95),
    (re.compile(r"\bgit\s+push\b[^;|&]*--force\b|\bgit\s+reset\s+--hard\b", re.I), "git-destructive", 0.88),
    (re.compile(r"\b(?:delete|drop)\b[^;|&]*\b(?:database|bazu|podataka)\b", re.I), "delete-database", 0.92),
    (re.compile(r"\b(?:obri[sš]i|izbri[sš]i|obrisati|izbrisati)\b[^;|&]*\b(?:sve|bazu|podatke|podataka|baze|disk|tabelu)\b", re.I), "obrisi-bazu", 0.92),
    (re.compile(r"\b(?:format\s+[a-z]:|mkfs(?:\.[a-z0-9]+)?\b|wipefs\b|fdisk\b|parted\b)", re.I), "format-disk", 0.98),
    (re.compile(r"\bdd\s+[^;|&]*\bof=/dev/(?:sd[a-z]|nvme\d+n\d+|vd[a-z]|xvd[a-z]|mmcblk\d+|loop\d+|null\b)", re.I), "dd-raw-device", 0.96),
    (re.compile(r"\bbase64\s+(?:-d|--decode)\b[^|]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|dash|dd|python\d*|perl)\b", re.I), "obfuscated-base64-exec", 0.97),
    (re.compile(r"\b(?:curl|wget)\b[^|]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh|python\d*)\b", re.I), "pipe-url-to-shell", 0.90),
    (re.compile(r"\b(?:ignore\s+(?:all\s+)?previous\s+instructions|zanemari\s+(?:sve\s+)?prethodne\s+upute)\b", re.I), "prompt-injection", 0.89),
    (re.compile(r"\b(?:shutdown|poweroff|halt|init\s+0|init\s+6)\b", re.I), "system-poweroff", 0.94),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.I), "fork-bomb", 0.99),
]

_SEND_RE = re.compile(
    r"\b(?:po[sš]alji|po[sš]aljite|isporu[cč]i|objavi|publikuj|send|publish|broadcast|tweet|postaj)\b"
    r".*\b(?:mail|email|mejl|poruk|wa|whatsapp|viber|sms|fakturu|ponudu|klijentu|kupcu|na\s+produkciju)\b"
    r"|\b(?:mail|wa_send|wa_send_file|send_file)\b",
    re.I,
)
_DRAFT_RE = re.compile(
    r"\b(?:napi[sš]i|napravi|kreiraj|izmijeni|promijeni|uredi|refaktori[sš]i|dodaj|implementiraj|"
    r"snimi|sa[cč]uvaj|generi[sš]i|write|create|edit|update|patch|refactor|fix|popravi)\b",
    re.I,
)
_COMPLEX_HARD_RE = re.compile(
    r"\b(?:arhitektur|mikroservis|distributed|kriptograf|sigurnosn\w+\s+audit|optimizuj|"
    r"migracij|orchestrat|multi-agent|dag|swarm|refactor\s+entire|kompletn\w+\s+sistem|"
    r"deep\s+research|benchmark|kalibracij|sft|dpo|qlora)\b",
    re.I,
)
_AMBIGUOUS_SHORT_RE = re.compile(
    r"^\s*(?:ovo|to|ono|uradi\s+to|popravi\s+to|fix\s+it|do\s+it|hm+|\?+)\s*$",
    re.I,
)

# Lightweight deterministic domain/intent fallback used when no host-provided
# classifiers are wired in. Keeps the public core self-contained.
_SQL_HINT_RE = re.compile(
    r"\b(?:select|with|insert\s+into|update|delete\s+from|baza|bazi|bazu|sql|upit|"
    r"tabela|tabeli|tabelu|kupac|kupci|kupaca|zaliha)\b", re.I
)
_CODE_HINT_RE = re.compile(
    r"\b(?:python|funkcij\w*|kod|skript\w*|fajl|datotek\w*|patch|refaktor\w*|"
    r"test\w*|\.py\b)\b", re.I
)
_HC_HINT_RE = re.compile(r"\b(?:screenshot|klikni|otvori\s+program|hc|uia|tap)\b", re.I)
_MEDIA_HINT_RE = re.compile(r"\b(?:pdf|xlsx|excel|docx|slik\w*|video|tts|ocr)\b", re.I)


def _local_classify(text: str) -> Tuple[str, str, Optional[str]]:
    """Return (domain, intent_name, tool_hint) from deterministic keywords."""
    if _SQL_HINT_RE.search(text or ""):
        return "sql", "sql_query", "sql"
    if _CODE_HINT_RE.search(text or ""):
        return "code", "kod", None
    if _HC_HINT_RE.search(text or ""):
        return "hc", "hc_action", "hc"
    if _MEDIA_HINT_RE.search(text or ""):
        return "media", "media_make", None
    return "general", "opce", None

# READ_ONLY_SHELL_V1: bezazlene shell komande koje NE mijenjaju stanje (dozvoljene u READ tieru).
_READONLY_SHELL_RE = re.compile(
    r"^\s*(?:sudo\s+)?(?:df|du|ls|ll|la|cat|bat|head|tail|less|more|wc|grep|egrep|rg|find|fd|"
    r"ps|pgrep|top|htop|free|uptime|whoami|id|groups|hostname|uname|date|cal|pwd|echo|printf|"
    r"which|whereis|type|command\s+-v|file|stat|md5sum|sha256sum|sha1sum|diff|cmp|sort|uniq|cut|tr|"
    r"awk|sed\s+-n|jq|tree|nl|column|env|printenv|lsblk|lsusb|lspci|lscpu|nproc|vmstat|iostat|"
    r"mpstat|sar|ss|netstat|lsof|ip\s+(?:a|addr|r|route|link)\b|ifconfig|ping\s+-c\s*\d+\s+\S+|"
    r"dig|nslookup|host|curl\s+-s?I|rocm-smi|nvidia-smi|squeue|sinfo|sacct|module\s+(?:avail|list)|"
    r"systemctl\s+(?:status|is-active|is-enabled|list-units)|journalctl|docker\s+(?:ps|images|logs|inspect)|"
    r"git\s+(?:status|diff|log|show|branch|remote|rev-parse|ls-files|blame)|"
    r"python3?\s+--version|pip\s+(?:list|show)|node\s+--version|npm\s+ls)\b",
    re.I,
)
_READONLY_CHAIN_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")

# Mutirajući alati (za filtriranje u READ tieru i provjeru u decide_tool)
MUTATING_TOOLS = frozenset({
    "run", "shell", "bash", "sh", "exec", "gama_script", "gama_run", "ssh",
    "fanout", "fanout_smart", "fanout_all", "write_file", "fs_write", "fs_edit",
    "edit", "write", "apply_patch", "delete_file", "file_move", "file_copy",
    "sql_write", "mail", "wa_send", "wa_send_file", "send_file", "hc", "hands",
    "uiact", "tap", "type", "key",
})
SEND_TOOLS = frozenset({"mail", "wa_send", "wa_send_file", "send_file"})
DELETE_TOOLS = frozenset({"delete_file"})
WRITE_TOOLS = frozenset({"write_file", "fs_write", "fs_edit", "edit", "write", "apply_patch", "file_move", "file_copy"})
SHELL_TOOLS = frozenset({"run", "shell", "bash", "sh", "exec", "gama_script", "gama_run", "ssh", "fanout", "fanout_smart", "fanout_all"})
SQL_TOOLS = frozenset({"sql", "gama_sql"})

# ---------------------------------------------------------------------------
# In-memory metrika i keš
# ---------------------------------------------------------------------------
_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_METRICS: Dict[str, Any] = {
    "calls": 0,
    "cache_hits": 0,
    "precheck_hits": 0,
    "precheck_misses": 0,
    "tool_checks": 0,
    "tool_blocked": 0,
    "evidence_checks": 0,
    "evidence_verified": 0,
    "evidence_failed": 0,
    "escalations": 0,
    "latencies_ms": [],
}


def enabled() -> bool:
    return os.environ.get("GAMA_DECISION_L0", "1").strip().lower() not in ("0", "false", "no", "off")


def fnv1a_hex(text: str) -> str:
    h = 0x811C9DC5
    for b in (text or "").encode("utf-8", "replace"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def _norm_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def calibrate_probs(logits: Dict[str, float], temp: float = CALIB_TEMP) -> Dict[str, float]:
    """Temperature scaling nad sirovim logitima: p_i = exp(z_i / T) / sum_j exp(z_j / T)."""
    if not logits:
        return {}
    t = max(0.05, float(temp))
    mx = max(logits.values())
    exps = {k: math.exp((v - mx) / t) for k, v in logits.items()}
    total = sum(exps.values()) or 1.0
    return {k: round(v / total, 4) for k, v in exps.items()}


def _is_benign_quoted_or_explain(task: str) -> bool:
    """Sprječava lažni pozitiv kada korisnik samo ispisuje string (`echo "rm -rf /"`) ili pita za objašnjenje."""
    t = (task or "").strip()
    if not t:
        return False
    if _BENIGN_ECHO_RE.match(t) and not _DANGEROUS_CHAIN_RE.search(t):
        return True
    if _EXPLAIN_ONLY_RE.match(t) and not _DANGEROUS_CHAIN_RE.search(t):
        return True
    return False


def match_destructive(task: str) -> Optional[Tuple[str, float]]:
    """Vraća (rule_id, risk_score) ako zadatak sadrži stvarnu destruktivnu komandu ili injekciju."""
    t = (task or "").strip()
    if not t or _is_benign_quoted_or_explain(t):
        return None
    for rx, rule_id, score in _DESTRUCTIVE_RULES:
        if rx.search(t):
            return (rule_id, score)
    return None


def _assess_complexity(task: str) -> Tuple[str, Dict[str, float], str, List[str]]:
    """Vraća (complexity_level, probs, model_pick, escalation_chain)."""
    t = (task or "").strip()
    n = len(t)
    hard_hits = len(_COMPLEX_HARD_RE.findall(t))
    if hard_hits >= 2 or n > 600:
        logits = {"low": -1.2, "medium": 0.8, "high": 2.4}
        probs = calibrate_probs(logits)
        return (
            "high",
            probs,
            "deepseek/deepseek-v4.1-flash-1017",
            ["deepseek/deepseek-v4.1-flash-1017", "deepseek-chat", "anthropic/claude-sonnet-4-5"],
        )
    if hard_hits == 1 or n > 160:
        logits = {"low": 0.2, "medium": 2.1, "high": 0.5}
        probs = calibrate_probs(logits)
        return (
            "medium",
            probs,
            "deepseek-chat",
            ["deepseek-chat", "deepseek/deepseek-v4.1-flash-1017"],
        )
    logits = {"low": 2.3, "medium": 0.4, "high": -1.0}
    probs = calibrate_probs(logits)
    return (
        "low",
        probs,
        "deepseek-chat",
        ["deepseek-chat", "deepseek/deepseek-v4.1-flash-1017"],
    )


def _expected_evidence_for(tier: str, domain: str, intent_name: str, tool_hint: Optional[str]) -> Dict[str, Any]:
    """Gate 1 -> Gate 3 ugovor: definiše šta Post-Action ProofGate mora provjeriti."""
    if tier == "IRREVERSIBLE":
        return {
            "kind": "destructive_guard",
            "requires_human_approval": True,
            "must_have_audit_hash": True,
            "must_snapshot_before": True,
        }
    if tier == "SEND" or tool_hint in SEND_TOOLS:
        return {
            "kind": "external_send",
            "requires_explicit_send_verb": True,
            "must_have_audit_hash": True,
            "must_record_recipient": True,
        }
    if domain == "sql" or tool_hint in SQL_TOOLS or intent_name.startswith("sql_"):
        return {
            "kind": "sql_rows",
            "read_only": True,
            "must_have_evidence_source": True,
            "forbid_unverified_numbers": True,
        }
    if domain == "code" or intent_name == "kod":
        return {
            "kind": "code_verified",
            "must_change_sha256": True,
            "must_pass_semgrep_diff": True,
        }
    if domain == "hc" or intent_name.startswith("hc_"):
        return {
            "kind": "hc_verified",
            "must_have_node_response": True,
        }
    if tier == "DRAFT":
        return {
            "kind": "file_sha256",
            "must_change_sha256": True,
            "must_pass_semgrep_diff": False,
        }
    return {
        "kind": "read_only",
        "forbid_mutations": True,
    }


def _tool_bundle_for(domain: str, intent_name: str, intent_tool: Optional[str], tier: str) -> List[str]:
    bundle: List[str] = []
    if intent_tool:
        bundle.append(intent_tool)
    if domain == "sql" or intent_name.startswith("sql_"):
        bundle.extend(["sql", "brain_search"])
    elif domain == "code" or intent_name == "kod":
        bundle.extend(["fs_read", "fs_edit", "fs_write", "fs_grep", "fs_glob", "test_run", "git"])
    elif domain == "hc" or intent_name.startswith("hc_"):
        bundle.extend(["hc", "fleet_status", "fleet"])
    elif domain == "media" or intent_name.startswith("media_"):
        bundle.extend(["make_doc", "make_pdf", "make_xlsx"])
    else:
        bundle.extend(["fs_read", "fs_grep", "fs_glob", "brain_search"])

    if tier == "READ":
        bundle = [t for t in bundle if t not in MUTATING_TOOLS]
    seen = set()
    out = []
    for t in bundle:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# Pravac A: Zero-Latency Speculative Execution & Deterministic Slot Filler (DSF)
# ---------------------------------------------------------------------------
_SESSION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}
_HISTORY_LOCK = threading.Lock()


def update_session_slots(sid: str, text: str, slots: Dict[str, Any]) -> None:
    with _HISTORY_LOCK:
        if sid not in _SESSION_HISTORY:
            _SESSION_HISTORY[sid] = []
        _SESSION_HISTORY[sid].append({
            "text": text,
            "slots": slots,
            "ts": time.time()
        })
        if len(_SESSION_HISTORY[sid]) > 10:
            _SESSION_HISTORY[sid].pop(0)


def get_last_slot_from_history(sid: str, key: str) -> Optional[Any]:
    with _HISTORY_LOCK:
        if sid not in _SESSION_HISTORY:
            return None
        for entry in reversed(_SESSION_HISTORY[sid]):
            val = entry["slots"].get(key)
            if val:
                return val
        return None


def extract_dsf_slots(text: str, sid: str = "default") -> Dict[str, Any]:
    """
    DSF (Deterministic Slot Filler) za automatsko i anaforsko izdvajanje filePath i sql parametara u <2ms.
    """
    slots = {"filePath": None, "sql": None}
    t = str(text or "")

    # 1. Eksplicitno izdvajanje filePath-a (prvo navodnici i backticks koji mogu imati razmake i dvotačke)
    path_quotes_re = re.compile(r'[`"\']([a-zA-Z0-9_\.\-\/: ]+\.[a-zA-Z0-9]+|/(?:[a-zA-Z0-9_\.\-:]+/)+[a-zA-Z0-9_\.\-:]+)[`"\']')
    m_q = path_quotes_re.search(t)
    if m_q:
        slots["filePath"] = m_q.group(1)
    else:
        # Bez navodnika - ne dozvoljavamo razmake radi izbjegavanja lažnih pozitivnih cijelih rečenica
        file_path_re = re.compile(
            r'(?:[a-zA-Z]:\\(?:[a-zA-Z0-9_\.\-]+\\)*[a-zA-Z0-9_\.\-]+|'
            r'/(?:[a-zA-Z0-9_\.\-:]+/)+[a-zA-Z0-9_\.\-:]+|'
            r'\b[a-zA-Z0-9_\.\-\/:_]+\.(?:py|ts|json|sql|md|txt|csv|xlsx|docx|yml|yaml|xml|sh|js|html|css|cfg|conf|ini|log)\b)'
        )
        m_p = file_path_re.search(t)
        if m_p:
            slots["filePath"] = m_p.group(0)

    # 2. Eksplicitno izdvajanje SQL-a (backticks ili klasični SELECT/WITH/UPDATE/DELETE/INSERT)
    m_sql_block = re.search(r'```sql\s*([\s\S]+?)```', t, re.I)
    if m_sql_block:
        slots["sql"] = m_sql_block.group(1).strip()
    else:
        sql_start_re = re.compile(r'\b(SELECT|WITH|UPDATE|INSERT\s+INTO|DELETE\s+FROM)\b', re.I)
        m_start = sql_start_re.search(t)
        if m_start:
            start_idx = m_start.start()
            sub = t[start_idx:]
            idx = sub.find(';')
            if idx != -1:
                slots["sql"] = sub[:idx+1].strip()
            else:
                slots["sql"] = sub.strip()

    # 3. Anaforska rezolucija ako slotovi nisu pronađeni eksplicitno
    if not slots["filePath"]:
        file_anaphora = re.compile(
            r'\b(?:u\s+njemu|iz\s+njega|taj\s+fajl|taj\s+file|taj\s+document|taj\s+dokument|'
            r'to|it|file|fajl|skriptu|skripta|u\s+fajl|u\s+datoteku|u\s+skriptu)\b',
            re.I
        )
        if file_anaphora.search(t):
            slots["filePath"] = get_last_slot_from_history(sid, "filePath")

    if not slots["sql"]:
        sql_anaphora = re.compile(
            r'\b(?:taj\s+upit|izvr[sš]i\s+to|run\s+it|execute\s+it|pokreni\s+ga|izvr[sš]i\s+ga|'
            r'query|upit|ga|it)\b',
            re.I
        )
        if sql_anaphora.search(t):
            slots["sql"] = get_last_slot_from_history(sid, "sql")

    # Ažuriramo istoriju za buduće anaforske reference
    update_session_slots(sid, t, slots)
    return slots


def speculative_evaluate(text: str, timeout_s: float = 0.15) -> Optional[str]:
    """
    Optional zero-latency speculative classifier.

    Sends a one-token guided-regex request to an OpenAI-compatible endpoint
    configured via ``BH_SPECULATIVE_URL`` (chat completions URL) and
    ``BH_SPECULATIVE_MODEL``. When unset the feature is disabled and ``None``
    is returned, so the deterministic heuristic remains authoritative.
    """
    import urllib.request
    import urllib.error

    url = os.environ.get("BH_SPECULATIVE_URL", "").strip()
    if not url:
        return None
    payload = {
        "model": os.environ.get("BH_SPECULATIVE_MODEL", "risk-classifier"),
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Klasifikuj rizik i tier akcije za ovaj upit: {text}\n"
                    "Odgovori isključivo jednim slovom:\n"
                    "R - ako je akcija samo čitanje (READ)\n"
                    "D - ako akcija mijenja fajlove ili lokalno stanje (DRAFT)\n"
                    "S - ako šalje mail ili poruku vani (SEND)\n"
                    "I - ako je akcija destruktivna ili nepovratna (IRREVERSIBLE)"
                )
            }
        ],
        "temperature": 0.0,
        "max_tokens": 1,
        "extra_body": {
            "guided_regex": "[RDSI]"
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode("utf-8"))
                choices = res_body.get("choices", [])
                if choices:
                    val = choices[0].get("message", {}).get("content", "").strip()
                    if val in ("R", "D", "S", "I"):
                        return val
    except Exception:
        pass
    return None


def decide_request(
    text: str,
    sid: str = "default",
    profile: str = "general",
    hist_len: int = 0,
) -> Dict[str, Any]:
    """
    Gate 1: L0 Pre-Routing, Risk Assessment & DecisionEnvelope generator (<5 ms).
    Ne troši nijedan LLM tool-call turn.
    """
    t0 = time.perf_counter()
    raw = str(text or "")
    norm = _norm_key(raw)
    cache_key = f"{profile}:{hist_len}:{norm}"

    with _LOCK:
        _METRICS["calls"] += 1
        hit = _CACHE.get(cache_key)
        if hit and (time.time() - hit[0]) <= CACHE_TTL_S:
            _METRICS["cache_hits"] += 1
            cached = dict(hit[1])
            cached["cached"] = True
            cached["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
            return cached

    # 1. Precheck: deterministička pravila za destruktivne komande i injekcije
    destr = match_destructive(raw)
    if destr is not None:
        rule_id, risk_val = destr
        with _LOCK:
            _METRICS["precheck_hits"] += 1
            _METRICS["escalations"] += 1
        dec_id = f"pre-{fnv1a_hex(norm)}"
        env: Dict[str, Any] = {
            "ok": True,
            "decision_id": dec_id,
            "provider": "bh-decision-l0",
            "model": "deterministic-rules-v2",
            "rule_id": rule_id,
            "tier": "IRREVERSIBLE",
            "risk_level": "high",
            "risk": risk_val,
            "confidence": 1.0,
            "verdict": "deny" if profile != "full" else "ask",
            "decision": "deny" if profile != "full" else "ask",
            "requires_escalation": True,
            "abstained": [],
            "route": "block" if profile != "full" else "agent",
            "engine_hint": "block",
            "domain": "security",
            "intent": "block",
            "complexity": "low",
            "model_pick": "deepseek-chat",
            "escalation_chain": ["deepseek-chat"],
            "tool_bundle": [],
            "expected_evidence_spec": _expected_evidence_for("IRREVERSIBLE", "security", "block", None),
            "decisions": {
                "risk_level": {"selected": "high", "probabilities": {"low": 0.0, "medium": 0.0, "high": 1.0}},
                "needs_approval": {"selected": True, "probabilities": {"true": 1.0, "false": 0.0}},
            },
            "reason": f"precheck:{rule_id}",
            "cached": False,
        }
        canon = json.dumps(env, ensure_ascii=False, sort_keys=True)
        env["decision_hash"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
        ms = round((time.perf_counter() - t0) * 1000.0, 3)
        env["latency_ms"] = ms
        with _LOCK:
            _METRICS["latencies_ms"].append(ms)
            if len(_METRICS["latencies_ms"]) > 500:
                _METRICS["latencies_ms"] = _METRICS["latencies_ms"][-500:]
            _CACHE[cache_key] = (time.time(), dict(env))
        return env

    with _LOCK:
        _METRICS["precheck_misses"] += 1

    # 2. Spajanje signala iz router_gate i gama_intent u jednom prolazu
    rg_res: Dict[str, Any] = {}
    if _RG is not None:
        try:
            rg_res = _RG.apply(raw)
        except Exception:
            rg_res = {}
    elif _R2 is not None:
        try:
            rg_res = _R2.classify(raw)
        except Exception:
            rg_res = {}

    gi_res: Dict[str, Any] = {}
    if _GI is not None:
        try:
            gi_res = _GI.classify(raw)
        except Exception:
            gi_res = {}

    eng = str(rg_res.get("engine") or gi_res.get("engine") or "chat")
    dom = str(rg_res.get("domain") or "general")
    intent_name = str(gi_res.get("intent") or "opce")
    intent_tool = gi_res.get("tool") or rg_res.get("forced_tool")
    r_risk = float(rg_res.get("risk") or 0.05)

    if _RG is None and _R2 is None and _GI is None:
        dom, intent_name, intent_tool = _local_classify(raw)

    # Ako je router2 označio "block", ali je naš _is_benign_quoted_or_explain rekao da je samo echo/explain:
    if eng == "block" and _is_benign_quoted_or_explain(raw):
        eng = "chat"
        r_risk = 0.05

    # 3. Određivanje Action Tiera (READ | DRAFT | SEND | IRREVERSIBLE) i kalibriranih vjerovatnoća
    if eng == "block" or r_risk >= 0.85:
        tier = "IRREVERSIBLE"
        risk_logits = {"low": -2.0, "medium": 0.2, "high": 3.0}
        verdict = "deny" if profile != "full" else "ask"
    elif _SEND_RE.search(raw) and not _is_benign_quoted_or_explain(raw):
        tier = "SEND"
        r_risk = max(r_risk, 0.65)
        risk_logits = {"low": -1.0, "medium": 1.8, "high": 1.2}
        verdict = "ask"
    elif _DRAFT_RE.search(raw) or dom == "code" or intent_name in ("kod", "napravi_ponudu", "napravi_dokument", "mem_write"):
        tier = "DRAFT"
        r_risk = max(r_risk, 0.25)
        risk_logits = {"low": 1.2, "medium": 2.0, "high": -0.8}
        verdict = "allow"
    else:
        tier = "READ"
        r_risk = min(r_risk, 0.15)
        risk_logits = {"low": 2.8, "medium": 0.1, "high": -1.8}
        verdict = "allow"

    # 3.5 Pravac A: DSF & Zero-Latency Speculative Execution
    slots = extract_dsf_slots(raw, sid)

    timeout_s = float(os.environ.get("BH_SPECULATIVE_TIMEOUT", "0.15"))
    spec_char = speculative_evaluate(raw, timeout_s=timeout_s)
    spec_tier = None
    if spec_char == "R":
        spec_tier = "READ"
    elif spec_char == "D":
        spec_tier = "DRAFT"
    elif spec_char == "S":
        spec_tier = "SEND"
    elif spec_char == "I":
        spec_tier = "IRREVERSIBLE"

    # Speculative Safety Override: ako spekulativni model detektuje veći nivo rizika od našeg lokalnog, radimo override
    tier_hierarchy = {"READ": 1, "DRAFT": 2, "SEND": 3, "IRREVERSIBLE": 4}
    if spec_tier and tier_hierarchy.get(spec_tier, 0) > tier_hierarchy.get(tier, 0):
        tier = spec_tier
        if tier == "IRREVERSIBLE":
            risk_logits = {"low": -2.0, "medium": 0.2, "high": 3.0}
            verdict = "deny" if profile != "full" else "ask"
            r_risk = max(r_risk, 0.85)
        elif tier == "SEND":
            risk_logits = {"low": -1.0, "medium": 1.8, "high": 1.2}
            verdict = "ask"
            r_risk = max(r_risk, 0.65)
        elif tier == "DRAFT":
            risk_logits = {"low": 1.2, "medium": 2.0, "high": -0.8}
            verdict = "allow"
            r_risk = max(r_risk, 0.25)

    risk_probs = calibrate_probs(risk_logits)
    risk_selected = max(risk_probs, key=lambda k: risk_probs[k])

    # 4. Kalibracija confidence-a i provjera apstinencije (rješava Jev 0/1 problem)
    abstained: List[str] = []
    if not norm or _AMBIGUOUS_SHORT_RE.match(norm):
        intent_logits = {"chat": 0.4, "coding": 0.35, "research": 0.3, "other": 0.45}
        intent_probs = calibrate_probs(intent_logits)
        conf = max(intent_probs.values())
        abstained.append("intent")
    else:
        base_conf = max(float(rg_res.get("confidence") or 0.6), float(gi_res.get("confidence") or 0.0))
        # Mapiramo u logit marginu pa kroz Temperature Scaling T*
        margin = (base_conf - 0.5) * 4.5
        intent_logits = {"primary": margin + 1.6, "alt_1": 0.0, "alt_2": -0.8}
        intent_probs = calibrate_probs(intent_logits)
        conf = round(max(intent_probs.values()), 4)
        if conf < THRESH_ABSTAIN:
            abstained.append("intent")

    if abstained:
        conf = min(conf, 0.50)

    requires_escalation = bool(
        conf < THRESH_ESCALATION
        or len(abstained) > 0
        or tier in ("IRREVERSIBLE", "SEND")
    )
    if requires_escalation:
        with _LOCK:
            _METRICS["escalations"] += 1

    # Risk-Adaptive Sandboxing (Gate 2): kada je DRAFT, a confidence srednji, preporuči sandbox/checkpoint
    if tier == "DRAFT" and conf < THRESH_CONFIDENCE:
        verdict = "sandbox"

    complexity, comp_probs, model_pick, esc_chain = _assess_complexity(raw)
    tool_bundle = _tool_bundle_for(dom, intent_name, intent_tool, tier)
    expected_ev = _expected_evidence_for(tier, dom, intent_name, intent_tool)

    # Route za harness
    if verdict == "deny":
        route = "block"
    elif tier == "READ" and not abstained and len(norm) <= 60 and hist_len <= 2 and eng == "chat" and not intent_tool:
        route = "fast_chat"
    elif tier == "READ" and not abstained and eng == "chat" and not intent_tool:
        route = "chat_early"
    else:
        route = "agent"

    dec_id = f"dec-{fnv1a_hex(norm + ':' + tier)}"
    env = {
        "ok": True,
        "decision_id": dec_id,
        "provider": "bh-decision-l0",
        "model": f"gama-calibrated-l0-T{CALIB_TEMP}",
        "tier": tier,
        "risk_level": risk_selected,
        "risk": round(r_risk, 3),
        "confidence": conf,
        "verdict": verdict,
        "decision": "allow" if verdict in ("allow", "sandbox") else verdict,
        "sandbox_recommended": verdict == "sandbox",
        "requires_escalation": requires_escalation,
        "abstained": abstained,
        "route": route,
        "engine_hint": eng,
        "domain": dom,
        "intent": intent_name,
        "intent_tool": intent_tool,
        "complexity": complexity,
        "model_pick": model_pick,
        "escalation_chain": esc_chain,
        "tool_bundle": tool_bundle,
        "expected_evidence_spec": expected_ev,
        "filePath": slots["filePath"],
        "sql": slots["sql"],
        "speculative_execution": {
            "enabled": True,
            "slots": slots,
            "speculative_tier": spec_tier,
            "speculative_match": spec_tier == tier if spec_tier else True,
            "speculative_raw_char": spec_char,
        },
        "decisions": {
            "risk_level": {"selected": risk_selected, "probabilities": risk_probs},
            "complexity": {"selected": complexity, "probabilities": comp_probs},
            "needs_approval": {
                "selected": verdict in ("ask", "deny"),
                "probabilities": {"true": 1.0 if verdict in ("ask", "deny") else 0.05, "false": 0.0 if verdict in ("ask", "deny") else 0.95},
            },
        },
        "reason": f"l0:{tier.lower()}:{intent_name}",
        "cached": False,
    }
    canon = json.dumps(env, ensure_ascii=False, sort_keys=True)
    env["decision_hash"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    ms = round((time.perf_counter() - t0) * 1000.0, 3)
    env["latency_ms"] = ms

    with _LOCK:
        _METRICS["latencies_ms"].append(ms)
        if len(_METRICS["latencies_ms"]) > 500:
            _METRICS["latencies_ms"] = _METRICS["latencies_ms"][-500:]
        _CACHE[cache_key] = (time.time(), dict(env))

    return env


def decide_tool(
    tool: str,
    args: Optional[Dict[str, Any]] = None,
    req_ctx: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Gate 2: In-process Pre-Tool Execution Gate (<1 ms).
    Provjerava konkretan poziv alata i argumente u odnosu na DecisionEnvelope iz Gate 1.
    """
    t0 = time.perf_counter()
    nm = str(tool or "").strip()
    a = args if isinstance(args, dict) else {}
    ctx = req_ctx if isinstance(req_ctx, dict) else {}
    user_text = str(ctx.get("user_text") or "")

    with _LOCK:
        _METRICS["tool_checks"] += 1

    # Izvuci tekstualni payload komande/skripte iz argumenata
    cmd_payload = " ".join(
        str(a.get(k) or "")
        for k in ("cmd", "command", "script", "code", "query", "task", "prompt", "goal", "text", "args")
        if a.get(k)
    ).strip()

    # 1. Provjeri destruktivne obrasce u samim argumentima alata (npr. shell/bash/hc/ssh)
    if nm in SHELL_TOOLS or nm in ("hc", "hands", "sandbox", "opencode", "claude", "code"):
        destr = match_destructive(cmd_payload)
        if destr is not None:
            rule_id, risk_val = destr
            # Ako korisnik NIJE izričito tražio tu destruktivnu akciju, blokiraj odmah
            user_destr = match_destructive(user_text) if user_text else None
            if not user_destr:
                with _LOCK:
                    _METRICS["tool_blocked"] += 1
                res = {
                    "ok": False,
                    "decision": "deny",
                    "verdict": "deny",
                    "tier": "IRREVERSIBLE",
                    "risk": risk_val,
                    "rule_id": rule_id,
                    "reason": f"bh_decision_l0: destruktivni payload ({rule_id}) bez izričite naredbe korisnika",
                    "expected_evidence_spec": _expected_evidence_for("IRREVERSIBLE", "security", "block", nm),
                }
                res["decision_hash"] = hashlib.sha256(
                    json.dumps(res, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()
                res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
                return res

    # 2. Provjeri SEND alate (mail, wa_send...)
    if nm in SEND_TOOLS:
        has_send_intent = bool(user_text and _SEND_RE.search(user_text) and not _is_benign_quoted_or_explain(user_text))
        if not has_send_intent and ctx.get("tier") != "SEND":
            with _LOCK:
                _METRICS["tool_blocked"] += 1
            res = {
                "ok": False,
                "decision": "deny",
                "verdict": "deny",
                "tier": "SEND",
                "risk": 0.75,
                "reason": f"bh_decision_l0: alat '{nm}' šalje vanjsku poruku bez izričite naredbe korisnika",
                "expected_evidence_spec": _expected_evidence_for("SEND", "comm", "mail", nm),
            }
            res["decision_hash"] = hashlib.sha256(
                json.dumps(res, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
            return res

    # 2.b Provjera mutating alata za READ tier
    # READ_ONLY_SHELL_V1: read-only shell komande (df, ls, cat, git status...) su dozvoljene u READ tieru.
    _readonly_shell = False
    if nm in SHELL_TOOLS and cmd_payload:
        _parts = [p.strip() for p in _READONLY_CHAIN_SPLIT_RE.split(cmd_payload) if p.strip()]
        if _parts and all(_READONLY_SHELL_RE.match(p) for p in _parts):
            _readonly_shell = True
    if ctx.get("tier") == "READ" and nm in MUTATING_TOOLS and not _readonly_shell:
        with _LOCK:
            _METRICS["tool_blocked"] += 1
        res = {
            "ok": False,
            "decision": "deny",
            "verdict": "deny",
            "tier": "READ",
            "risk": 0.50,
            "reason": f"bh_decision_l0: alat '{nm}' vrši mutaciju što je zabranjeno u READ tieru",
            "expected_evidence_spec": _expected_evidence_for("READ", "security", "block", nm),
        }
        res["decision_hash"] = hashlib.sha256(
            json.dumps(res, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
        return res

    # 3. Odredi tier i expected_evidence_spec za dozvoljeni alat
    if nm in DELETE_TOOLS:
        tier = "IRREVERSIBLE"
        ev = {"kind": "delete_verified", "must_not_exist": True, "path": a.get("path") or a.get("filePath")}
    elif nm in WRITE_TOOLS:
        tier = "DRAFT"
        ev = {"kind": "file_sha256", "must_change_sha256": True, "path": a.get("path") or a.get("filePath")}
    elif nm in SQL_TOOLS:
        tier = "READ"
        ev = {"kind": "sql_rows", "read_only": True, "must_have_evidence_source": True}
    elif nm in MUTATING_TOOLS:
        tier = "DRAFT"
        ev = {"kind": "command_rc", "must_check_rc": True}
    else:
        tier = "READ"
        ev = {"kind": "read_only", "forbid_mutations": True}

    parent_hash = str(ctx.get("decision_hash") or "")
    res = {
        "ok": True,
        "decision": "allow",
        "verdict": "allow",
        "tier": tier,
        "risk": 0.30 if tier == "DRAFT" else (0.70 if tier == "IRREVERSIBLE" else 0.05),
        "reason": f"bh_decision_l0:allow:{nm}",
        "parent_decision_hash": parent_hash,
        "expected_evidence_spec": ev,
    }
    res["decision_hash"] = hashlib.sha256(
        json.dumps(res, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
    return res


def verify_evidence(
    decision_envelope: Optional[Dict[str, Any]],
    tool_name: str,
    tool_result: Any,
) -> Dict[str, Any]:
    """
    Gate 3 (Post-Action ProofGate):
    Provjerava da li izlaz alata zadovoljava `expected_evidence_spec` iz Gate 1/2
    i izdaje `EvidenceReceipt` vezan za `decision_hash`.
    """
    env = decision_envelope if isinstance(decision_envelope, dict) else {}
    spec = env.get("expected_evidence_spec") or {}
    kind = str(spec.get("kind") or "read_only")
    r = tool_result if isinstance(tool_result, dict) else {"ok": bool(tool_result)}
    ok_flag = bool(r.get("ok", True))

    verified = ok_flag
    reasons: List[str] = []

    if kind == "delete_verified" and ok_flag:
        if r.get("verified") is False or r.get("exists") is True:
            verified = False
            reasons.append("delete_not_verified_on_disk")
    elif kind == "file_sha256" and ok_flag:
        if r.get("err") or r.get("error"):
            verified = False
            reasons.append("file_write_error")
    elif kind == "sql_rows" and ok_flag:
        if r.get("err") or r.get("error"):
            verified = False
            reasons.append("sql_error")

    with _LOCK:
        _METRICS["evidence_checks"] += 1
        if verified:
            _METRICS["evidence_verified"] += 1
        else:
            _METRICS["evidence_failed"] += 1

    receipt = {
        "decision_id": env.get("decision_id") or "",
        "decision_hash": env.get("decision_hash") or "",
        "tool": str(tool_name),
        "evidence_kind": kind,
        "verified": verified,
        "reasons": reasons,
        "ts": time.time(),
    }
    receipt["receipt_hash"] = hashlib.sha256(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return receipt


def status() -> Dict[str, Any]:
    """Vraća metriku L0 Decision & Evidence motora."""
    with _LOCK:
        lats = sorted(_METRICS["latencies_ms"])
        n = len(lats)
        p50 = lats[n // 2] if n else 0.0
        p95 = lats[min(n - 1, int(n * 0.95))] if n else 0.0
        avg = round(sum(lats) / n, 3) if n else 0.0
        hits = _METRICS["precheck_hits"]
        misses = _METRICS["precheck_misses"]
        total_pre = hits + misses
        return {
            "ok": True,
            "enabled": enabled(),
            "provider": "bh-decision-l0",
            "model": f"gama-calibrated-l0-T{CALIB_TEMP}",
            "calibration_temp": CALIB_TEMP,
            "thresholds": {
                "confidence": THRESH_CONFIDENCE,
                "escalation": THRESH_ESCALATION,
                "abstain": THRESH_ABSTAIN,
            },
            "calls": _METRICS["calls"],
            "cache_hits": _METRICS["cache_hits"],
            "precheck": {
                "hits": hits,
                "misses": misses,
                "coverage": round(hits / total_pre, 4) if total_pre else 0.0,
            },
            "tool_gate": {
                "checks": _METRICS["tool_checks"],
                "blocked": _METRICS["tool_blocked"],
            },
            "evidence_gate": {
                "checks": _METRICS["evidence_checks"],
                "verified": _METRICS["evidence_verified"],
                "failed": _METRICS["evidence_failed"],
            },
            "escalations": _METRICS["escalations"],
            "avg_latency_ms": avg,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
        }


def apply_prefix_stable_v1(
    schemas: List[Dict[str, Any]],
    system_prompt: str,
    dynamic_vars: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Primjenjuje PREFIX_STABLE_V1 pravilo stabilnosti KV-cache-a:
    1. Sortira šeme alata po imenu funkcije kako bi redoslijed bio potpuno deterministički.
    2. Izmješta dinamičke varijable na kraj system prompta.
    """
    # 1. Sortiranje šema alata
    sorted_schemas = sorted(
        schemas,
        key=lambda x: str(x.get("function", {}).get("name") or x.get("name") or "")
    )

    # 2. Pronalaženje i izmještanje dinamičkih varijabli na dno system prompta
    cleaned_prompt = system_prompt
    dynamic_block_lines = []

    # Definišemo uobičajene dinamičke regex obrasce u promptovima
    patterns = [
        (r"(?i)today's\s+date:\s*[^\n]+", "Date"),
        (r"(?i)current\s+time:\s*[^\n]+", "Time"),
        (r"(?i)session\s+id:\s*[^\n]+", "SID"),
        (r"(?i)sid:\s*[^\n]+", "SID"),
        (r"(?i)working\s+directory:\s*[^\n]+", "CWD"),
    ]

    for pat, label in patterns:
        matches = re.findall(pat, cleaned_prompt)
        for m in matches:
            cleaned_prompt = cleaned_prompt.replace(m, "")
            dynamic_block_lines.append(m.strip())

    if dynamic_vars:
        for k, v in sorted(dynamic_vars.items()):
            dynamic_block_lines.append(f"{k}: {v}")

    # Očistimo višestruke nove redove nastale brisanjem
    cleaned_prompt = re.sub(r"\n{3,}", "\n\n", cleaned_prompt).strip()

    if dynamic_block_lines:
        cleaned_prompt += "\n\n=== DYNAMIC CONTEXT (KV-CACHE STABLE) ===\n" + "\n".join(dynamic_block_lines)

    return sorted_schemas, cleaned_prompt


if __name__ == "__main__":
    for sample in [
        "rm -rf /",
        'echo "rm -rf /"',
        "echo cm0gLXJmIC8= | base64 -d | sh",
        "koliko ima kupaca u bazi demo",
        " pošalji mail kupcu ALFA sa ponudom",
        "napiši python funkciju za parsiranje CSV-a i snimi u test.py",
        "ovo",
    ]:
        res = decide_request(sample)
        print(
            f"{sample!r:62} -> tier={res['tier']:12} verdict={res['verdict']:7} "
            f"conf={res['confidence']:.2f} route={res['route']:10} ev={res['expected_evidence_spec']['kind']} ({res['latency_ms']} ms)"
        )
