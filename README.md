# GAMA Decision OS

**An open-core control plane for autonomous agents: decide before acting, constrain execution, and require evidence that the action actually happened.**

GAMA Decision OS sits between your agent and its tools. It answers three questions that most agent stacks leave to the model:

1. **Should this action run at all?** Risk, intent/tier, confidence and the evidence that will be required.
2. **How should it run?** Allow, sandbox, ask a human, or deny.
3. **Did it actually work?** A verifiable evidence receipt instead of the model's own `ok: true`.

The core is licensed **Apache-2.0**. Enterprise capabilities are licensed separately; see [Open-core](#open-core).

- Website: https://gamai.io
- Contact: info@gamai.io

---

## Three gates

| Gate | Entry point | What it does |
| --- | --- | --- |
| **Gate 1 — pre-action** | `decide_request(text)` | Deterministic precheck plus calibrated classification into `READ`, `DRAFT`, `SEND`, `IRREVERSIBLE`. Produces a decision envelope with `verdict`, `route`, `confidence`, `expected_evidence_spec`, `decision_hash`. |
| **Gate 2 — in-action** | `decide_tool(tool, args, ctx)` | Tool-level gate: `allow`, `sandbox`, `ask`, `deny`. Blocks mutations in `READ`, blocks unrequested destructive shell and mail calls. |
| **Gate 3 — post-action** | `verify_evidence(envelope, tool, result)` | Checks the expected evidence contract and emits a hashed `EvidenceReceipt`. Verifies deletes on disk, SQL rows, external sends, code changes. |

```
agent ──▶ decide_request ──▶ decide_tool ──▶ tool ──▶ verify_evidence ──▶ done / rollback
```

## Install

The core has **no third-party runtime dependencies** (Python standard library only).

```bash
python3 -m pip install -e .
python3 -m pytest tests/ -q
```

Requirements: Python 3.9+.

## Quick start

```python
from gama_decision import decide_request, decide_tool, verify_evidence

envelope = decide_request("delete /tmp/report.txt")
print(envelope["tier"], envelope["verdict"], envelope["expected_evidence_spec"])

decision = decide_tool("delete_file", {"path": "/tmp/report.txt"}, envelope)
receipt = verify_evidence(decision, "delete_file", {"ok": True, "verified": True, "exists": False})
print(receipt["verified"], receipt["receipt_hash"])
```

See [`examples/`](examples/) for a Python client and curl examples.

## What is in the core

- `gama_decision/decision_l0.py` — deterministic rules, tiering, calibrated probabilities, session slot filling, speculative override hook, tool gate, evidence gate.
- `gama_decision/decision_context.py` — dependency-free repository/context compression (optional `gama_repomap3` backend when installed).
- `gama_decision/calibration_evaluator.py` — ECE and Brier score with a pure-Python fallback.
- `gama_decision/eval_adapter_ece.py` — adapter evaluation and temperature-scaling calibration (optional `scipy`/`torch` backends).
- `gama_decision/dpo_near_miss.py`, `dpo_dataset_generator.py` — near-miss DPO dataset generation from receipt logs.
- `tests/` — decision, speculative, context and calibration tests.

## Open-core

| | Core (Apache-2.0) | Enterprise |
| --- | --- | --- |
| Three-gate runtime | Yes | Yes |
| Evidence receipts | Yes | Yes |
| Calibration tooling | Yes | Yes |
| Compliance reporting / retention | — | Yes |
| SSO / SCIM, multi-tenancy | — | Yes |
| ERP / database connectors | — | Yes |
| Signed releases, SLA, support | — | Yes |

The enterprise license template is in [`LICENSE-ENTERPRISE.md`](LICENSE-ENTERPRISE.md). Core code is governed only by Apache-2.0.

## Security

- No secrets are required to run the core.
- All network features are opt-in via environment variables.
- Report vulnerabilities per [`SECURITY.md`](SECURITY.md).

## Documentation

- [`docs/GAMA_DECISION_OS_MANIFESTO.md`](docs/GAMA_DECISION_OS_MANIFESTO.md) — design principles.
- [`docs/SITE_ARCHITECTURE.md`](docs/SITE_ARCHITECTURE.md) — public site and information architecture.
- [`docs/BENCHMARK.md`](docs/BENCHMARK.md) — reproducible benchmark notes and caveats.
- [`docs/BENCHMARK_LUMI_10K.md`](docs/BENCHMARK_LUMI_10K.md) — LUMI-G 10k async agents: 10.000/10.000, 0 grešaka, 0 retry (4× MI250X; 2026-11-15). Provjera: `python3 benchmarks/lumi_10k/verify_stress.py` (čita `results/stress_v5_*.json`).
- [`docs/BENCHMARK_COMPETITIVE.md`](docs/BENCHMARK_COMPETITIVE.md) — competitive benchmark vs agent control-plane / guardrails / observability market (2026-11-13).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

## Brojevi (jedan izvor istine)

Svi brojevi u dokumentaciji i na sajtu dolaze iz `config/FACTS.json` u internom repou:

| Stavka | Vrijednost | Kako je izmjereno |
|---|---|---|
| Alati (katalog) | **398** | `len(all_tools())` |
| Alati (runtime prompt) | **296** | `len(TOOLS)` |
| Vještine (biblioteka) | **5.024** | direktoriji u `~/.agents/skills` |
| Persone | **409** | `gama_persona_ondemand.list_personas()` |
| Baseline šema | **53.226 tokena** | sve šeme prije kompresije |
| Prosječno šema (live) | **2.312 tokena** | `_token_ledger.db`, 24 h |
| Ušteda (live, 24 h) | **75,5 %** (n=2.021) | `python3 benchmarks/ledger_stats.py` (token_ledger, 2026-11-23) |
| Ušteda (7 dana) | **70,9 %** (n=11.012) | isto; projekcija do 93 % važi samo za veći udio ponavljanja |
| Short-circuit | **7,2 %** upita (24 h) · **3,0 %** (7 d) | isto. Ranije navedenih „28 %" **nije reproducirano** |
| L0 odluka | **0,0026 ms** p50 (READ) · 0,0017 (IRREVERSIBLE) · 0,0020 (SEND) | `python3 benchmarks/decision_latency.py --n 500`, 0 pogrešnih odluka na 1.500 poziva, 2026-11-23 |
| ECE (kalibracija, dry-run) | **0,407** (Brier 0,317, accuracy 0,643, n=42) | `python3 -m gama_decision.eval_adapter_ece --dry-run` (2026-11-23). Broj sa adapterom (0,2973 → 0,0347) traži GPU + adapter i **nije reproduciran ovdje** |

### Nije reproducirano u ovom repou
Sljedeće je mjereno interno, ali **artefakt nije objavljen** — tretirati kao nepotvrđeno dok se ne doda skripta:
`Tier model 40/40 (100%)` · `Tool paging 97,3 %` · `Code Mode −82,3 % tokena`

## Šta je novo (2026-11-15)

| Sloj | Rezultat | Kako je izmjereno |
|---|---|---|
| **Code Mode** (kod umjesto tool-callova) | **−82,3 %** tokena na 3 koraka (−70,6 % na 1, −89,2 % na 10) | bench, 5 realnih multi-step zadataka, 40 alata |
| **Deterministički obrasci** | **10 obrazaca = 27 %** stvarnog prometa, 0 tokena | regex na 318 stvarnih upita |
| **Canary ramp** | 5 % (shadow mjeri prije 25 % / 100 %); sve uštede aktivne na **6 čvorova** (16 flagova) | hash bucket po (sid, obrazac) |
| **Gated semantički keš** | 89 % hit, **USR = 0 %** (20/20 trapova blokirano) | bench 200 upita |
| **Exact cache na ingress** | −13,8 % ponovljenih poziva (prije se gubilo) | live, cache hit verifikovan |
| **Dedup tool rezultata** (TOOL_RESULT_DEDUP) | **0–37 %**, zavisno od ponavljanja: 0 % bez ponavljanja, 19,4 % na 10 %, 24,2 % na 25 %, 36,9 % na 40 % | bench sa realnim, unikatnim sadržajima (pošteno mjereno, bez lažnih dedupova) |
| **Token ledger po fazi** (TOKEN_PHASE_V1) | ingress / loop / chat odvojeno; prvi snimak 26 zapisa, 8.670 prompt, 1.502.633 ušteđenih tokena | token ledger (SQLite), izvještaj po fazi i modelu |
| **Audit popravke** (Claude + Codex) | decision cache scopiran po sid (sigurnosni), exact cache u stream putu, output budget u streamu, paging 4k / truncate 6k, Code Mode timeout guard | 79 testova prošlo; deploy na svih 6 čvorova |
| **Brain v2** | 100.222 zapisa, sync 60 s, opoziv + stale detekcija | `/api/stats` |
| **Javna verifikacija dokaza** | `https://gamai.io/api/verify?hash=...` → `chain_ok=true` | live curl |

**Sigurnosne ograde Code Modea:** samo READ/DRAFT tier, AST validacija (bez importa/atributa/lambde),
max 40 linija i 10 poziva, automatski fallback na normalan tok ako kod ne prođe.
