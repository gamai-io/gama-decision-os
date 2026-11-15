# BENCHMARK COMPETITIVE 2026-11-13
## GAMA Decision OS vs AI agent control plane / guardrails / observability tržište

> **Status:** decision-grade competitive benchmark, ne pravni savjet i ne nezavisna certifikacija.
> **Datum:** 2026-11-13 (UTC); izvori pristupljeni 2026-11-13/14.
> **Obuhvat:** 20 konkurentskih rješenja + GAMA Decision OS + 1 adjacent (Stripe Agentic Commerce).
> **Metod:** javne product/pricing stranice, GitHub API, interni GAMA dokumenti. Bez hands-on testiranja konkurenata.

### Legenda

| Oznaka | Značenje |
|---|---|
| **DA** | Potvrđeno u javnom opisu, cjenovniku ili repozitoriju. |
| **DJEL** | Djelimično; postoji funkcionalnost, ali ne pokriva puni sloj. |
| **NE** | Nije nađeno u javnom opisu. Ne znači da ne postoji u enterprise verziji. |
| **N/P** | Nije provjereno u ovoj sesiji. |
| **vendor** | Tvrdnja dobavljača; nije nezavisno provjerena. |

**Pravilo za tumačenje:** „NE“ u tabeli znači „nije nađeno u javnom opisu“, ne „ne postoji“. Većina enterprise ugovora ima funkcije koje nisu javno dokumentovane. Sve tvrdnje o konkurenciji imaju izvor `[S#]` ili su označene kao `N/P`.

---

## 0. Metodologija i ograničenja

1. **Cijene** su javni list-price iznosi u USD, bez poreza, kako su objavljeni na zvaničnim pricing stranicama. Enterprise ugovori, regionalne cijene i popusti se razlikuju.
2. **GitHub stars/licence** su povučeni preko GitHub API-ja 2026-11-13/14. Brojevi se mijenjaju dnevno i služe samo kao signal, ne kao mjera kvaliteta.
3. **Sposobnosti konkurenata** su pročitane iz javnih product/pricing stranica i README fajlova. Nisu testirane uživo. Zato su neke ćelije `N/P`.
4. **GAMA metrike** su interne, iz GAMA Decision OS mjerenja i manifesta `[S23][S24]`. Nisu treće-lice auditovane. Gdje postoji razlika između marketinškog i end-to-end broja, eksplicitno je navedena.
5. **Dva izvora nisu bila dostupna:** Cisco/Robust Intelligence stranica je vraćala 403, a PayPal agentic commerce 404. Zato su ti redovi označeni `N/P` i ne ulaze u konačne zaključke.
6. **TAM/market size nije procijenjen** jer u ovoj sesiji nije bilo pouzdanog, provjerljivog javnog izvora za 2026. Fokus je bottom-up competitive benchmark, ne analyst-style TAM model.
7. **Nema tvrdnje „prvi“ ili „jedini na svijetu“.** Tvrdnja je ograničena na uzorak od 20 javno dostupnih konkurenata. Privatna i custom rješenja mogu imati slične funkcije.

---

## 1. Executive summary

- **Jedinstveni smo po closed-loop dokazu.** U uzorku od 20 javnih konkurenata nijedno ne kombinuje sve tri faze — pre-action odluku, izolovano izvršenje i post-action kriptografski potpisan dokaz — u jednom proizvodu. Najbliži su Airia (pre-tool-call enforcement + audit evidence) i AG2 (WAL/audit trail), ali bez signed receipts lanca.
- **Pre-action L0 ispod 2 ms je operativna prednost.** Većina „guardrails“ proizvoda radi kao model-based validator ili LLM-as-judge, ili tek post-hoc evaluacija. Airia marketinški obećava enforcement prije tool call-a, ali ne objavljuje L0 latenciju ni `expected_evidence_spec`.
- **Sandbox ladder je dublji od konkurencije.** runc/gVisor/Firecracker + 2,28 ms snapshot restore je više od jednog hosted sandboxa (E2B), jednog ephemeral sandboxa (LangSmith Sandboxes) ili app-level izbora backend-a (Hermes). To je odbrambena prednost, ali i trošak održavanja.
- **Tržište se konsoliduje i ubrzano širi od observability ka runtime-u.** Guardrails AI je otišao u Harvey, Humanloop u Anthropic, Invariant u Snyk, Lakera u Check Point, Protect AI pod Palo Alto. Istovremeno LangSmith prodaje Agent Server, Sandboxes, Fleet i LLM Gateway. Kupci više ne kupuju „dashboard“ — kupuju control plane.
- **Naše slabe strane su GTM, ne tehnologija.** Nemamo hosted multi-tenant SaaS, 99,9% SLA, SOC 2 Type II/ISO 27001, enterprise UI, javne case studies ni široke SDK integracije. To je ono što konkurencija već ima i što moramo zatvoriti prije prve enterprise prodaje.

---

## 2. Tržišni kontekst (novembar 2026)

### 2.1 Konsolidacija guardrail sloja

| Događaj | Izvor | Šta znači |
|---|---|---|
| Guardrails AI se pridružio Harvey | `[S1]` | Standalone guardrail vendor traži distribuciju kroz vertikalnu aplikaciju. |
| Humanloop se pridružuje Anthropic-u | `[S7]` | Eval/prompt platforma se konsoliduje u model providera. |
| Snyk je preuzeo Invariant Labs | `[S13]` | Agent security ulazi u veći AppSec/DevSecOps stack. |
| Lakera je dio Check Point-a | `[S15]` | AI runtime security se konsoliduje u klasičnu cyber security distribuciju. |
| Protect AI sada vodi na Palo Alto Prisma AIRS | `[S14]` | AI security se konsoliduje u platform vendor-e; tačan datum akvizicije `N/P`. |

