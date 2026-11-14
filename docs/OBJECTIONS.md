# 10 najčešćih prigovora + odgovori sa dokazom

> Pravilo: svaki odgovor nosi **dokaz** ili eksplicitno „nije mjereno". Ako kupac
> traži broj koji nemamo, kažemo „nemamo" — ne izmišljamo.

---

## 1. „Zašto ne LangSmith?"

**Odgovor:** LangSmith je odličan za **observability i evaluaciju poslije** —
tragovi, promptovi, dataseti. Mi radimo nešto drugo: **gate prije izvršenja**.
LangSmith ne blokira `DELETE` prije nego što stigne do baze i ne izdaje Ed25519
potpisan receipt koji revizor može sam provjeriti.

**Dokaz:** Gate 1 odbija destruktivnu akciju za **2,31 ms p50**, prije izvršenja
(živi test, harness 1.2.2). Gate 3 daje hash-lanac + potpis, provjerljiv na
`/verify.html`. Observability i gate se **dopunjavaju** — ne moraš birati.

---

## 2. „Zašto ne Guardrails AI?"

**Odgovor:** Guardrails validira **izlaz modela** (tekst, format, politike) prije
nego što ga vratiš korisniku. Mi validiramo **akciju** — stvarni poziv alata koji
mijenja sistem — i po potrebi je izolujemo u sandbox. To su različiti slojevi:
Guardrails štiti od lošeg teksta, mi štitimo od loše **mutacije**.

**Dokaz:** Gate 2 sandbox ljestve (runc 110 ns / gVisor 751 ns / Firecracker
54 ns); Gate 3 provjerava da je efekat stvarno nastao (`expected_evidence_spec`,
npr. `sql_rows`). Guardrails to ne radi.

---

## 3. „Nemamo budžet."

**Odgovor:** Počni od **€0**. Community je Apache-2.0, 1 čvor, bez telemetrije —
dovoljno da vidiš ponašanje na svom sistemu. Ako radi, Pro je **€299/čvor/mj**
(godišnje), min. 2 čvora. Jedan pogrešan ulaz robe ili ponuda realno košta više
od toga.

**Dokaz / oznaka:** Community i Pro cijene su fiksne i javne (PRICING.md).
Trošak incidenta **€5.000–€50.000** je **interna pretpostavka, nije mjereno** —
koristimo je kao anchor, ne kao garantovanu uštedu. Startupi imaju −50 % na Pro
12 mjeseci.

---

## 4. „Mi ne koristimo AI agente."

**Odgovor:** Ako imaš skripte, cron, RPA ili SQL automatizaciju, imaš **iste
akcije** — samo ih pokreće drugi izvor. L0 klasifikuje **poziv alata**, ne model.
Gate radi i za determinističke agente i za LLM agente.

**Dokaz:** READ_ONLY_SHELL pravilo propušta `df`, `ls`, `cat`, `git status` kao
READ, a blokira `touch`/mutacije — to je korisno i bez ijednog LLM poziva.

---

## 5. „GDPR — gdje idu naši podaci?"

**Odgovor:** Nigdje. Self-hosted, može i **air-gapped**; licence se provjeravaju
**offline** potpisanim tokenom, bez phone-home. Receipts i logovi ostaju u tvojoj
infrastrukturi. Enterprise ima DPA + listu subprocesora + upitnik sigurnosti.

**Dokaz:** licenca je potpisani offline token (`GAMA-XXXX-…`), provjera lokalna;
nema kill switch-a i nema brisanja podataka kupca. Arhitektura je opisana u
`LICENSE-ENTERPRISE.md`.

---

## 6. „Kako znamo da ne blokirate previše?"

**Odgovor:** Zato što je gate **tiered**, ne binaran: READ prolazi odmah, SEND
traži potvrdu, samo IRREVERSIBLE ide u deny. Možeš prvo pustiti **„posmatraj"
režim** — samo mjeriš koliko bi akcija bilo ask/deny, bez blokiranja ijedne.
Pragovi su konfigurabilni.

**Dokaz:** živi test — READ `df`/`ls` → allow; IRREVERSIBLE → deny/ask. Stopu
lažnih blokada na **tvom** prometu tek treba izmjeriti u pilotu; **nije mjereno**,
i ne tvrdimo da je nula.

---

## 7. „Ovo je samo wrapper oko modela / premalo je."

**Odgovor:** Nije. Iza njega je **396 alata** sa **90,6 % kompresijom šeme**
(213.781 B → 20.076 B po upitu), sandbox ljestve tri nivoa, i kriptografski
receipt lanac. To je infrastruktura, ne prompt.

**Dokaz:** kompresija 90,6 % mjerena po upitu; 294 alata u OpenCode/harness šemi,
harness 1.2.2 na floti od 6 čvorova. Benchmark 20 konkurenata: nijedno javno
rješenje ne kombinuje pre-action L0 + sandbox + Ed25519 receipts.

---

## 8. „Nemamo tim da to održava."

**Odgovor:** Zato je dizajnirano da ne traži telefon kući: offline licenca,
feature flag-ovi, bez obfuskacije i bez kill switch-a. Community → Pro je in-place
upgrade, isti data dir i ista šema baze. Enterprise dobija named inženjera i SLA.

**Dokaz:** upgrade putanja i grace period (30 dana read-only, bez brisanja
podataka) opisani u PRICING.md §5. Podrška: Pro 2 radna dana, Enterprise 24/7.

---

## 9. „EU AI Act se još ne odnosi na nas."

**Odgovor:** Možda ne još — ali evidencija se skuplja **unazad**. Ako je počneš
skupljati tek kad obaveza stupi, prve mjesece nemaš. Mi dajemo mapiranje na
**čl. 12 (logging), 14 (human oversight), 15 (accuracy/robustness), 19
(automatsko logovanje), 26 (obaveze deployera), 72 (post-market monitoring)** i
evidence pack koji skida veći dio prikupljanja.

**Dokaz / granica:** mapiranje i šabloni postoje (Enterprise pack). **Ne
zamjenjujemo pravnika** i ne tvrdimo da garantujemo usklađenost — uklanjamo
60–80 % posla oko prikupljanja dokaza (interna procjena).

---

## 10. „Zašto da vjerujemo vašim brojkama?"

**Odgovor:** Zato što objavljujemo i **ograničenja** i **kako se provjerava**.
Kalibracija ECE 0,297 → 0,035 je rađena na **degenerisanom datasetu** i to piše
uz broj. Receipt možeš sam provjeriti na javnoj stranici — ne moraš vjerovati nama.
I **nemamo izmišljene kupce ni reference**; gdje nema mjerenja, piše „cilj".

**Dokaz:** `https://decision-os.gamai.io/verify.html` — zalijepi receipt JSON ili
SHA-256 hash; hash se računa u browseru, potpis provjerava Ed25519. Lokalno:
`curl …/gtl/verify` ili `gama_dsc.sigil.verify_sigil`. Reproducibilno, bez našeg
posredovanja.

---

## Bonus prigovor: „Šta ako agent ipak pogriješi?"

Receipt lanac rekonstruiše **ko je šta odlučio i zašto** — tier, razlog,
`decision_hash`, `receipt_hash`, i da li je efekat potvrđen. To je razlika između
„ne znamo šta se desilo" i „imamo dokaz za revizora". Za povratne akcije i dalje
vrijedi: gate smanjuje blast radius, ne daje besmrtnost.
