# GAMA Decision OS

**Control and proof for every AI-agent action — before it executes.**

---

## The problem

AI agents now send quotes, change prices, post invoices and touch inventory in
production systems. Most tooling watches **after** the fact — it logs a trace and
hopes. When the agent gets it wrong, the cost is not tokens: it is a wrong quote,
a wrong stock movement and a customer who no longer trusts the process.

On top of that, the EU AI Act expects demonstrable records and human oversight
(Art. 12, 14, 15, 19, 26, 72) — and "we have logs" rarely survives an audit.

---

## The solution — 3 Gates on every action

| Gate | What it does | Evidence (measured) |
|---|---|---|
| **Gate 1 — L0 decision** | Classifies every action before execution: READ / DRAFT / SEND / IRREVERSIBLE → allow / ask / deny | **2.31 ms p50** |
| **Gate 2 — Sandbox ladder** | Isolated execution matched to risk | runc **110 ns** · gVisor **751 ns** · Firecracker **54 ns** · snapshot restore **2.28 ms** |
| **Gate 3 — Proof** | Ed25519-signed receipts + SHA-256 hash chain | Every receipt is publicly verifiable |

An agent cannot simply "just do" a destructive action. It is classified,
isolated when needed, and leaves a cryptographic record of who decided what and
why.

---

## Proof it works

- **396 tools** in the system; **schema compression 90.6%** (213,781 B → 20,076 B
  per query) — the full toolset fits in context without truncation.
- **Calibration:** ECE **0.297 → 0.035** (T = 0.2), ranking **1.000** on a
  held-out set of **1,200** samples. *Limitation: the dataset is degenerate and
  the fit sits on the boundary — stated on purpose.*
- **RLDF DPO:** train_loss **0.10052**, 600 near-miss pairs (300 hard + 300
  controls).
- **6-node fleet**, harness **1.2.2**, **294 tools** in the OpenCode/harness
  schema.
- **Benchmark of 20 competitors:** no public solution combines pre-action L0 +
  sandbox ladder + Ed25519 receipts.

---

## Pricing

| Tier | Price | Who it is for |
|---|---|---|
| **Community** | **€0** (Apache-2.0) | first prototype, 1 node, no telemetry |
| **Pro** | **€299**/node/month annual (€349 monthly), min. 2 nodes | teams running agents against live systems |
| **Enterprise** | from **€24,000**/yr (up to 10 nodes) + **€7,500** onboarding | banks, insurers, ERP distributors, public sector |

Priced per node, not per user — risk and evidence are measured per machine that
executes actions. No usage metering per call, no surprise invoices.

---

## Call to action

**Book a 10-minute demo** and watch a destructive command get blocked while a
benign one passes — on a live system, with a receipt you verify yourself.

→ https://decision-os.gamai.io · Public verifier: https://decision-os.gamai.io/verify.html

---

<sub>Every number comes from internal tests and is reproducible; where something
is not measured, it says "target" or "not measured". No invented customers or
references. Limitations (calibration on a degenerate set) are published alongside
the result.</sub>
