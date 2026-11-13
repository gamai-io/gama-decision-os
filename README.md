# GAMA Decision OS

**An open-core control plane for autonomous agents: decide before acting, constrain execution, and require evidence that the action actually happened.**

GAMA Decision OS sits between your agent and its tools. It answers three questions that most agent stacks leave to the model:

1. **Should this action run at all?** Risk, intent/tier, confidence and the evidence that will be required.
2. **How should it run?** Allow, sandbox, ask a human, or deny.
3. **Did it actually work?** A verifiable evidence receipt instead of the model's own `ok: true`.

The core is licensed **Apache-2.0**. Enterprise capabilities are licensed separately; see [Open-core](#open-core).

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

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