**Implikacija:** nezavisni guardrail startup teško dobija enterprise distribuciju. GAMA ne treba da bude još jedan guardrail vendor; treba da bude **proof layer** koji se ugrađuje u postojeće framework-e i platforme.

### 2.2 Observability se širi u runtime

LangSmith više nije samo tracing: na pricing stranici su **Agent Server, Sandboxes, Fleet, Engine, LLM Gateway** `[S4]`. Langfuse dodaje **AI Gateway** `[S5]`. Arize prodaje **Signal** i **Alyx** agente `[S6]`. AgentOps dodaje replay i cost tracking `[S17]`.

**Implikacija:** pure observability je commoditized. Diferencijacija je u tome ko **donosi odluku prije akcije** i ko **dokazuje poslije akcije**.

### 2.3 Sandbox je postao samostalan sloj

E2B ima enterprise minimum od **$3.000/mj** i do **1.100 konkurentnih sandboxa** `[S16]`. LangSmith Sandboxes se skaliraju na hiljade `[S4]`. Hermes nudi **6 terminal backend-a**: local, Docker, SSH, Modal, Daytona, Vercel Sandbox `[S20]`. OpenClaw nudi opcioni host sandbox i Microsoft Execution Containers na Windowsu `[S19]`.

**Implikacija:** sandbox više nije diferencijator sam po sebi. Diferencijator je **politika iznad sandboxa + dokaz ispod njega**.

### 2.4 Agent harness je komoditizovan

| Projekat | GitHub stars | Licenca | Signoz |
|---|---:|---|---|
| OpenClaw | 394.396 | MIT | 29 kanala, native apps, local-first, bez plaćenog tiera `[S19]` |
| Hermes Agent | 263.218 | MIT | self-improving skills/memory, 6 backend-a `[S20]` |
| Open Interpreter | 68.882 | Apache-2.0 | terminal UX, harness emulation `[S10]` |
| CrewAI | 60.865 | MIT | agent framework + enterprise platform `[S11]` |

**Implikacija:** ne treba se takmičiti kao još jedan harness. Treba biti sloj koji harness **poziva** prije i poslije akcije.

### 2.5 Compliance je ulaznica za enterprise

Airia javno mapira **EU AI Act, NIST AI RMF, SR 11-7, HIPAA, ISO 42001, SOC 2** `[S18]`. LangSmith, Langfuse, Humanloop, PromptLayer i AgentOps prodaju **SOC 2 Type II, ISO 27001, HIPAA, GDPR** `[S4][S5][S7][S8][S17]`. Kupac više ne pita „da li ima guardrails“; pita „pokaži mi audit trail i compliance mapping“.

### 2.6 Proof gap je naš wedge

Svi imaju **logove, trace-ove i eval rezultate**. Skoro niko ne prodaje **nepromjenjiv, kriptografski potpisan dokaz da je konkretna akcija izvršena tačno kako je odobreno**. Airia ima audit evidence, AG2 ima WAL/audit trail, ali nijedno javno ne tvrdi Ed25519 potpisane receipts u hash-lancu. To je prostor za GAMA Decision OS.

---

## 3. GAMA Decision OS baseline (ono što poredimo)

| Sloj | GAMA tvrdnja | Dokaz / status |
|---|---|---|
| **Gate 1: Pre-Action Decision** | L0 odluka ispod **2 ms**; klase **READ / DRAFT / SEND / IRREVERSIBLE**; `expected_evidence_spec`; kalibracija **T=0,2**, **ECE 0,035** | Interno mjerenje; dio manifesta `[S23]`. Nije nezavisno auditovano. |
| **Gate 2: Sandboxed Execution** | runc **110 ns**, gVisor **751 ns**, Firecracker **54 ns**; cold boot **1,846 s**; snapshot restore **2,28 ms**; HITL za SEND/IRREVERSIBLE | VMLAB mjerenja `[S23]`. 54 ns je syscall/mem latencija, ne end-to-end. |
| **Gate 3: Post-Action ProofGate** | SHA-256 hash-lanac + **Ed25519 potpisani receipts** u GTL SQLite ledgeru; rollback na grešci | Interni dizajn; implementacija nije treće-lice auditovana. |
| **Tool schema compression** | **398 alata / 213.781 B → 20.076 B prosječno = 90,6% (semantička selekcija)** ušteda na schema sloju | Interno izmjereno. Live A/B ukupne prompt uštede je **-12,3%** jer ToolRAG cap 64 već radi; vidi ograničenje u §7.4. |
| **Flota i integracije** | 6 čvorova, MCP, OpenCode plugin, **296 alata u runtime promptu / 398 u katalogu**, RLDF (DPO near-miss, Llama-3.2-3B LoRA) | Interni inventar. Nije nezavisno verifikovano. |
| **EU AI Act** | Mapiranje na **Član 12 (record-keeping), 14 (human oversight), 15 (accuracy/robustness/cybersecurity)** | Mapiranje, ne certifikacija. Certifikacija je „u toku“ `[S23]`. |

**Važna napomena o kalibraciji:** Gate 1 kalibracija (T=0,2, ECE 0,035) i RLDF near-miss eksperiment (Llama-3.2-3B LoRA, ECE 0,2992 na n=1200) su **dva različita mjerenja**. Ne spajati ih u istu tvrdnju. Prvo je kalibracija decision sloja; drugo je eval adaptera.

---

## 4. Market map

