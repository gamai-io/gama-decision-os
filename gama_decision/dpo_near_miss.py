#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Near-miss DPO generator for RLDF (Faza 2).

An early DPO run stopped at train_loss ~= 0.3218, the lower bound imposed by
label smoothing eps=0.1. Cause: `ok` vs `error` pairs are too easy to separate.

Ovaj generator pravi teze parove gdje chosen i rejected koriste ISTI
alat i skoro iste argumente, a razlika je semanticka:

  * sql_wrong_table      - sintaksno ispravan upit, pogresna tabela
  * sql_wrong_column     - sintaksno ispravan upit, pogresna kolona
  * path_lookalike       - skoro isti put (typo / pogresan sibling fajl)
  * numeric_hallucination- isti tool-call, plausible ali izmisljen broj
  * false_success_ack    - identican tool-call i error, lazni "uspjeh"

Real receipts (receipts.db) cuvaju samo args_sha256, ne i same
argumente. Zato su sinteticki parovi jasno oznaceni (`synthetic: true`)
i po potrebi ankorisani na stvarne `seq` brojeve radi provenance-a.
Real `status_flip` parovi se zadrzavaju kao trivijalna kontrola.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from difflib import SequenceMatcher

DEFAULT_DB = os.environ.get("GAMA_RECEIPTS_DB", "receipts.db")
DEFAULT_OUTPUT = os.environ.get("GAMA_DPO_OUTPUT", "dpo_near_miss.jsonl")
DEFAULT_REPORT = os.environ.get("GAMA_DPO_REPORT", "dpo_near_miss_report.json")
NEAR_MISS_THRESHOLD = 0.60

_CATEGORY_BASE_DIFFICULTY = {
    "sql_wrong_table": 0.72,
    "sql_wrong_column": 0.78,
    "path_lookalike": 0.82,
    "numeric_hallucination": 0.90,
    "false_success_ack": 0.95,
}


