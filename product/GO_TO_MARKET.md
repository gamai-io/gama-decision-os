# GAMA Decision OS — Go-to-Market Plan (30 days)

> Starts on **D0** = the day the release blockers below are closed. No public launch before that.
> Owner: GAMA (founder-led sales). Budget cap for month 1: **≤ €500** (domain, e-mail, small ads). Everything else is time.

---

## 0. Release blockers (must be true before any public post)

| # | Blocker | Why | Done? |
|---|---|---|---|
| B1 | `git filter-repo` on the public repo + rotate every key ever committed | History may contain provider keys/tokens. One leak kills the launch. | ☐ |
| B2 | ECE evaluation finished **or** page/README clearly says "target, not measured" | Rule: never publish an unverified number. Copy already says target; keep it. | ☐ |
| B3 | External security pass on the licence validator and webhook | Payment + licence path is the highest-risk surface. | ☐ |
| B4 | Trademark check "GAMA Decision OS" in EU/BiH (at least a knockout search) | Avoid a rebrand after traction. | ☐ |
| B5 | Privacy page, DPA template, security.txt, vulnerability contact | Enterprise buyers check these before a call. | ☐ |
| B6 | Stripe live keys only in env; webhook signature verified; test-mode checkout passes | Never ship hardcoded secrets. | ☐ |
| B7 | One-command demo that works on a clean laptop (Docker) | The demo is the sales pitch. | ☐ |
| B8 | Pricing consistency across site, README, Stripe | Mismatched prices kill trust. | ☐ |

---

## 1. Assets and infrastructure (D0–D3)

### Domain and e-mail
- Primary: `decision-os.gamai.io` (subdomain, no new domain cost) — or `gama-decision.eu` if available (< €15/yr).
- DNS: Cloudflare (already in use), orange-cloud on, HSTS.
- Mailboxes/aliases: `prodaja@`, `security@`, `legal@`, `support@` → existing GAMA mail. Test SPF/DKIM/DMARC before outreach.

### Hosting
- Landing is a static file. Serve it from any static host (nginx, Cloudflare Pages, object storage). **No server-side secrets on the landing host.**
- Checkout API (`webhook_checkout.py`) runs on a separate host/port behind nginx + TLS, with only Stripe env vars. Bind `127.0.0.1`, proxy via nginx.
- Uptime: existing watchdog + `GET /health` every 60 s.

Commands:
```bash
cd product
./deploy_landing.sh --start --port 8130         # local check
sudo ./deploy_landing.sh --nginx --domain decision-os.gamai.io
curl -fsS https://decision-os.gamai.io | grep -q "GAMA Decision OS"
```

### Repo and packages
- Public repo: `github.com/gamai-io/gama-decision-os` (create org if missing). Source-only, no runtime data.
- Branch protection on `main`, required CI (`ruff`, `pytest`, `make bench-l0`).
- `SECURITY.md`, `CONTRIBUTING.md` (DCO), `CODE_OF_CONDUCT.md`, issue templates.
- PyPI: reserve `gama-decision-os` (upload a `0.0.0` placeholder only if the name is at risk; otherwise publish real `1.0.0` at launch).
- Container: `ghcr.io/gamai-io/gama-decision-os:1.0.0` + `:latest`, multi-arch amd64/arm64, SBOM (syft), signed (cosign).
- Docs site: reuse README + `/docs`; no separate Docusaurus in month 1.

Launch-day build:
```bash
python -m build
twine check dist/*
twine upload dist/gama_decision_os-1.0.0*
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/gamai-io/gama-decision-os:1.0.0 --push .
cosign sign ghcr.io/gamai-io/gama-decision-os:1.0.0
```

### Checkout
- Stripe products: Pro monthly €349, Pro annual €3,588/node (2-node min), Enterprise invoice-only.
- Test with `stripe listen --forward-to 127.0.0.1:8444/webhook`; verify `licenses.db` row created; verify duplicate webhook is idempotent.
- Refund policy: 14 days, no questions, stated on site.

---

## 2. Message and proof (D0–D4)

One sentence: **"GAMA Decision OS makes autonomous agents safe to run against real systems: it decides before the action, isolates execution, and returns signed evidence — or rolls back."**

Proof ladder (use in this order):
1. **Live 3-minute demo** — agent tries an irreversible SQL update → L0 asks → approval → Firecracker run → receipt with hash → tamper the receipt → verification fails.
2. **Numbers** — 0.05 ms L0, 2.28 ms restore, −86.2% tokens, 10/10 SWE-lite, 0 false-success.
3. **Artifact** — link to the public repo and the benchmark commands.
4. **Honesty** — explicitly say ECE is still being measured. This builds more trust than a perfect deck.