| Kategorija | Rješenja | Šta kupac dobija | Šta im nedostaje za „control plane“ |
|---|---|---|---|
| **Agent harness / personal agents** | OpenClaw, Hermes Agent, Open Interpreter | Izvršavanje, memorija, kanali, skills, lokalni gateway | Enterprise policy, audit proof, compliance, multi-tenant governance |
| **Agent frameworks** | CrewAI, AG2, Letta, LangGraph | Orkestracija, multi-agent, memory, HITL | Deterministički pre-action gate, signed receipts, runtime ladder |
| **Guardrails / AI security** | Guardrails AI, NeMo Guardrails, Invariant/Snyk, Lakera/Check Point, Protect AI/Palo Alto | Input/output validacija, detekcija, red teaming, policy | Post-action crypto proof, dublji sandbox, ERP kontekst |
| **Observability / eval** | LangSmith, Langfuse, Arize, Humanloop, PromptLayer, AgentOps | Tracing, evals, prompt mgmt, cost, replay | Pre-action enforcement, sandbox, tamper-evident receipts |
| **Sandbox** | E2B, LangSmith Sandboxes, Hermes backends | Izolovano izvršavanje koda | Policy iznad sandboxa, decision log, proof |
| **Enterprise AI control plane** | Airia | Discovery, MCP gateway, policy, approvals, compliance mapping | Kriptografski receipts, runtime ladder, deterministic L0 |
| **Payment rail (adjacent)** | Stripe Agentic Commerce | Agent Wallet, Shared Payment Tokens, UCP, MPP/x402 `[S22]` | Nije control plane; integracija za Gate 2/3, ne konkurent |

---

## 5. Velika tabela poređenja

> **Tumačenje kolona:** `Pre-action` = odluka/politika prije izvršenja; `Runtime` = enforcement u toku; `Post-action dokaz` = nepromjenjiv dokaz poslije; `Sandbox` = izolovano izvršavanje; `Compliance` = javno navedene certifikacije/mapiranja. `Cijena` je list-price, bez poreza.

