# Case study — ERP distributer, PDV 17 %, tabela `customers`

> **Pošteno označeno:** ovaj dokument miješa **stvarno mjerenja** (interni testovi
> GAMA Decision OS) i **ilustrativni scenario** (izmišljen distributer, ne stvarni
> kupac). Svaki red u tabeli nosi oznaku **MJERENO** ili **ILUSTRACIJA**.
> Nigdje nema stvarnog kupca, imena firme ni reference.

---

## Kontekst scenarija (ILUSTRACIJA)

Zamisli distributera koji radi na ERP-u sa bazom `erp_prod`, tabelom kupaca
**`customers`** (ne `kupci`), i PDV stopom **17 %**. Agent dobija zadatke u prirodnom
jeziku:

- „pošalji ponudu kupcu X za 20 pumpi"
- „proknjiži ulaz robe iz fakture dobavljača Y"
- „ispravi cijenu artikla Z na 0"
- „pokaži stanje artikla Z"
- „obriši red iz `customers` gdje je šifra 123"

Bez gate-a, agent ima iste privilegije kao iskusni operater — ali bez umora,
konteksta i odgovornosti. Jedna pogrešna ponuda ili jedan pogrešan ulaz robe je
realan trošak.

---

## Kako GAMA Decision OS prolazi kroz isti tok

| # | Akcija agenta | Gate 1 odluka | Šta se dalje dešava | Oznaka |
|---|---|---|---|---|
| 1 | „pokaži stanje artikla Z" (`SELECT` nad `customers`/zalihom) | **READ → allow** | Izvršava se odmah | MJERENO (L0) + ILUSTRACIJA (upit) |
| 2 | „pošalji ponudu kupcu X" (email / mutacija) | **SEND → ask** | Traži se ljudska potvrda prije slanja | MJERENO (L0) + ILUSTRACIJA (tok) |
| 3 | „ispravi cijenu na 0" | **IRREVERSIBLE → ask/deny** | Blokirano ili eskalirano; nema tihog izvršenja | MJERENO (L0) + ILUSTRACIJA (tok) |
| 4 | „obriši red iz `customers`" | **IRREVERSIBLE → deny** | Gate 1 odbija prije baze; nema `DELETE` | MJERENO (L0) + ILUSTRACIJA (upit) |
| 5 | „proknjiži ulaz robe" | **DRAFT/SEND** | Izvršava se u sandboxu; Gate 3 provjerava da su redovi stvarno upisani | MJERENO (sandbox + Evidence Gate) + ILUSTRACIJA (poslovni tok) |

**Ključna razlika:** odluka se donosi **prije** izvršenja. `DELETE` i „cijena na 0"
nikad ne stignu do baze; ponuda ne ode bez čovjeka; benigni `SELECT` prolazi bez
trenja.

---

## Dokazi koji su stvarno izmjereni (interni test)

| Stavka | Rezultat | Kako je provjereno |
|---|---|---|
| L0 latencija odluke | **2,31 ms p50** | interni benchmark, ponovljiv |
| Gate 2 izolacija | runc **110 ns** · gVisor **751 ns** · Firecracker **54 ns** | interni TSR benchmark |
| Snapshot restore | **2,28 ms** | Firecracker mikro-VM, interni test |
| Kompresija šeme alata | **90,6 %** (213.781 B → 20.076 B po upitu) | mjereno na 396 alata |
| Kalibracija | ECE **0,297 → 0,035** (T = 0,2), rangiranje **1,000** na held-out **1.200** | realni ECE eval |
| RLDF DPO | train_loss **0,10052**, 600 near-miss parova | LUMI trening, završen 0:0 |
| Receipt lanac | Ed25519 potpis + SHA-256 hash-lanac, javna provjera | `verify.html`, `/gtl/verify` |
| Destruktivna komanda | `rm -rf` i `DELETE` → **deny** na Gate 1 | živi test, harness 1.2.2 |

**Ograničenje koje objavljujemo:** kalibracija je rađena na **degenerisanom
datasetu** gdje je tačnost 1,0, pa fit sjedi na granici. Zato je T = 0,2, a ne
agresivniji T. Ovo je stvarno ograničenje, ne marketinška sitnica — i zato ga
navodimo uz broj.

---

## Šta je ilustracija, a šta nije

**Nije mjereno (ilustracija):**

- Novčana ušteda za konkretnog distributera — **nemamo stvarnog kupca**.
- Vrijeme implementacije u konkretni ERP (erp_prod, SAP, Odoo) — zavisi od okruženja.
- Stopa lažnih blokada u produkciji na realnom prometu — **nije mjereno**; demo
  pokazuje ponašanje na kontrolisanim primjerima.
- „Sprečeno X incidenata godišnje" — **ne tvrdimo**.

**Jeste mjereno (interni test):** L0 latencija, sandbox ljestve, snapshot restore,
kompresija šeme, ECE/Brier/rangiranje, RLDF train_loss, blokada destruktivnih
komandi i provjera receipta.

**Interna pretpostavka (nije mjereno):** u PRICING dokumentu stoji da tipičan
incident izazvan neverifikovanom akcijom agenta košta **€5.000–€50.000** u
ispravkama i povjerenju. To je **pretpostavka za pozicioniranje**, ne izmjereni
podatak — tako je i označeno.

---

## Kako bi pilot izgledao (predlog, nije obećanje)

1. **Community, 1 čvor, read-only** — nedjelja 1: pustiti L0 u „posmatraj" režimu,
   mjeriti koliko akcija bi bilo ask/deny.
2. **Pro, 2 čvora** — nedjelje 2–4: uključiti ask za SEND, deny za IRREVERSIBLE,
   uvesti receipts u internu reviziju.
3. **Enterprise** — tek ako treba air-gapped, SSO/SCIM, EU AI Act evidence pack i
   ERP konektori.

Pilot ima jasne izlazne kriterije: broj blokiranih destruktivnih akcija, broj
lažnih blokada, i vrijeme provjere jednog receipta. Te brojeve tek treba izmjeriti
na kupcu — do tada su **cilj**, ne rezultat.

---

## Zvanična granica tvrdnje

> GAMA Decision OS dokazano, u internim testovima, klasifikuje akcije za ~2,3 ms,
> izoluje izvršavanje po riziku i izdaje kriptografski provjerljive receipts.
> Poslovni efekat na konkretnom ERP-u **tek treba izmjeriti u pilotu**.

To je cijela tvrdnja. Ništa više, ništa manje.

---

→ Demo: https://decision-os.gamai.io · Verifikator: https://decision-os.gamai.io/verify.html
