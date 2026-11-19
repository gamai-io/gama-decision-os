# GAMA Decision OS

**Autonomous Agent Control Plane.** Score risk before the agent acts, isolate execution, and return evidence that can be verified.

[![License: Apache-2.0](https://img.shields.io/badge/core-Apache--2.0-00d69a.svg)](LICENSE-CORE)
[![Status: v1.0](https://img.shields.io/badge/status-v1.0-38bdf8.svg)](#status)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab.svg)](#install)

> The core is open source (Apache-2.0). Enterprise adds compliance, SSO/SCIM, multi-tenancy, ERP connectors and SLA. See [open-core](#open-core).

---

## Why

LLM agents now execute actions: they call SQL, send e-mail, move stock, create invoices. Most agent stacks have no answer to three questions:

1. **Should this action run at all?** (risk, intent, expected evidence)
2. **Where exactly does it run?** (blast radius, isolation)
3. **How do we know it actually worked?** (proof, not the model's `ok:true`)

GAMA Decision OS is a middleware layer that answers all three. It does not replace your agent.

```
Before:   LLM ──▶ tool ──▶ "done" ──▶ trust me
After:    LLM ──▶ L0 ──▶ sandbox ──▶ evidence ──▶ done / rollback
```

---

## Three pillars

| Pillar | What it does | Measured |
|---|---|---|
| **Pre-Action Decision (L0)** | Deterministic precheck + calibrated classifier maps every action to `READ / DRAFT / SEND / IRREVERSIBLE`, with expected evidence and confidence. | **0.05 ms** READ allow, **0.92 ms** IRREVERSIBLE ask |
| **Sandboxed Execution (TSR)** | Risk selects isolation: `runc` (fast), `gVisor` (untrusted network), Firecracker microVM (transactions). | **2.28 ms** snapshot restore; **54 ns/op** Firecracker syscall |
| **Post-Action Evidence** | SHA-256 result hash in an append-only hash chain. No evidence, no "done". Automatic rollback. Keyed (Ed25519) signatures are a planned separate layer, not included in this build. | **10/10** SWE-lite with independent pytest, **0 false-success** |

---

## Benchmarks

Internal measurements, 13 Nov 2026. Reproduce with `make bench` (see [Benchmarks](#reproducing-benchmarks)).

| Metric | Result | Condition |
|---|---|---|
| L0 precheck | **0.05 ms** | READ allow, p50 |
| L0 IRREVERSIBLE routing | **0.92 ms** | ask + rationale |
| L0 full decision | **2.31 ms** | p50, n=500 |
| L0 deterministic core | **0.30 ms** | p50, n=2000, no network |
| Firecracker snapshot restore | **2.28 ms** | pre-warm + mmap restore |
| Firecracker syscall latency | **54 ns/op** | vs 92 ns bare metal |
| runc syscall latency | **110 ns/op** | standard container |
| gVisor syscall latency | **751 ns/op** | Sentry interception |
| Firecracker cold boot | **1,846 ms** | one-off before snapshot |
| Prompt token reduction | **−86.2%** | 544,470 → 75,113 tokens (405 → 34–66 schemas) |
| SWE-bench-lite (10 tasks) | **10/10** | independent `fail_to_pass` + `pass_to_pass`; `tests/` restored to pristine |
| Harness soak | **20/20 ok** | 30 min, 0 retry |
| Evidence calibration (ECE) | **0.0347** (target < 0.05) | T=0.2, held-out n=240, accuracy 1.0 — degenerate/limited, see note |

**Honest note on ECE:** ECE was measured at **0.0347** (T=0.2, held-out n=240) by `calibration_evaluator.py` (ECE + Brier + ASCII reliability diagram). The set is degenerate — empirical accuracy was 1.0 at n=240 — so this is a weak calibration signal, not a general guarantee. Target is < 0.05; cite 0.0347 only with this limitation and the dataset hash.

---

## Architecture

```
                          ┌──────────────────────────────────────────────────────────┐
   Agent / LLM            │                  GAMA Decision OS                        │
   (OpenCode, Claude,     │                                                          │
    LangGraph, custom)    │   ┌────────────┐        ┌────────────────────────────┐   │
          │               │   │  Gate L0   │        │  Evidence Gate             │   │
          │  tool call    │   │  risk tier │        │  sha256 hash chain         │   │
          ├──────────────▶│   │  evidence  │        │  hash chain + checkpoint   │   │
          │               │   │  conf/abs. │        └────────────┬───────────────┘   │
          │               │   └─────┬──────┘                     │                   │
          │               │         │                            │                   │
          │               │   READ/DRAFT          SEND/IRREV      │                   │
          │               │         │                 │          │                   │
          │               │         ▼                 ▼          │                   │
          │               │   ┌───────────┐   ┌──────────────┐   │                   │
          │               │   │ TSR Router│   │ Human approval│  │                   │
          │               │   └─┬───┬───┬─┘   └──────┬───────┘   │                   │
          │               │     │   │   │            │           │                   │
          │               │  runc gVisor FC-µVM       │           │                   │
          │               │     └───┴───┴────────────┴───────────┘                   │
          │               └──────────────────────────┬───────────────────────────────┘
          │                                          │
          ▼                                          ▼
   PASS → commit + hash-chained receipt     FAIL → rollback + alert + audit entry
```

Components:

- **L0 engine** — 12 deterministic rules (shell patterns, `dd of=/dev/`, fork bomb, base64|sh, quoted false positives), 4 tiers, temperature scaling, abstention, expected-evidence spec.
- **TSR adapters** — `runc`, `gVisor`, Firecracker; a router picks the cheapest isolation that matches risk.
- **Evidence Gate** — result hashing, `prev_hash → hash` chain, SQLite receipts, checkpoint/rollback hooks (keyed Ed25519 signing is not included in this build).
- **Integrations** — REST (`POST /decide`, `POST /verify`), Python SDK, CLI, agent middleware, MCP tool.

---

## Install

### From source (works today)

```bash
git clone https://github.com/gamai-io/gama-decision-os.git
cd decision-os
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[server]"
gama-decision --version
gama-decision serve --host 127.0.0.1 --port 8443
```

### Container

```bash
# image publishing is part of the v1.0 release checklist
docker run --rm -p 8443:8443 -v "$PWD/data:/data" ghcr.io/gamai-io/gama-decision-os:1.0.0
```

### PyPI

Package name reserved for release: `gama-decision-os`. Until the release is public, use the source install above.

### Requirements

- Python 3.10+
- Linux for sandbox backends (`runc`/`gVisor`/Firecracker); macOS/Windows run L0 + Evidence Gate only.
- Firecracker backend: KVM (`/dev/kvm`), 2 GB RAM per microVM, NVMe recommended for snapshots.

---

## Quickstart

```python
from gama_decision import DecisionOS

dos = DecisionOS()  # reads GAMA_* env vars

decision = dos.decide(
    tool="sql",
    args={"query": "UPDATE stock SET qty = qty - 1 WHERE sku = 'A-1042'"},
    context={"agent": "order-bot", "session": "s-77"},
)

print(decision.tier)          # IRREVERSIBLE
print(decision.confidence)    # 0.92
print(decision.expected_evidence)
# {"kind": "rowcount_and_snapshot", "verify": "..."}

if decision.allowed:
    with dos.sandbox(decision) as box:
        result = box.run("python sync_stock.py")
    receipt = dos.verify(result, decision)
    print(receipt.ok, receipt.sha256)
else:
    print(decision.route)  # "ask"
```

REST:

```bash
curl -s localhost:8443/decide -H 'content-type: application/json' -d '{
  "tool":"mail.send",
  "args":{"to":"buyer@example.com","subject":"Offer 2026-118"},
  "context":{"agent":"sales-bot"}
}'
# {"tier":"SEND","route":"ask","confidence":0.88,"allowed":false,...}
```

---

## Open-core

| Component | Community (Apache-2.0) | Pro | Enterprise |
|---|---|---|---|
| L0 risk engine | ✅ | ✅ | ✅ |
| TSR adapters (runc/gVisor/FC) | ✅ | ✅ | ✅ |
| Evidence Gate + hash chain | ✅ | ✅ | ✅ |
| CLI / REST / Python SDK | ✅ | ✅ | ✅ |
| Production build | — | ✅ | ✅ |
| Signed evidence export | — | ✅ | ✅ |
| SQL/REST connectors | 1 (community) | 2 included | all |
| SSO / SCIM / RBAC | — | — | ✅ |
| Multi-tenant | — | — | ✅ |
| EU AI Act evidence pack | — | — | ✅ |
| ERP connectors (SAP, Odoo, Microsoft Dynamics, custom) | — | add-on | ✅ |
| Air-gapped offline licence | — | — | ✅ |
| SLA 99.9% / 24/7 | — | — | ✅ |

**No open-core trap:** a single team can run the full decision → sandbox → evidence loop in production on the Community tier. Enterprise sells organisational controls, not the ability to work.

Pricing details: [PRICING.md](PRICING.md).

---

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `GAMA_HOST` | `127.0.0.1` | Bind address |
| `GAMA_PORT` | `8443` | HTTP port |
| `GAMA_DB` | `./data/decisions.db` | SQLite receipts/evidence |
| `GAMA_L0_MODE` | `deterministic` | `deterministic` or `hybrid` (LLM tie-break) |
| `GAMA_LLM_BASE_URL` | — | OpenAI-compatible endpoint for hybrid mode |
| `GAMA_LLM_MODEL` | — | Model id for hybrid mode |
| `GAMA_SANDBOX` | `runc` | Default backend |
| `GAMA_FIRECRACKER_KERNEL` | — | Path to vmlinux for FC backend |
| `GAMA_LICENSE_KEY` | — | Pro/Enterprise key (offline) |
| `GAMA_TELEMETRY` | `0` | Never on by default |

Secrets are read from the environment or `/etc/gama-decision/env`; never commit them.

---

## Security

- No privileged Docker daemon required for Firecracker. KVM access is the only elevated capability.
- Evidence records are SHA-256 hash-chained and verified offline; this build does not include keyed (Ed25519) signatures.
- The default L0 mode never sends prompts to a third party.
- Report vulnerabilities to **security@gamai.io** (PGP on request). Please do not open public issues for security bugs.
- This project is a control layer, not a compliance certificate. It produces evidence; your auditor and counsel decide sufficiency.

---

## Reproducing benchmarks

```bash
make bench-l0        # L0 latency + tier matrix
make bench-tsr       # syscall/boot/restore on Linux with KVM
make bench-swe       # SWE-bench-lite, independent pytest
make bench-tokens    # deferred-tools A/B, prompt token count
```

Hardware used for the published numbers: a 10 vCPU / 33 GB / GTX 1660S KVM host for the sandbox benchmarks, plus a separate host for soak and SWE-lite runs. Results vary with kernel, storage and CPU; report your hardware with any comparison.

---

## Status

v1.0 core is functional and used internally. Public release checklist: sanitise git history (secrets rotation), publish images, reserve PyPI name, complete ECE evaluation, external security review. Until that checklist is done, treat this repo as **release candidate**, not a GA product.

---

## Contributing

See `CONTRIBUTING.md`. DCO sign-off required. By contributing you agree your contribution is licensed under Apache-2.0.

## License

- Core: [Apache-2.0](LICENSE-CORE).
- Enterprise modules: [commercial licence](LICENSE-ENTERPRISE.md).
- "GAMA" and "GAMA Decision OS" are trademarks of GAMA. Apache-2.0 does not grant trademark rights.