| # | Rješenje (izvor) | Kategorija | Pre-action | Runtime | Post-action dokaz | Observability / eval | Sandbox | Compliance | Cijena (list) | OSS (licenca / stars) | Snaga | Slabost |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | **GAMA Decision OS** `[S23][S24]` | Control plane / proof layer | **DA** — L0 <2 ms, 4 klase, `expected_evidence_spec` | **DA** — HITL + policy + runtime ladder | **DA** — SHA-256 lanac + Ed25519 receipts | DJEL — trace + RLDF eval; nema javni SaaS | **DA** — runc/gVisor/Firecracker, 2,28 ms snapshot | DJEL — EU AI Act Art 12/14/15 mapiranje; certifikacija u toku | interno / nije javno | privatno; MCP + OpenCode plugin | Closed-loop proof, ERP/SQL fokus, 296 alata, flota | Nema hosted SaaS, SOC2, enterprise UI, case studies |
| 1 | **Guardrails AI** `[S1][S2]` | Guardrails / reliability | DJEL — input/output validatori; nema risk tier | DJEL — blokira/preradi output | NE | DA — evals + synthetic data (Snowglobe) | NE | N/P | nije javno; kontakt | Apache-2.0; 7.608 stars | Guardrails Hub, validatori, Harvey distribucija | Nema action gate, sandbox, signed proof; konsolidacija (Harvey) |
| 2 | **NVIDIA NeMo Guardrails** `[S3]` | Guardrails toolkit | DJEL — input/dialog/execution/output rails | DJEL — rails | NE | DA — eval + vulnerability scan | NE | nema built-in certifikata; self-host | besplatno | Apache-2.0; 7.500 stars | Colang dialog rails, NVIDIA ekosistem | Nema risk tier/proof; self-host operacija |
| 3 | **LangSmith + LangGraph** `[S4]` | Observability + agent runtime | DJEL — LLM Gateway, Agent Authorization beta | DA — gateway + sandbox | NE — traces only | DA — traces, evals, Engine | DA — Sandboxes, TTL, snapshot/fork, scale to 1000s | SOC2 Type II, ISO27001, HIPAA, GDPR, SLA (Enterprise) | Free; Plus $39/seat/mj; Enterprise custom; LSU $1 | platforma proprietary; LangGraph MIT 44.919 stars | Full lifecycle, managed, ogroman ekosistem | Nema signed receipts; nema deterministic L0; vendor lock-in |
| 4 | **Langfuse** `[S5]` | Observability / eval | NE | DJEL — AI Gateway | NE — traces only | DA — traces, evals, prompt mgmt | NE | SOC2 Type II, ISO27001, HIPAA, GDPR (Pro/Enterprise) | Hobby $0; Core $29/mj; Pro $199/mj; Enterprise $2.499/mj | self-host OSS; GitHub API NOASSERTION; 37.397 stars | Jeftin, OSS, prompt mgmt, self-host | Post-hoc; nema enforcement/sandbox/proof |
| 5 | **Arize Phoenix / AX** `[S6]` | Observability / eval | NE | NE | NE — traces only | DA — evals, trajectory, Signal, Alyx | NE | SOC2 Type II, GDPR navedeni; HIPAA N/P | Free; Pro $50/mj; Enterprise custom | Phoenix OSS; NOASSERTION; 12.277 stars | Dubok eval, trajectory viz, agent analytics | Nema runtime enforcement/proof; enterprise sales |
| 6 | **Humanloop** `[S7]` | Evals / prompt / observability | NE | NE | NE | DA — evals, prompts, observability | NE | SOC2 Type II, GDPR, HIPAA (BAA), VPC | free trial; Enterprise custom | proprietary | Eval UI, enterprise compliance, Anthropic distribucija | Nema runtime/sandbox/proof; konsolidacija (Anthropic) |
| 7 | **PromptLayer** `[S8]` | Prompt mgmt / observability | DJEL — deployment approvals (ne runtime) | NE | NE | DA — prompts, traces, evals | NE | SOC2 Type II, GDPR, HIPAA, CCPA | Free; Pro $49/mj; Team $500/mj; Enterprise custom | proprietary; SDK OSS | Prompt versioning, deployment approvals, niska cijena | Nema runtime gate/sandbox/proof |
| 8 | **AgentOps** `[S17]` | Observability / replay | NE | NE | NE — replay/logs | DA — replay, cost, prompt injection | NE | SOC2, HIPAA, NIST AI RMF (Enterprise) | Free (5k events); Pro od $40/mj; Enterprise custom | SDK OSS; licenca N/P; platforma proprietary | Time-travel replay, 400+ integracija, niska cijena | Post-hoc; nema enforcement/sandbox/proof |
| 9 | **E2B** `[S16]` | Sandbox | NE | DA — izolacija | NE | NE | DA — hosted sandbox | N/P | Hobby $0 + usage; Pro $150/mj + usage; Enterprise od $3.000/mj | Apache-2.0; 14.849 stars | Hosted sandbox scale (1.100), SDK, per-second | CPU-only; nema policy/proof/observability |
| 10 | **Airia** `[S18]` | Enterprise AI control plane | **DA** — policy prije tool call-a; allow/block/approval/redact | **DA** — enforcement | DJEL — audit evidence; nema crypto lanac (nije tvrđeno) | DA — governance dashboard | NE | EU AI Act, NIST AI RMF, SR 11-7, HIPAA, ISO 42001, SOC2 (vendor) | nije javno; demo | proprietary | Discovery, MCP gateway, compliance mapping, enterprise UI | Nema crypto receipts, sandbox ladder; privatne cijene |
| 11 | **Invariant Labs / Snyk** `[S13]` | Agent security / guardrails | **DA** — contextual guardrails nad tool call-ovima | **DA** — policy enforcement | NE | DA — Explorer | NE | N/P; Snyk platform | nije javno | Guardrails Apache-2.0; 476 stars; Snyk proprietary | Security research, MCP Scan, Snyk distribucija | Nema sandbox/proof; rano/akvizicija |
| 12 | **Lakera / Check Point** `[S15]` | AI security | **DA** — runtime detection | **DA** — block/monitor | NE | DA — red teaming | NE | N/P; Check Point | free tier; Enterprise custom (nije javno) | proprietary | <50 ms claim, 100+ jezika, Check Point distribucija | Detection, ne action decision; nema proof/sandbox |
| 13 | **Protect AI / Palo Alto Prisma AIRS** `[S14]` | AI security platform | **DA** — AI Gateway/runtime | **DA** — block/monitor | NE | DA — posture/red teaming | NE | N/P; Palo Alto | nije javno | proprietary | Full AI security stack, Palo Alto distribucija | Nema deterministic L0/proof/sandbox ladder; broad, ne deep |
| 14 | **CrewAI** `[S11]` | Agent framework + platform | DJEL — guardrails + HITL | DJEL — guardrails/HITL | NE | DA — tracing/OTel | NE | SSO/RBAC/PII policies; SOC2 N/P | Free (50 executions/mj); Enterprise custom | MIT; 60.865 stars; enterprise proprietary | Visual studio, enterprise governance, 65% F500 (vendor) | Nema sandbox/proof; framework lock-in |
| 15 | **AG2 (AutoGen)** `[S12]` | Agent framework / AgentOS | DJEL — HITL | DJEL — HITL | DJEL — WAL/audit trail; nema crypto | DA — telemetry/eval | NE | nema certifikata; self-host | besplatno | Apache-2.0; 5.062 stars | Multi-agent Network/Hub, memory, community | Nema policy engine/sandbox/proof; v1 migracija |
| 16 | **OpenClaw** `[S19]` | Personal agent harness | DJEL — approvals/pairing | DJEL — host sandbox optional | NE | NE (logs) | DJEL — optional host sandbox; MEC na Windowsu | nema enterprise certifikata; local-first | besplatno; nema plaćenog tiera | MIT; 394.396 stars | 29 kanala, native apps, local-first, ogromna zajednica | Nema enterprise governance/proof/compliance; security config burden |
| 17 | **Hermes Agent (Nous)** `[S20]` | Self-improving agent harness | N/P — permissions/approvals nisu u README-u | DJEL — sandbox backends | NE | NE | DA — 6 backend-a: local, Docker, SSH, Modal, Daytona, Vercel Sandbox | nema; self-host | besplatno; modeli po potrošnji | MIT; 263.218 stars | Self-improving skills/memory, kanali, portability | Nema policy/proof/compliance; enterprise support N/P |
| 18 | **Letta (MemGPT)** `[S9]` | Stateful agent OS | DJEL — permissions | DJEL — sandboxes | NE | NE | DA — cloud/remote sandboxes | Enterprise RBAC/SAML/OIDC; SOC2 N/P | Free; Pro $20/mj; Teams Pro $20/seat/mj; Enterprise custom | Apache-2.0; 25.432 stars | Memory OS, stateful agents, desktop | Nema action risk/proof; sandbox nije kernel ladder |
| 19 | **Open Interpreter** `[S10]` | Coding agent | DJEL — approvals | DA — OS sandbox | NE | NE | DA — native sandbox macOS/Linux/Windows | nema | besplatno | Apache-2.0; 68.882 stars | Terminal UX, harness emulation, Codex kompatibilnost | Nema governance/proof/compliance |
| 20 | **Robust Intelligence / Cisco AI Defense** `[S26]` | AI security | N/P | N/P | N/P | N/P | N/P | N/P | nije javno | proprietary | Cisco distribucija (N/P) | Sve N/P — nije provjereno; ne ulazi u zaključke |