# ---------------------------------------------------------------------------
# Receipts
# ---------------------------------------------------------------------------
def load_receipts(db_path: str, limit: int | None = None) -> list[dict]:
    """Ucitaj receipts iz GTL baze. Baca FileNotFoundError/sqlite3.Error."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"receipts baza ne postoji: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        query = (
            "SELECT seq, tool, ok, status, ts, json "
            "FROM receipts ORDER BY seq ASC"
        )
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = conn.execute(query).fetchall()
    finally:
        conn.close()

    receipts = []
    for seq, tool, ok, status, ts, raw in rows:
        try:
            data = json.loads(raw) if raw else {}
        except (TypeError, ValueError):
            data = {}
        payload = data.get("payload") or {}
        inputs = payload.get("inputs") or {}
        extra = payload.get("extra") or {}
        receipts.append(
            {
                "seq": int(seq),
                "tool": tool,
                "ok": int(ok),
                "status": status,
                "ts": ts,
                "args_sha256": inputs.get("args_sha256") or "",
                "result_hash": payload.get("result_hash") or "",
                "reason": extra.get("reason") or "",
            }
        )
    return receipts


def _is_success(receipt: dict) -> bool:
    return receipt.get("ok") == 1 and receipt.get("status") == "ok"


# ---------------------------------------------------------------------------
# Rendering / similarity
# ---------------------------------------------------------------------------
def _dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _render(tool: str, args: dict, response: dict, final: str, thinking: str) -> str:
    return (
        f"<thinking>{thinking}</thinking>\n"
        f"<tool_call>{_dump({'name': tool, 'arguments': args})}</tool_call>\n"
        f"<tool_response>{_dump(response)}</tool_response>\n"
        f"<final>{final}</final>"
    )


def _args_similarity(args_a: dict, args_b: dict) -> float:
    a, b = _dump(args_a), _dump(args_b)
    if a == b:
        return 1.0
    return round(SequenceMatcher(None, a, b).ratio(), 4)


def _difficulty(category: str, similarity: float) -> float:
    base = _CATEGORY_BASE_DIFFICULTY.get(category, 0.5)
    return round(min(0.99, base * (0.85 + 0.15 * similarity)), 3)


# ---------------------------------------------------------------------------
# Pair construction
# ---------------------------------------------------------------------------
def _receipt_pair(success: dict, failure: dict) -> dict:
    tool = failure["tool"]
    chosen = _render(
        tool,
        {"args_sha256": success["args_sha256"]},
        {"status": success["status"], "ok": True},
        f"Alat {tool} je uspjesno izvrsen (status=ok).",
        f"Planiranje izvrsavanja alata {tool}.",
    )
    rejected = _render(
        tool,
        {"args_sha256": failure["args_sha256"]},
        {"status": failure["status"], "ok": False},
        f"Alat {tool} je uspjesno izvrsen (status=ok).",
        f"Planiranje izvrsavanja alata {tool}.",
    )
    return {
        "prompt": f"Izvrsi operaciju koristeci alat: {tool}. Verifikuj ispravan ishod.",
        "chosen": chosen,
        "rejected": rejected,
        "synthetic": False,
        "metadata": {
            "tool": tool,
            "chosen_tool": tool,
            "rejected_tool": tool,
            "category": "status_flip",
            "difficulty": 0.25,
            "args_similarity": None,
            "args_similarity_basis": "unknown_receipts_store_only_sha256",
            "identical_tool_calls": False,
            "bucket": "trivial",
            "source": "receipts",
            "synthetic": False,
            "chosen_seq": success["seq"],
            "rejected_seq": failure["seq"],
            "chosen_status": success["status"],
            "rejected_status": failure["status"],
            "note": "stvarni par iz receipts baze; ok vs error (laka kontrola)",
        },
    }


def _synthetic_pair(
    *,
    category: str,
    tool: str,
    prompt: str,
    args_chosen: dict,
    response_chosen: dict,
    final_chosen: str,
    args_rejected: dict,
    response_rejected: dict,
    final_rejected: str,
    anchors: dict | None = None,
    identical_tool_calls: bool = False,
    threshold: float = NEAR_MISS_THRESHOLD,
    note: str = "",
) -> dict:
    anchors = anchors or {}
    similarity = 1.0 if identical_tool_calls else _args_similarity(args_chosen, args_rejected)
    difficulty = _difficulty(category, similarity)
    bucket = "near_miss" if (difficulty >= threshold and similarity >= 0.5) else "trivial"
    chosen = _render(
        tool,
        args_chosen,
        response_chosen,
        final_chosen,
        f"Biram alat {tool}; provjeravam ishod prije tvrdnje.",
    )
    rejected = _render(
        tool,
        args_rejected,
        response_rejected,
        final_rejected,
        f"Biram alat {tool}; provjeravam ishod prije tvrdnje.",
    )
    return {
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
        "synthetic": True,
        "metadata": {
            "tool": tool,
            "chosen_tool": tool,
            "rejected_tool": tool,
            "category": category,
            "difficulty": difficulty,
            "args_similarity": similarity,
            "args_similarity_basis": "synthetic_arguments",
            "identical_tool_calls": bool(identical_tool_calls),
            "bucket": bucket,
            "source": "synthetic",
            "synthetic": True,
            "anchor_chosen_seq": anchors.get("chosen_seq"),
            "anchor_rejected_seq": anchors.get("rejected_seq"),
            "note": note,
        },
    }


def _anchors(by_tool: dict, tools: tuple[str, ...], idx: int) -> dict:
    successes, failures = [], []
    for tool in tools:
        for receipt in by_tool.get(tool, []):
            (successes if _is_success(receipt) else failures).append(receipt)
    return {
        "chosen_seq": successes[idx % len(successes)]["seq"] if successes else None,
        "rejected_seq": failures[idx % len(failures)]["seq"] if failures else None,
    }


# ---------------------------------------------------------------------------
# Synthetic categories
# ---------------------------------------------------------------------------
def _gen_sql_wrong_table(by_tool: dict, limit: int, threshold: float) -> list[dict]:
    variants = [
        ("001", "kupci", 1),
        ("042", "kupac", 1),
        ("777", "kupci2026", 0),
        ("1114", "kupac", 1),
    ]
    pairs = []
    for idx in range(limit):
        sifra, bad_table, n = variants[idx % len(variants)]
        good_query = f"SELECT COUNT(*) AS n FROM customers WHERE sifra = '{sifra}'"
        bad_query = f"SELECT COUNT(*) AS n FROM {bad_table} WHERE sifra = '{sifra}'"
        pairs.append(
            _synthetic_pair(
                category="sql_wrong_table",
                tool="sql",
                prompt=(
                    f"U bazi demo provjeri koliko kupaca ima sifru {sifra}. "
                    "Koristi tabelu customers i vrati tacan broj."
                ),
                args_chosen={"db": "demo", "query": good_query},
                response_chosen={"ok": True, "status": "ok", "rows": [{"n": n}]},
                final_chosen=f"Kupaca sa sifrom {sifra}: {n}.",
                args_rejected={"db": "demo", "query": bad_query},
                response_rejected={
                    "ok": False,
                    "status": "error",
                    "error": f"no such table: {bad_table}",
                },
                final_rejected=f"Potvrdjeno: kupac {sifra} postoji ({n}).",
                anchors=_anchors(by_tool, ("sql",), idx),
                threshold=threshold,
                note="ista SQL forma, pogresna tabela; error je prekriven lazni uspjeh",
            )
        )
    return pairs


def _gen_sql_wrong_column(by_tool: dict, limit: int, threshold: float) -> list[dict]:
    variants = [
        ("001", "kod", 1),
        ("042", "sifra_kupca", 1),
        ("777", "id_kupca", 0),
        ("1114", "kupac_sifra", 1),
    ]
    pairs = []
    for idx in range(limit):
        sifra, bad_column, n = variants[idx % len(variants)]
        good_query = f"SELECT COUNT(*) AS n FROM customers WHERE sifra = '{sifra}'"
        bad_query = f"SELECT COUNT(*) AS n FROM customers WHERE {bad_column} = '{sifra}'"
        pairs.append(
            _synthetic_pair(
                category="sql_wrong_column",
                tool="sql",
                prompt=(
                    f"U bazi demo provjeri postoji li kupac sa sifrom {sifra}. "
                    "Tabela je customers, kolona sifra."
                ),
                args_chosen={"db": "demo", "query": good_query},
                response_chosen={"ok": True, "status": "ok", "rows": [{"n": n}]},
                final_chosen=f"Kupac {sifra}: {'postoji' if n else 'ne postoji'}.",
                args_rejected={"db": "demo", "query": bad_query},
                response_rejected={
                    "ok": False,
                    "status": "error",
                    "error": f"no such column: {bad_column}",
                },
                final_rejected=f"Kupac {sifra}: {'postoji' if n else 'ne postoji'}.",
                anchors=_anchors(by_tool, ("sql",), idx),
                threshold=threshold,
                note="ista tabela, pogresna kolona; sintaksno validno, semanticki pogresno",
            )
        )
    return pairs


def _gen_path_lookalike(by_tool: dict, limit: int, threshold: float) -> list[dict]:
    variants = [
        (
            "project/decision_l0.py",
            "project/calibration_evaluator.py",
            True,
            "def decide_request",
        ),
        (
            "project/tests/test_decision_l0.py",
            "project/tests/test_decison_l0.py",
            False,
            "def test_gate",
        ),
        (
            "project/decision_l0.py",
            "project/decision_context.py",
            True,
            "def decide_request",
        ),
        (
            "project/dpo_near_miss.py",
            "project/dpo_near_mis.py",
            False,
            "def load_receipts",
        ),
    ]
    pairs = []
    for idx in range(limit):
        good_path, bad_path, bad_exists, symbol = variants[idx % len(variants)]
        if bad_exists:
            bad_response = {
                "ok": True,
                "status": "ok",
                "path": bad_path,
                "contains": None,
            }
        else:
            bad_response = {
                "ok": False,
                "status": "error",
                "error": f"file not found: {bad_path}",
            }
        pairs.append(
            _synthetic_pair(
                category="path_lookalike",
                tool="fs_read",
                prompt=(
                    f"Procitaj fajl {good_path} i odgovori sadrzi li `{symbol}`. "
                    "Ne citaj druge fajlove."
                ),
                args_chosen={"path": good_path},
                response_chosen={
                    "ok": True,
                    "status": "ok",
                    "path": good_path,
                    "contains": symbol,
                },
                final_chosen=f"Da, {good_path} sadrzi `{symbol}`.",
                args_rejected={"path": bad_path},
                response_rejected=bad_response,
                final_rejected=f"Da, {good_path} sadrzi `{symbol}`.",
                anchors=_anchors(by_tool, ("fs_read", "fs_write", "apply_patch"), idx),
                threshold=threshold,
                note="skoro isti put (typo ili sibling fajl); tvrdnja ignorise stvarni ishod",
            )
        )
    return pairs


def _gen_numeric_hallucination(by_tool: dict, limit: int, threshold: float) -> list[dict]:
    variants = [
        ("sql", 1114, 1141, True),
        ("sql", 1114, 1041, True),
        ("sql", 1114, 1102, False),
        ("brain_search", 1114, 1124, True),
    ]
    pairs = []
    for idx in range(limit):
        tool, true_n, claimed_n, identical = variants[idx % len(variants)]
        prompt = "Koliko ukupno kupaca ima u tabeli customers? Vrati tacan broj iz baze."
        if tool == "sql":
            if identical:
                args_chosen = {
                    "db": "demo",
                    "query": "SELECT COUNT(*) AS n FROM customers",
                }
                args_rejected = dict(args_chosen)
            else:
                args_chosen = {
                    "db": "demo",
                    "query": "SELECT COUNT(*) AS n FROM customers",
                }
                args_rejected = {
                    "db": "demo",
                    "query": "SELECT COUNT(sifra) AS n FROM customers",
                }
            response_chosen = {"ok": True, "status": "ok", "rows": [{"n": true_n}]}
            response_rejected = (
                dict(response_chosen)
                if identical
                else {"ok": True, "status": "ok", "rows": [{"n": claimed_n}]}
            )
        else:
            args_chosen = {"query": "broj kupaca u bazi demo"}
            args_rejected = dict(args_chosen)
            response_chosen = {
                "ok": True,
                "status": "ok",
                "fact": "U bazi demo ima 1114 kupaca.",
            }
            response_rejected = dict(response_chosen)
        pairs.append(
            _synthetic_pair(
                category="numeric_hallucination",
                tool=tool,
                prompt=prompt,
                args_chosen=args_chosen,
                response_chosen=response_chosen,
                final_chosen=f"Ukupno {true_n} kupaca.",
                args_rejected=args_rejected,
                response_rejected=response_rejected,
                final_rejected=f"Ukupno {claimed_n} kupaca.",
                anchors=_anchors(by_tool, ("sql", "brain_search"), idx),
                identical_tool_calls=identical,
                threshold=threshold,
                note=(
                    "identican tool-call/odgovor, razlicit konacni broj"
                    if identical
                    else "COUNT(*) vs COUNT(kolona); oba ok, samo jedan je tacan metric"
                ),
            )
        )
    return pairs


def _gen_false_success_ack(by_tool: dict, limit: int, threshold: float) -> list[dict]:
    variants = [
        {
            "tool": "run",
            "prompt": "Popravi gresku i pokreni testove; javi stvarni rezultat.",
            "args": {
                "cmd": "pytest -q tests/test_eval_adapter_ece.py",
                "timeout": 120,
            },
            "response": {
                "ok": False,
                "status": "error",
                "rc": 1,
                "stderr": "1 failed, 0 passed",
            },
            "honest": "Nije popravljeno: rc=1, 1 test pada. Dokaz: stderr.",
            "lie": "Popravljeno; svi testovi prolaze.",
        },
        {
            "tool": "apply_patch",
            "prompt": "Primijeni patch na fajl i potvrdi da je izmjena na disku.",
            "args": {
                "path": "project/eval_adapter_ece.py",
                "patch": "@@ def evaluate @@ ...",
            },
            "response": {
                "ok": False,
                "status": "error",
                "error": "patch context not found",
            },
            "honest": "Patch nije primijenjen (context not found); fajl je nepromijenjen.",
            "lie": "Patch je primijenjen i fajl je izmijenjen.",
        },
        {
            "tool": "hc",
            "prompt": "Pokreni komandu na serveru i reci da li je izvrsena.",
            "args": {"node": "server", "cmd": "dir C:\\GAMA"},
            "response": {
                "ok": False,
                "status": "error",
                "error": "timeout after 30s",
            },
            "honest": "Komanda nije izvrsena: timeout poslije 30s. Nema dokaza o uspjehu.",
            "lie": "Komanda je uspjesno izvrsena na serveru.",
        },
        {
            "tool": "fs_write",
            "prompt": "Sacuvaj konfiguraciju i potvrdi upis.",
            "args": {"path": "/proc/gama_x.conf", "content": "x=1\n"},
            "response": {
                "ok": False,
                "status": "error",
                "error": "permission denied",
            },
            "honest": "Upis nije uspio: permission denied. Fajl nije sacuvan.",
            "lie": "Fajl je sacuvan.",
        },
    ]
    pairs = []
    for idx in range(limit):
        variant = variants[idx % len(variants)]
        pairs.append(
            _synthetic_pair(
                category="false_success_ack",
                tool=variant["tool"],
                prompt=variant["prompt"],
                args_chosen=variant["args"],
                response_chosen=variant["response"],
                final_chosen=variant["honest"],
                args_rejected=variant["args"],
                response_rejected=variant["response"],
                final_rejected=variant["lie"],
                anchors=_anchors(
                    by_tool, ("run", "apply_patch", "hc", "fs_write"), idx
                ),
                identical_tool_calls=True,
                threshold=threshold,
                note="identican tool-call i error; razlika je samo u priznanju neuspjeha",
            )
        )
    return pairs


_GENERATORS = (
    _gen_sql_wrong_table,
    _gen_sql_wrong_column,
    _gen_path_lookalike,
    _gen_numeric_hallucination,
    _gen_false_success_ack,
)


# ---------------------------------------------------------------------------
# Real receipt pairs (trivial control)
# ---------------------------------------------------------------------------
def _build_receipt_pairs(
    receipts: list[dict], max_total: int = 300, max_per_tool: int = 40
) -> list[dict]:
    successes = defaultdict(list)
    failures = defaultdict(list)
    for receipt in receipts:
        if _is_success(receipt):
            successes[receipt["tool"]].append(receipt)
        else:
            failures[receipt["tool"]].append(receipt)

    pairs = []
    for tool in sorted(set(successes) & set(failures)):
        succ = sorted(successes[tool], key=lambda r: r["seq"])
        fail = sorted(failures[tool], key=lambda r: r["seq"])
        used_fail: set[int] = set()
        made = 0
        for success in succ:
            if made >= max_per_tool or len(pairs) >= max_total:
                break
            best_idx = None
            best_dist = None
            for idx, failure in enumerate(fail):
                if idx in used_fail:
                    continue
                dist = abs(failure["seq"] - success["seq"])
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_idx = idx
            if best_idx is None:
                break
            used_fail.add(best_idx)
            pairs.append(_receipt_pair(success, fail[best_idx]))
            made += 1
        if len(pairs) >= max_total:
            break
    return pairs[:max_total]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_near_miss_dataset(
    db_path: str = DEFAULT_DB,
    output_path: str = DEFAULT_OUTPUT,
    report_path: str | None = DEFAULT_REPORT,
    limit: int | None = None,
    max_real_pairs: int = 300,
    max_synthetic_per_category: int = 60,
    threshold: float = NEAR_MISS_THRESHOLD,
    seed: int = 7,
    shuffle: bool = False,
) -> dict:
    """Generisi near-miss DPO dataset i vrati summary."""
    receipts = load_receipts(db_path, limit=limit)
    by_tool = defaultdict(list)
    for receipt in receipts:
        by_tool[receipt["tool"]].append(receipt)

    real_pairs = _build_receipt_pairs(receipts, max_total=max_real_pairs)
    pairs = list(real_pairs)
    for generator in _GENERATORS:
        pairs.extend(generator(by_tool, max_synthetic_per_category, threshold))

    if shuffle:
        random.Random(seed).shuffle(pairs)

    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")

    summary = summarize_pairs(pairs, threshold=threshold)
    report = {
        "config": {
            "db": db_path,
            "output": output_path,
            "limit": limit,
            "max_real_pairs": max_real_pairs,
            "max_synthetic_per_category": max_synthetic_per_category,
            "threshold": threshold,
            "seed": seed,
            "shuffle": shuffle,
        },
        "summary": summary,
        "generated_at": time.time(),
    }
    if report_path:
        report_dir = os.path.dirname(os.path.abspath(report_path))
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
    return summary


def summarize_pairs(pairs: list[dict], threshold: float = NEAR_MISS_THRESHOLD) -> dict:
    by_category = Counter()
    by_tool = Counter()
    by_bucket = Counter()
    by_category_bucket = Counter()
    difficulties = []
    similarities = []

    for pair in pairs:
        meta = pair.get("metadata") or {}
        category = meta.get("category", "unknown")
        bucket = meta.get("bucket", "unknown")
        by_category[category] += 1
        by_tool[meta.get("tool", "unknown")] += 1
        by_bucket[bucket] += 1
        by_category_bucket[f"{category}:{bucket}"] += 1
        difficulties.append(float(meta.get("difficulty") or 0.0))
        if meta.get("args_similarity") is not None:
            similarities.append(float(meta["args_similarity"]))

    total = len(pairs)
    return {
        "total": total,
        "near_miss": by_bucket.get("near_miss", 0),
        "trivial": by_bucket.get("trivial", 0),
        "synthetic": sum(1 for p in pairs if p.get("synthetic")),
        "real": sum(1 for p in pairs if not p.get("synthetic")),
        "threshold": threshold,
        "by_category": dict(sorted(by_category.items())),
        "by_tool": dict(sorted(by_tool.items())),
        "by_bucket": dict(sorted(by_bucket.items())),
        "by_category_bucket": dict(sorted(by_category_bucket.items())),
        "mean_difficulty": round(sum(difficulties) / total, 4) if total else 0.0,
        "min_difficulty": round(min(difficulties), 4) if difficulties else 0.0,
        "max_difficulty": round(max(difficulties), 4) if difficulties else 0.0,
        "mean_args_similarity": (
            round(sum(similarities) / len(similarities), 4) if similarities else None
        ),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generisi near-miss DPO parove iz GTL receipts baze."
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="receipts sqlite baza")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="izlazni JSONL")
    parser.add_argument(
        "--report", default=DEFAULT_REPORT, help="izlazni JSON summary ('' za off)"
    )
    parser.add_argument("--limit", type=int, default=None, help="limit receipts redova")
    parser.add_argument("--max-real-pairs", type=int, default=300)
    parser.add_argument("--max-synthetic-per-category", type=int, default=60)
    parser.add_argument("--threshold", type=float, default=NEAR_MISS_THRESHOLD)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--json", action="store_true", help="samo JSON summary")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        summary = generate_near_miss_dataset(
            db_path=args.db,
            output_path=args.output,
            report_path=(args.report or None),
            limit=args.limit,
            max_real_pairs=args.max_real_pairs,
            max_synthetic_per_category=args.max_synthetic_per_category,
            threshold=args.threshold,
            seed=args.seed,
            shuffle=args.shuffle,
        )
    except (FileNotFoundError, sqlite3.Error) as exc:
        print(f"GRESKA: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(
            f"OK: {summary['total']} parova "
            f"(near_miss={summary['near_miss']}, trivial={summary['trivial']}, "
            f"synthetic={summary['synthetic']}, real={summary['real']})"
        )
        print(f"Output: {args.output}")
        if args.report:
            print(f"Report: {args.report}")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
