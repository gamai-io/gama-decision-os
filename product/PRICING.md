# GAMA Decision OS — Pricing Strategy (v1.0, 2026-11-13)

> Status: internal pricing decision. Currency: EUR. Fixed BAM rate: **€1 = 1.95583 BAM**.
> All prices exclude VAT (BiH 17%). Prices are per legal entity, not per user.

---

## 1. Positioning

**We sell risk reduction and auditability per production node — not seats.**

Why per node:
- The buyer's cost is infrastructure and blast radius, not headcount. A node is the unit that runs agent actions and produces evidence.
- Per-seat pricing punishes exactly the teams that should adopt agents widely.
- Per-node maps cleanly to the licence token and to offline validation (air-gapped).

**Anchor:** one production incident caused by an unverified agent action (wrong price sent, wrong stock movement, wrong invoice) typically costs **€5,000–€50,000** in correction and trust. One Pro node at €299/month is **€3,588/year** — less than a single incident and less than 2% of a junior ops engineer's loaded cost in the EU.

**Compliance anchor:** external EU AI Act readiness consulting runs €15,000–€60,000. Our Enterprise pack does not replace a lawyer, but it removes 60–80% of the evidence-gathering work.

---

## 2. Tiers

### Community — €0, Apache-2.0
**Target:** individual developers, researchers, students, first prototypes, open-source integrations.

Included:
- L0 risk engine (deterministic precheck + 4 tiers), TSR adapters (runc, gVisor, Firecracker), Evidence Gate (SHA-256 hash chain; Ed25519 signing planned, not in this build), CLI, REST, Python SDK.
- 1 node, unlimited local runs, no telemetry.
- Community support via GitHub Discussions.

Deliberately excluded: SSO/SCIM, multi-tenant, signed audit export for regulators, ERP connectors, SLA, production build with offline licence validation.

**Why free:** distribution and trust. Every integration, blog post and benchmark run lowers CAC for Pro. The core must be genuinely useful, or the open-core story collapses.

### Pro — €299/node/month (annual) or €349/node/month (monthly)
**Minimum:** 2 nodes. **Annual:** billed upfront, 2 months free (effective €299 vs €349).
**Target:** 5–200 person product/ops teams running agents against real systems; agencies deploying for clients.

Included:
- Everything in Community + production build.
- Unlimited agents, sessions and evidence receipts.
- Evidence export: JSON/CSV with signature verification + retention policies.
- 2 connectors included (PostgreSQL/MSSQL, REST/webhook); extra connector €49/node/month.
- E-mail support, 2 business days; upgrade assistance.
- Free upgrades within a major version; security patches for 12 months after a major release.

**Why €299:** below the €500/month procurement threshold for most SMBs (no board approval), high enough to fund support. At 10 nodes it is €35,880/year — comparable to a mid-level engineer, but sold as infrastructure.

### Enterprise — from €24,000/year (up to 10 nodes) + €7,500 onboarding
**Target:** banks, insurers, ERP-heavy distributors, public sector, any organisation with a named AI Act obligation or an internal audit function.

Included:
- Everything in Pro, unlimited nodes beyond 10 at €1,800/node/year.
- Air-gapped install, offline signed licence, hardened container images, SBOM.
- EU AI Act evidence pack: Art. 9–15 mapping, risk register template, technical documentation skeleton, incident log export.
- SSO (OIDC/SAML), SCIM, RBAC, multi-tenant isolation, audit log streaming (SIEM).
- ERP connectors: SAP (OData/BAPI), Odoo, Microsoft Dynamics, custom (scoped).
- SLA 99.9%, 24/7 escalation, named engineer, quarterly review, annual architecture audit.
- DPA + subprocessor list + security questionnaire support.

**Why €24k:** it must be a budget line, not an experiment. It sits under the €25k capex threshold in many EU mid-market firms and above the "manager can approve" line — forcing proper ownership. Onboarding is separate and mandatory: an air-gapped ERP integration without onboarding is a support liability.

---

## 3. Add-ons (fixed, published)

| Add-on | Price | Notes |
|---|---|---|
| Extra ERP connector (Pro) | €49/node/month | Enterprise custom connectors quoted |
| Custom connector build | €4,500 one-time | 5 days, includes tests + docs |
| EU AI Act readiness workshop | €2,500 | 1 day, remote, up to 8 people |
| Evidence pack review (annual) | €3,500 | Auditor-facing export review |
| Premium support | +20% of ACV | 4h response, 12/5 |
| On-site training | €1,800/day + travel | Sarajevo/Balkan preferred |
| Historical evidence migration | €2,900 | Up to 1M receipts |

---

## 4. Discount policy (published, no hidden deals)

- **Annual prepay:** 2 months free (already in the annual price).
- **Startups** (< 3 years, < €2M ARR): 50% off Pro for 12 months, then list price.
- **Academia / non-profit:** 50% off Pro, forever, 1–5 nodes.
- **Open-source maintainers:** free Pro for 2 nodes with a public integration.
- **Volume (Pro):** 11–25 nodes −10%, 26–50 nodes −18%, 51+ custom.
- **Multi-year:** 3-year Enterprise −10%, paid annually.
- **No discount on onboarding** — it protects delivery quality.
- Discounts do not stack; the largest applies.

---

## 5. Packaging and licence enforcement

- **Licence unit:** node = one machine/VM running the Decision OS service in production. Dev/test/staging are free on Pro and Enterprise.
- **Token:** signed offline licence (`GAMA-XXXX-…`) bound to `licence_id`, tier, node limit, expiry, feature flags. Verified locally with our public key; no phone-home required.
- **Grace:** 30 days after expiry, read-only mode (decisions still logged, mutating actions require approval). Never delete customer data.
- **No obfuscation, no kill switch.** Enforcement is contractual + technical (feature flags), not hostile.
- **Community → Pro:** in-place upgrade, same data directory, same DB schema.

---

## 6. Unit economics (planning assumptions, to be validated)

| Item | Assumption |
|---|---|
| Pro gross margin | 85–90% (self-hosted, support is the cost) |
| Enterprise gross margin | 65–75% (onboarding + named engineer) |
| Target CAC (Pro, inbound) | €600–€1,200 |
| Target CAC (Enterprise, outbound) | €6,000–€9,000 |
| Payback (Pro) | < 4 months |
| Payback (Enterprise) | < 7 months |
| Churn target | < 1.5%/month Pro, < 5%/year Enterprise |

These are targets, not measured results. Revise after the first 20 paying customers.

---

## 7. What we do NOT charge for

- Reading/exporting your own evidence after cancellation.
- Security patches for supported versions.
- Community core features.
- per-seat access to the dashboard.
- API calls, receipts or decisions (no metered surprises). This is a differentiator against usage-priced observability vendors.

---

## 8. Rollout sequencing

1. **Weeks 1–2:** publish Community + Pro list prices, no checkout yet (invoice + manual licence).
2. **Weeks 3–4:** Stripe Checkout for Pro monthly/annual; licence issued automatically by webhook.
3. **Month 2:** Enterprise price sheet + security questionnaire + DPA template.
4. **Month 3:** review conversion by tier; only then consider usage-based enterprise add-ons.

**Guardrail:** do not discount before 20 conversations. Early discounts destroy the anchor.