**Adjacent napomena — Stripe Agentic Commerce** `[S22]`: nije control plane. Nudi Agent Wallet, Shared Payment Tokens, UCP, MPP/x402. Relevantno kao **payment rail** za Gate 2/3 (npr. IRREVERSIBLE plaćanje), ne kao konkurent. PayPal agentic commerce stranica je vratila 404; `N/P`.

---

## 6. Differentiators: šta mi imamo što oni nemaju / šta oni imaju što mi nemamo

| Rješenje | Mi imamo što oni nemaju | Oni imaju što mi nemamo |
|---|---|---|
| **Guardrails AI** | Deterministički L0 + sandbox ladder + signed receipts. | Guardrails Hub validatori, Snowglobe synthetic data, Harvey enterprise distribucija. |
| **NeMo Guardrails** | Closed-loop enforcement + kriptografski dokaz + ERP kontekst. | Colang dialog modeling, NVIDIA safety modeli, velika Apache-2.0 zajednica. |
| **LangSmith** | L0 risk tier + `expected_evidence_spec` + Ed25519 receipts. | Managed observability/eval, Agent Server, Fleet, Engine, SOC2/ISO/HIPAA, SLA, ogroman ekosistem. |
| **Langfuse** | Action enforcement + sandbox + proof. | Zreo OSS observability, prompt mgmt, niska cijena, self-host, SOC2/ISO/HIPAA. |
| **Arize Phoenix/AX** | Pre-action gate + signed receipts. | Dubok eval/experiment UI, Phoenix OSS, trajectory analytics, enterprise trust. |
| **Humanloop** | Runtime enforcement + sandbox + proof. | Eval/prompt UI, enterprise compliance, Anthropic distribucija. |
| **PromptLayer** | Runtime gate + sandbox + proof. | Prompt management, deployment approvals, niska cijena, SOC2/HIPAA. |
| **AgentOps** | Pre-action decision + signed receipts + runtime ladder. | Time-travel replay, 400+ integracija, niska cijena, SOC2/HIPAA/NIST. |
| **E2B** | Policy/decision + proof + multi-runtime ladder. | Hosted sandbox na skali (1.100), SDK/templates, per-second billing, $3k enterprise minimum. |
| **Airia** | Kriptografski receipts + deterministic L0 + runtime ladder. | Discovery/shadow AI, MCP gateway, policy/approval UI, compliance mapping, enterprise connectors. |
| **Invariant / Snyk** | Proof + sandbox ladder + hosted control plane potencijal. | MCP Scan, security research, Snyk distribucija, Guardrails OSS. |
| **Lakera / Check Point** | Deterministički action gate + proof + sandbox. | <50 ms detection claim, 100+ jezika, red teaming, Check Point distribucija. |
| **Protect AI / Palo Alto** | Proof + L0 + runtime ladder. | Full AI security stack, AI gateway, supply chain, red teaming, agent identity, Palo Alto distribucija. |
| **CrewAI** | Signed audit proof + sandbox ladder. | Agent framework, visual studio, enterprise governance, 65% F500 (vendor), onboarding. |
| **AG2** | Pre-action risk + signed receipts + runtime ladder. | Multi-agent Network/Hub, WAL/audit trail, Apache-2.0 zajednica, memory/compaction. |
| **OpenClaw** | Enterprise governance, proof, compliance. | 29 kanala, native desktop/mobile apps, 394k stars, local-first onboarding, bez plaćenog tiera. |
| **Hermes Agent** | Proof/compliance/policy. | Self-improving skills/memory, 6 sandbox backend-a, kanali, 263k stars, trajectory generation. |
| **Letta** | Proof/policy/runtime ladder. | Stateful memory OS, agent identity, desktop, cloud sandboxes, $20 cijena. |
| **Open Interpreter** | Governance/proof/multi-runtime. | Terminal UX, harness emulation, Codex kompatibilnost, 68.9k stars. |
| **Robust Intelligence / Cisco** | Jasan proof/L0/sandbox dizajn (ako se potvrdi). | Cisco AI Defense distribucija — `N/P`, ne ulazi u zaključke. |

---

## 7. 5 načina na koje smo bolji (sa dokazom)

### 7.1 Closed-loop proof: odluka → izvršenje → potpisani dokaz

**Tvrdnja:** GAMA je jedino rješenje u uzorku koje javno kombinuje pre-action odluku, izolovano izvršenje i post-action kriptografski dokaz.

**Dokaz:**
- GAMA Gate 1 + Gate 2 + Gate 3, SHA-256 lanac + Ed25519 receipts `[S23]`.
- Airia ima pre-tool-call enforcement i audit evidence, ali ne tvrdi signed receipts `[S18]`.
- AG2 ima WAL i audit trail, ali ne kriptografski potpisane receipts `[S12]`.
- LangSmith, Langfuse, Arize, AgentOps imaju trace-ove/logove, ne tamper-evident receipts `[S4][S5][S6][S17]`.
- E2B ima sandbox, ali ne policy/decision/proof `[S16]`.

**Ograničenje:** Uzorak je 20 javnih konkurenata. Privatni enterprise add-oni mogu imati slično. „Proof“ nije isto što i pravna certifikacija.