Do **not** claim: "EU AI Act certified", "100% safe", "replaces auditors", "works with every ERP". Say "evidence pack mapped to Art. 9–15; sufficiency is decided by your auditor".

---

## 3. Channel plan (D4–D30)

### Tier 1 — developer launch
| Channel | Action | Date | Success metric |
|---|---|---|---|
| Hacker News | "Show HN: Open-source control plane that stops agents before they act" — post 15:00 CET Tue/Wed, founder in comments all day | D8 | ≥ 80 points, ≥ 25 comments, ≥ 400 visits |
| r/LocalLLaMA | Technical post: Firecracker 2.28 ms restore + token A/B methodology, no marketing | D9 | ≥ 100 upvotes, ≥ 30 comments |
| r/selfhosted + r/devops | "Self-hosted agent control plane" angle | D12 | 2 posts, ≥ 150 visits total |
| GitHub | `awesome-ai-agents` / `awesome-llmops` PRs | D10 | 2 accepted listings |

### Tier 2 — B2B / BiH region
| Channel | Action | Date | Success metric |
|---|---|---|---|
| LinkedIn (founder) | 3 posts/week: demo clip, benchmark teardown, "false-success" essay. DM 20 warm contacts. | D5–D30 | 10k impressions, 40 profile visits, 8 calls |
| BiH IT associations (BIT Alliance, Hub387, Networks) | Offer free 1-hour workshop "Agenti u produkciji: kontrola i dokazi" | D15 | 1 event booked, 15 attendees |
| Accountants/ERP integrators | 10 targeted e-mails to firms running Pantheon/SAP/custom ERP | D16–D22 | 3 replies, 1 pilot |
| Banks/insurers (compliance leads) | 5 intro e-mails with 1-page EU AI Act mapping | D18 | 2 meetings |
| Universities (ETF Sarajevo, FON) | Guest lecture + student licences | D20 | 1 lecture, 20 Community signups |

### Tier 3 — paid (only if organic shows intent)
- €150 test: LinkedIn single-image ad to "CTO/Head of AI, DACH + Adriatic", landing CTA "Book demo". Kill if CPC > €4 or 0 demos after 1,000 impressions.
- No Google Ads in month 1. Search volume is too low and intent is captured by GitHub.

### Content (2 pieces, not 10)
1. **"0 false-success: how we verify agent work with independent tests"** — methodology + raw results + how to reproduce. Publish D7.
2. **"2.28 ms Firecracker restore for transactional agents"** — architecture + numbers + limits. Publish D14.

Each ends with a demo CTA and a repo link. Cross-post to dev.to and LinkedIn.

---

## 4. 30-day calendar

| Day | Work | Output |
|---|---|---|
| D1–D3 | Close blockers B1–B8; domain, TLS, mail | Landing live on staging, checkout test-mode green |
| D4 | Finalise demo script + record 3-min video | Video file, subtitles BS/EN |
| D5 | Publish site + repo public; no promotion yet | URL works, `README` renders |
| D6 | Soft launch to 20 warm contacts; collect objections | 5 replies, 3 calls booked |
| D7 | Publish post #1 (false-success) | 1 article |
| D8 | **Show HN** | ≥ 80 points or iterate title next week |
| D9 | r/LocalLLaMA post | ≥ 100 upvotes |
| D10 | Directory PRs, Product Hunt draft | 2 PRs |
| D12 | r/selfhosted + r/devops | traffic spike |
| D14 | Publish post #2 (Firecracker) | 1 article |
| D15 | BiH workshop | 15 attendees, 5 leads |
| D16–D22 | 15 outbound e-mails/day (ERP, accounting, compliance) | 20 conversations |
| D18 | 5 enterprise intro e-mails | 2 meetings |
| D20 | University lecture | 20 signups |
| D22 | First Pro trial → paid conversion push | 3 trials active |
| D25 | Webinar: "Agent control in 30 minutes" (live, recorded) | 20 live, 50 replay |
| D28 | Retro: channel ROI, pricing objections, churn risks | Decision memo |
| D30 | Publish transparent "month 1 numbers" post | 1 article |

---

## 5. Measurable targets (month 1)

| Metric | Target | Kill/keep rule |
|---|---|---|
| Landing unique visitors | 1,200 | < 400 = message problem, not traffic problem |
| Demo requests | 25 | < 8 = CTA/offer problem |
| Qualified calls | 12 | < 4 = targeting problem |
| Pro trials | 5 | < 2 = onboarding friction |
| Paid Pro | 2 | 0 = pricing or trust gap |
| Enterprise pilot conversations | 1 | 0 = wrong ICP or no proof |
| GitHub stars | 500 | < 100 = distribution failure |
| Community signups (licence downloads) | 150 | < 40 = install friction |
| Content → demo conversion | ≥ 3% | < 1% = wrong audience |
| Support tickets / trial | < 3 | > 5 = product not ready |