**Prodajna rečenica:** „Ne pitajte agenta da li je uradio — pokažite potpisan dokaz da je uradio tačno ono što je odobreno.“

### 7.2 Deterministički L0 ispod 2 ms

**Tvrdnja:** L0 odluka sa 4 klase i `expected_evidence_spec` je brža i operativnija od model-based guardrails ili LLM-as-judge pristupa.

**Dokaz:**
- GAMA L0 ispod 2 ms; interno mjereno `[S23]`.
- Guardrails AI i NeMo rade validaciju kroz modele/rails, što je sporije i probabilistički `[S1][S3]`.
- Airia obećava enforcement prije tool call-a, ali ne objavljuje L0 latenciju ni evidence spec `[S18]`.
- Lakera tvrdi <50 ms runtime detection `[S15]` — to je 25× sporije od 2 ms, ali drugačiji sloj (detekcija napada, ne odluka o akciji).

**Ograničenje:** 2 ms je L0 odluka, ne end-to-end tool call. Nije nezavisno mjereno. Pod visokim opterećenjem i sa velikim kontekstom latencija može rasti.

**Prodajna rečenica:** „Odluka prije akcije, ne naknadna pamet.“

### 7.3 Runtime ladder: runc / gVisor / Firecracker + 2,28 ms snapshot

**Tvrdnja:** Tri nivoa izolacije sa brzim snapshot restore-om daju izbor između performanse i bezbjednosti; konkurencija uglavnom nudi jedan sandbox.

**Dokaz:**
- GAMA: runc 110 ns, gVisor 751 ns, Firecracker 54 ns; cold boot 1,846 s; snapshot restore 2,28 ms `[S23]`.
- E2B: jedan hosted sandbox, CPU-only, per-second `[S16]`.
- LangSmith: jedan ephemeral sandbox sloj, TTL/snapshot/fork `[S4]`.
- Hermes: 6 backend-a, ali app-level izbor, ne kernel/microVM ladder `[S20]`.
- OpenClaw: opcioni host sandbox / Microsoft Execution Containers `[S19]`.
- Open Interpreter: native OS sandbox `[S10]`.

**Ograničenje:** Firecracker 54 ns je syscall/mem latencija, ne end-to-end. Cold boot je 1,846 s; 2,28 ms je restore iz snapshot-a. Ne miješati ta dva broja u prodaji.

**Prodajna rečenica:** „Izolacija se bira prema riziku, ne po defaultu.“

### 7.4 Tool schema compression: 90,6% na schema sloju

**Tvrdnja:** 398 alata / 213.781 B → 20.076 B prosječno = 90,6% (semantička selekcija) ušteda na schema sloju; to čini 296-tool agent praktičnim.

**Dokaz:**
- Interno izmjereno; brojevi iz GAMA konteksta i mjerenja `[S23]`.
- Bez kompresije, 398 tool schema troši ogroman dio konteksta i povećava cijenu/latenciju.

**Ograničenje (obavezno navesti):** Live A/B je pokazao **-12,3% ukupne prompt uštede**, jer produkcijski ToolRAG cap 64 već radi. 90,6% je **schema-layer** ušteda, ne end-to-end. Ne prodavati kao „90% ukupne uštede“ — to bi bila lažna tvrdnja.

**Prodajna rečenica:** „Više alata, manje konteksta — bez skupog prepisivanja prompta.“

### 7.5 EU AI Act Art 12/14/15: dokaz vezan za akciju

**Tvrdnja:** Hash-lanac + Ed25519 receipts + human gates mapiraju se na Art 12 (record-keeping), Art 14 (human oversight) i Art 15 (accuracy/robustness/cybersecurity) bolje od običnih logova i trace-ova.

**Dokaz:**
- GAMA mapiranje u manifestu `[S23]`.
- Airia mapira EU AI Act/NIST/SR 11-7/HIPAA/ISO 42001/SOC2, ali audit evidence nije kriptografski lanac `[S18]`.
- LangSmith/Langfuse/Humanloop/PromptLayer/AgentOps prodaju SOC2/HIPAA/GDPR `[S4][S5][S7][S8][S17]`, ali ne action-level proof.
- AG2 WAL/audit trail je najbliži, ali bez potpisa `[S12]`.

**Ograničenje:** Mapiranje nije certifikacija. Art 12/14/15 zahtjevi su širi od logova (npr. data governance, tehnička dokumentacija, tačnost, robustnost). Potrebna je pravna validacija i conformity assessment.

**Prodajna rečenica:** „Audit trail koji se ne može prepisati — i koji regulator može provjeriti.“

---

## 8. 5 rupa koje moramo zatvoriti prije prodaje

| # | Rupa | Zašto je rupa | Ko to već ima | Kako zatvoriti (90 dana) | KPI |
|---:|---|---|---|---|---|
| 1 | **Hosted multi-tenant SaaS + SLA** | Kupci ne žele da sami održavaju flotu; enterprise traži 99,9% SLA i status page. | LangSmith, Langfuse, Arize, AgentOps, E2B `[S4][S5][S6][S17][S16]` | EU-hosted control plane (Frankfurt/BiH), tenant isolation, per-tenant KMS, usage metering, 99,9% SLA, DR, on-call. | Onboarding <1 dan; p95 receipt <50 ms; uptime 99,9%. |
| 2 | **SOC 2 Type II / ISO 27001 / HIPAA / GDPR DPA** | Bez toga nema enterprise procurement-a; security questionnaire blokira prodaju. | LangSmith, Langfuse, Humanloop, PromptLayer, AgentOps, Airia `[S4][S5][S7][S8][S17][S18]` | SOC2 auditor, ISO 27001 gap assessment, HIPAA BAA (ako health), GDPR DPA, subprocessors lista, pen test, trust center. | Report za 6–9 mjeseci; security questionnaire pass rate >90%. |
| 3 | **Enterprise UI** | Approval inbox, policy editor i evidence explorer su mjesto gdje kupac živi; CLI/MCP nije dovoljno. | LangSmith, Langfuse, Arize, Airia, CrewAI `[S4][S5][S6][S18][S11]` | 3 ekrana: Approvals, Policies, Evidence; RBAC/SSO/SCIM; audit export CSV/JSON; dashboards. | Time-to-approve <30 s; false block <2%; NPS >40. |
| 4 | **Integracije, SDK i dokumentacija** | Kupac uvodi u postojeći stack; 10-min quickstart je uslov za pilot. | LangSmith/LangGraph, CrewAI, AG2, OpenClaw/Hermes, E2B `[S4][S11][S12][S19][S20][S16]` | Python/TS SDK; LangChain/LangGraph, CrewAI, OpenAI Agents SDK, MCP, OTel; GitHub Action; 5 recepata; docs site. | Time-to-first-receipt <10 min; 5 adaptera; 90% docs coverage. |
| 5 | **Trust, case studies i pravni dosje** | Bez reference kupca i dokaza u produkciji, „EU AI Act“ tvrdnje su marketing. | CrewAI (65% F500 vendor claim), Airia (compliance mapping), LangSmith (customers) `[S11][S18][S4]` | 3 design partnera (BiH/EU), redacted case study, load test, pen test, EU AI Act conformity dossier, incident response, osiguranje. | 3 logotipa; 1 audit report; 1 javni benchmark. |

### 8.1 Dodatna rupa koju ne treba zanemariti: model/provider coverage

GAMA trenutno radi sa DeepSeek/OpenRouter/Claude i lokalnim modelima kroz harness. Konkurencija ima šire provider coverage i fallback-e (LangSmith LLM Gateway `[S4]`, Hermes Nous Portal/OpenRouter/BYOK `[S20]`, Letta BYOK `[S9]`). Za enterprise prodaju treba jasna matrica podržanih modela, cijena i data residency opcija. Ovo nije među „5 glavnih“ jer je rješivo integracijom, ali može blokirati pilote.

---

## 9. Pozicioniranje

### 9.1 Jedna rečenica

**GAMA Decision OS je proof-layer control plane za autonomne agente: svaka akcija dobije odluku ispod 2 ms, izolovano izvršenje i kriptografski dokaz — preko bilo kog agent frameworka, bez zaključavanja u model.**

### 9.2 Tri ciljne niše

| Niša | Kupac | Bolna tačka | Naš dokaz | Ponuda |
|---|---|---|---|---|
| **1. Regulisani ERP/finansije u BiH/EU** | CFO, CIO, compliance | Agent ne smije pisati u `customers`, glavnu knjigu ili fakture bez dokaza i rollback-a. | 3-Gate + SHA-256 + rollback + `erp_prod`/`erp_archive` kontekst `[S23]`. | Pilot 6 sedmica, 1 proces (ulaz robe ili faktura), mjerenje false-block i vremena odobrenja. |
| **2. EU AI Act high-risk deploymenti** | Compliance, legal, security | Art 12/14/15 audit bez kriptografskog lanca je teško odbraniti pred regulatorom. | Hash-lanac + Ed25519 + HITL + mapiranje `[S23]`. | Conformity dossier + evidence export + human oversight workflow. |
| **3. Agent platforme i system integratori** | CTO, product, SI partner | Treba im proof/guardrail layer, ne još jedan framework; ne žele da grade audit sami. | MCP + OpenCode plugin + 296 alata + flota `[S23]`. | White-label/OEM proof layer, revenue share, zajednički pilot. |

### 9.3 Messaging

- „Ne prodajemo još jedan agent framework. Prodajemo dokaz da je agent uradio tačno ono što je smio.“
- „Vaš agent, naš control plane.“
- „Od ‚vjeruj mi‘ do ‚evo potpisanog dokaza‘.“

---

## 10. Preporučeni 90-dnevni plan

| Faza | Dani | Fokus | Izlaz |
|---|---:|---|---|
| **Pakovanje** | 0–30 | Definisati 3 paketa (Proof, Control, Enterprise), ICU pricing, 1-pager, demo scenario. | Pricing sheet + demo + 3 design partnera. |
| **Hosted alpha** | 0–45 | EU-hosted multi-tenant alpha, tenant isolation, SSO, approval inbox. | 3 tenanta, p95 receipt <50 ms. |
| **Compliance** | 30–60 | SOC2 gap assessment, DPA, subprocessors, pen test narudžba. | Gap report + pen test scope. |
| **Integracije** | 30–60 | Python/TS SDK, LangChain/LangGraph, CrewAI, MCP, OTel. | 5 adaptera, 10-min quickstart. |
| **Dokaz** | 60–90 | Load test, 1 case study, javni benchmark, EU AI Act dossier draft. | 1 case study + 1 audit report + launch. |

---

## Appendix A: Izvori

> Svi izvori pristupljeni 2026-11-13/14. Cijene i funkcije se mogu promijeniti.