CAC guardrail: if paid spend / paid customers > €1,500 in month 1, stop paid and go all-in on founder-led outbound.

---

## 6. Sales motion

### Pro (self-serve → assisted)
1. Demo request or trial key.
2. 20-min call: one scenario, live gate, receipt.
3. Send a 1-page "control memo": their agent, their tool, risk tier, evidence they would get.
4. 14-day trial with 2 nodes; weekly 15-min check-in.
5. Close annual (2 months free) or monthly. Invoice for BiH, Stripe for EU.

### Enterprise (founder-led)
1. Discovery with security/compliance + engineering in the same call.
2. Security questionnaire + DPA + architecture diagram (have these ready, not "we'll send later").
3. Paid 2-week pilot (€3,500, credited to year 1) on one non-critical workflow. **Never free enterprise pilots.**
4. Evidence review with their auditor.
5. Annual contract + onboarding.

Objection handling:
- *"We already log prompts."* → Prompts are not evidence of execution. Show the receipt chain and the tamper test.
- *"Our agent is internal, low risk."* → Ask what happens on a wrong stock update. Run their scenario through L0. Let the tier speak.
- *"Open source means unsupported."* → Show Pro support terms and the release cadence; show the CI/bench commands.
- *"EU AI Act doesn't apply to us yet."* → Don't argue law. Offer the mapping as preparation; let their counsel decide.

---

## 7. Tracking and instrumentation

- Self-hosted **Umami** or **Plausible** (no cookies, no third-party CDN on the landing). Events: `demo_submit`, `pricing_view`, `docs_click`, `github_click`.
- UTM scheme: `utm_source=hn|reddit|linkedin|email&utm_medium=...&utm_campaign=launch|bih|enterprise`.
- Leads in a single SQLite/Notion table: name, company, source, tier, scenario, next step, date. No lead lives only in a DM.
- Weekly review every Monday: visits → demos → calls → trials → paid. Update this file with actuals.

---

## 8. Risks and countermeasures

| Risk | Signal | Response |
|---|---|---|
| "Yet another agent framework" | HN comments conflate us with orchestration | Lead with *control + evidence*, never with "agent builder" |
| Security researcher finds key in history | Any fork/scan alert | Pre-empt with B1; publish a security audit note on launch day |
| EU AI Act overclaim backlash | Comments challenge legal claims | Copy says "mapping, not certification"; never say "compliant" |
| Price too high for BiH SMBs | Demo calls stall at €299 | Offer Pro monthly + startup 50%; do not cut list price |
| Enterprise pilot scope creep | Custom connector demands before contract | Paid pilot, fixed scope, connector as add-on |
| Founder bandwidth | < 5 outbound/day | Batch outreach 2×/week; use templates; protect demo time |

---

## 9. Day-30 decision gate

Continue to month 2 only if **at least 2 of 3** are true:
1. ≥ 2 paying customers (any tier).
2. ≥ 8 qualified calls with ICP companies.
3. ≥ 300 GitHub stars **and** ≥ 40 Community installs.

If not, do not add features. Change one variable only: ICP, message, or channel. Re-run for 30 days.

---

## 10. Copy-paste launch post (HN)

**Title:** Show HN: Open-source control plane that stops AI agents before they act

**Body:**
> We kept seeing agents report `ok: true` while the database said otherwise. So we built a control layer between the agent and the tool: a deterministic + calibrated risk gate (READ/DRAFT/SEND/IRREVERSIBLE), a sandbox router (runc/gVisor/Firecracker, 2.28 ms snapshot restore), and an evidence gate that hashes and signs the result, or rolls back.
>
> Core is Apache-2.0, self-hosted, no telemetry. We verify agent work with independent tests, not the model's own claim: 10/10 SWE-bench-lite, 0 false-success.
>
> What we do not have yet: a finished ECE number (calibration eval is running) and broad ERP coverage. Happy to answer anything, including the uncomfortable parts.
>
> Repo: <link> · Demo: <link>

---

## 11. Definition of done for this plan

- [ ] Site + repo + checkout live and tested end-to-end with a real card (then refunded).
- [ ] All 8 blockers closed and evidenced (command + output in `out/gtm/`).
- [ ] 15 outbound conversations logged.
- [ ] 2 content pieces published.
- [ ] Month-1 actuals written back into this file.