| ID | Izvor | URL |
|---|---|---|
| S1 | Guardrails AI — homepage, „Guardrails AI joins Harvey“, Snowglobe, Hub | https://www.guardrailsai.com/ |
| S2 | Guardrails AI — GitHub (Apache-2.0, stars) | https://github.com/guardrails-ai/guardrails |
| S3 | NVIDIA NeMo Guardrails — GitHub (Apache-2.0, rails, eval) | https://github.com/NVIDIA-NeMo/Guardrails |
| S4 | LangSmith / LangChain — pricing, Agent Server, Sandboxes, Fleet, Engine, LLM Gateway, SOC2/ISO/HIPAA | https://www.langchain.com/pricing |
| S5 | Langfuse — pricing, cloud/self-host, SOC2/ISO/HIPAA, AI Gateway | https://langfuse.com/pricing |
| S6 | Arize — pricing, AX/Phoenix, Signal/Alyx, compliance | https://arize.com/pricing/ |
| S7 | Humanloop — pricing, „joining Anthropic“, compliance | https://humanloop.com/pricing |
| S8 | PromptLayer — pricing, deployment approvals, compliance | https://www.promptlayer.com/pricing |
| S9 | Letta — pricing, stateful agents, sandboxes, enterprise | https://www.letta.com/pricing |
| S10 | Open Interpreter — GitHub (Apache-2.0, sandbox, harness) | https://github.com/openinterpreter/openinterpreter |
| S11 | CrewAI — pricing, enterprise governance, 65% F500 claim | https://www.crewai.com/pricing |
| S12 | AG2 (AutoGen) — GitHub (Apache-2.0, Network/Hub, WAL) | https://github.com/ag2ai/ag2 |
| S13 | Invariant Labs — Explorer, Guardrails, MCP Scan, Snyk acquisition | https://www.invariantlabs.ai/ |
| S14 | Protect AI — redirect na Palo Alto Prisma AIRS | https://protectai.com/ |
| S15 | Lakera — Check Point, runtime security, <50 ms claim | https://www.lakera.ai/ |
| S16 | E2B — pricing, sandbox rates, enterprise minimum | https://e2b.dev/pricing |
| S17 | AgentOps — pricing, replay, prompt injection, compliance | https://www.agentops.ai/ |
| S18 | Airia — control plane, pre-tool-call enforcement, compliance mapping | https://airia.com/ |
| S19 | OpenClaw — homepage, 29 channels, MIT, no paid tier, security | https://openclaw.ai/ |
| S20 | Hermes Agent — GitHub (MIT, 6 backends, skills/memory) | https://github.com/NousResearch/hermes-agent |
| S21 | GitHub API — stars/licence za repoe (povučeno 2026-11-13/14) | https://api.github.com/repos/ |
| S22 | Stripe — Agentic Commerce docs (Agent Wallet, SPT, UCP, MPP/x402) | https://docs.stripe.com/agentic-commerce |
| S23 | GAMA Decision OS Manifesto | `docs/GAMA_DECISION_OS_MANIFESTO.md` |
| S24 | GAMA GATES | interno, nije javno |
| S25 | GAMA API / arhitektura | interno, nije javno |
| S26 | Cisco AI Defense / Robust Intelligence — stranica nije bila dostupna (403); `N/P` | https://www.cisco.com/site/us/en/products/security/ai-defense/index.html |

---

## Appendix B: Verification notes

1. **Guardrails AI konsolidacija:** stranica eksplicitno kaže „Guardrails AI joins Harvey“ i ima datum objave Sep 9, 2026 `[S1]`. Detalji transakcije nisu provjereni.
2. **Humanloop konsolidacija:** stranica kaže „Humanloop is joining Anthropic“ `[S7]`. Detalji transakcije nisu provjereni.
3. **Invariant/Snyk:** stranica kaže „Snyk Acquires Invariant Labs“ `[S13]`. Detalji transakcije nisu provjereni.
4. **Lakera/Check Point:** footer i blog referenciraju Check Point `[S15]`. Tačan datum transakcije/konsolidacije nije provjeren.
5. **Protect AI/Palo Alto:** `protectai.com` vodi na Palo Alto Prisma AIRS `[S14]`. Tačan datum transakcije/konsolidacije nije provjeren.
6. **Robust Intelligence/Cisco:** stranica 403 `[S26]`; sve ćelije `N/P`. Ne koristiti u prodajnim tvrdnjama.
7. **PayPal agentic commerce:** URL 404; `N/P`. Ne koristiti u prodajnim tvrdnjama.
8. **Cijene:** list-price; enterprise ugovori se razlikuju. Npr. LangSmith Enterprise je „custom“ iako ima javne komponente `[S4]`.
9. **Stars:** GitHub API `[S21]`; brojevi se mijenjaju dnevno.
10. **GAMA brojevi:** interni; nisu treće-lice auditovani. Za prodaju prema enterprise kupcu, pripremiti reproducibilne benchmark skripte i sirove rezultate.

---

## Appendix C: Šta bi trebalo pobiti u narednoj iteraciji

- **Airia** je najbliži konkurent po pre-action enforcement-u; potrebno je uraditi hands-on demo i provjeriti da li ima API za custom policy i audit export.
- **LangSmith Agent Server/Sandboxes** je najbliži po full-lifecycle-u; potrebno je provjeriti da li Agent Authorization beta može poslužiti kao pre-action gate.
- **AG2 WAL/audit trail** je najbliži po audit sloju; potrebno je provjeriti da li se može potpisati i exportovati kao dokaz.
- **E2B** je najbliži po sandboxu; potrebno je uporediti startup latency i cijenu sa GAMA runtime ladder-om pod istim workload-om.
- **OpenClaw/Hermes** su najbliži po distribuciji i broju kanala; potrebno je procijeniti da li su partneri (integracija) ili konkurenti (ako dodaju governance).

---

*Kraj dokumenta. Sljedeća revizija: nakon hands-on testova Airia, LangSmith Sandboxes, E2B i AG2 WAL, te nakon SOC2 gap assessment-a.*
