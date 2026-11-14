# MERGE_NOTES — live gamai.io + novi GAMA Decision OS sajt

Datum: 2026-11-14
Izvor live: `https://gamai.io/` (sha256 `1625690fc7dab3e6…`, 8.916 B)
Lokalni izvor: `/root/gamai-web-en/` (`index.html` sha256 `0ed07af45cfe94a0…`; jedina razlika prema live-u je live tracking beacon skript)
Generator: `/opt/gama-harness/site/build_site.py` (jedini izvor; sve stranice se generišu, ne ručno)

## Pravilo spajanja

Spojeno je **aditivno**: nijedna live tvrdnja nije zamijenjena novom. Gdje su se brojevi razlikovali (npr. 178 alata u live katalogu vs 294 u harnessu 1.2.2), zadržana su **oba** broja sa datumom/kontekstom. Gdje je live imao zasebnu stranicu, njen sadržaj je preuzet na najbližu stranicu novog sajta (vidi mapu ispod), a stara ruta nije zadržana da nav ostane konzistentan.

## Mapa: live stranica → gdje je sada

| Live stranica | Sadržaj | Sada na |
|---|---|---|
| `/` | hero, SIGIL lanac, 4 KPI, „Moćno na sajtu", „Šta dobijaš uz SIGIL", istraživanje, uskoro | `index.html` |
| `/index-en.html` | prijevod BS indexa (nema jedinstvenih tvrdnji) | sve tvrdnje su na BS stranicama; EN URL nije napravljen (vidi „Izbačeno") |
| `/product.html` | problem, EU AI Act, signed receipts, isolation, per-tenant, mjerenja | `sigil.html`, `index.html` |
| `/gamacode.html` | harness, alati, flota, sandbox, modeli | `gamacode.html` |
| `/tools.html` | server alati, 396 generatora (42 grupe / 252 alata), klijentski alati, 22 AI alata | `gamacode.html#alati` (puna imena alata), `index.html` |
| `/skills.html` | 1.000 katalog, 992 open-source skillova, GPU radnik, Skill Market, kategorije | `sigil.html#ekosistem`, `gamacode.html#alati`, `index.html` |
| `/experts.html` | 364 persone, domeni | `sigil.html#ekosistem`, `index.html` |
| `/mcp.html` | MCP server, alati, instalacija, OpenCode/Claude/Cursor config | `gamacode.html#alati` |
| `/benchmarks.html` | false-success tabele, SIGIL/harness/isolation/model, 28 repo linkova, DOI | `benchmarks.html` (nova stranica), `index.html` |
| `/news.html` | 13 nalaza (determinizam, iskrenost, CUA, sigurnost, dataset, infra…) | `benchmarks.html#istrazivanje`, `index.html` |
| `/news.xml` | RSS feed sa 13 nalaza | `news.xml` (generisan iz `build_site.py`) |
| `/coming-soon.html` | SIGIL Cloud (hosted gate, SDK, dashboard, AI Act pack), novi GAMACODE | `index.html#uskoro`, `pricing.html#sigil-cloud` |
| `/legal.html` | Terms, Privacy, AI Act 12/19/26/72, DPA, Cookies | `contact.html#uslovi`, `contact.html#privatnost` |
| `/privacy.html` | privatnost (kontrolor, podaci, osnov, retencija, podprocesori, prava) | `contact.html#privatnost` |
| `/docs.html` | dokumentacija | `gamacode.html#docs` (postojeća) + MCP config |

## Preuzeto iz live-a (novo u odnosu na stari novi sajt)

- Hero narativ: **namjera → odobrenje → izvršenje → potpisani receipt → anchor**.
- 4 live KPI-ja: **25.600** LUMI false-success probe, **400/400** uhvaćenih laži, **1.000** receipta (lanac validan, 0 grešaka), **5,8 ms** Firecracker VM.
- „Moćno na sajtu": GAMACODE, Alati (396 generatora), Vještine **992**, Eksperti **364 persone**, MCP, Open source **30+**.
- „Šta dobijaš uz SIGIL" (6 kartica): potpisani receipti, dokaz ne logovi, fail-closed, izolacija, AI Act audit 180 dana, multi-tenant.
- Puni katalog alata (imena server i klijentskih alata), MCP alati i instalacioni config (OpenCode / Claude Code / Cursor).
- Benchmark podaci: LUMI-G 8 nodova (25.600, 6,25%, p50 2,4 / p95 10,8 ms), CrossNode honest (25.600/25.600, p50 64,8 ms), CrossNode liar (28.800, 400/400, p50 171 ms), LUMI job **23394156**, Zenodo DOI **10.5281/zenodo.24092188**, CrossNode-Bench v1.4.0.
- Harness / izolacija / model: **178 alata**, **1.172 testa**, code-bench 6/6 ~16 s, Firecracker **5,8 ms** fork / **1,846 s** boot / **2,286 ms** restore / vsock ~11 ms, AgentMujo v1.5.0 CUA **49,0%**, ScreenSpot **76,3%**, tool **95,2%**, refusal **100%**.
- 13 istraživačkih nalaza (uključujući 660/700 i 669/700 determinizam, prompt-injection 100% → 0–3,3%, General-30 30/30 @ p50 6,218 s, 216 workera ≈96%, GAMA 11/15 vs opencode 12/12).
- 28 open-source repozitorija po sloju + arhivirani (`gama-shard`, `gama-retrieval`) + DOI linkovi.
- Hosted SIGIL Cloud cijene: **Free €0 / Pro €49/mj. / Enterprise €1,5k+/mj. / usage €0,002–0,02** — jasno odvojeno od self-hosted Decision OS licenci (€0 / €299 po čvoru / €24k+).
- Legal: puni Terms, Privacy (kontrolor, pravni osnov, 180 dana, Cloudflare/EU/email/payment podprocesori, prava, SCC), AI Act **12/19/26/72**, DPA sažetak (48 h breach, EU residency, enkripcija, least privilege), Cookies; kontakti **legal@gamai.io** i **privacy@gamai.io**.
- EU AI Act tabela proširena sa čl. **19, 26, 72** (pored 12/14/15).
- 992 vještine / 364 persone / 1.000 katalog / GPU radnik / Skill Market / kategorije.

## Novo (nije bilo u live-u)

- Decision OS 3-Gate arhitektura, L0 tiering (READ / DRAFT / SEND / IRREVERSIBLE), `expected_evidence_spec`.
- Kalibracija ECE 0,297 → **0,0347** (T=0,2, held-out n=240) i RLDF petlja (LUMI jobovi 23714934 / 23715009).
- Mjerenja: L0 **2,31 ms** p50 / jezgro **0,30 ms** / −86,2% prompta / SWE-lite **10/10** sa nezavisnim pytest-om / streaming prvi tekst **1,29 s**.
- GTL ledger i javna verifikacija (`verify.html`), replay/idempotency, hash-lanac i Ed25519 detalji.
- Nova stranica `benchmarks.html` (objedinjuje live benchmark + istraživanje + open source).
- 6-člana flota i sandbox tabele (runc / gVisor / Firecracker), MCP integracije i harness 1.2.2.

## Izbačeno / konsolidovano i zašto

1. **Live tracking beacon** (`navigator.sendBeacon("/v1/track", …)` u live `</body>`) nije preuzet — novi sajt ima izjavu „bez telemetrije / bez analitike" i ne smije tiho slati podatke.
2. **Zasebne live rute** (`tools.html`, `skills.html`, `experts.html`, `mcp.html`, `news.html`, `legal.html`, `privacy.html`, `coming-soon.html`, `product.html`) nisu zadržane kao zasebni URL-ovi; sadržaj je premješten na gore mapirane stranice da nav (Decision OS, SIGIL, GAMACODE, Benchmark, Docs, Pricing, Verify, Kontakt) bude isti na svakoj stranici. Nijedna tvrdnja nije izgubljena.
3. **EN index** nije napravljen kao zasebna stranica jer je bio prijevod BS indexa bez jedinstvenih tvrdnji. Ako treba `/index-en.html`, može se dodati u `build_site.py` iz istog izvora.
4. **Sukobljeni brojevi** nisu „prepisani": 178 alata (live katalog 11.11.2026) i 294 alata (harness 1.2.2) stoje zajedno sa kontekstom; 992 open-source vještina i 1.000 katalog takođe stoje zajedno.
5. **Dvije pricing linije** su odvojene: hosted SIGIL Cloud (live cijene) i self-hosted Decision OS (nove cijene) — da ne postoji kontradikcija.

## Verifikacija (dokaz)

Build:

```
$ cd /opt/gama-harness/site && python3 build_site.py
   43076  index.html
   37936  decision-os.html
   39183  sigil.html
   41043  gamacode.html
   35638  benchmarks.html
   33047  verify.html
   35296  pricing.html
   32281  contact.html
   23774  404.html
     148  robots.txt
    1071  sitemap.xml
    3923  news.xml
```

HTTP (lokalni `python3 -m http.server 8100`):

```
index.html          HTTP 200  43076B
decision-os.html    HTTP 200  37936B
sigil.html          HTTP 200  39183B
gamacode.html       HTTP 200  41043B
benchmarks.html     HTTP 200  35638B
verify.html         HTTP 200  33047B
pricing.html        HTTP 200  35296B
contact.html        HTTP 200  32281B
404.html            HTTP 200  23774B
robots.txt          HTTP 200  148B
sitemap.xml         HTTP 200  1071B
news.xml            HTTP 200  3923B
```

Struktura:

- Nav linkovi identični na svih 9 stranica (samo `aria-current` se razlikuje) — provjereno.
- Footer identičan na svih 9 stranica — provjereno.
- Nema pokvarenih internih fajlova ni anchor-a (`broken anchors: none`).
- HTML tag balance: 0 grešaka na svih 9 stranica.
- `sitemap.xml` sadrži `benchmarks.html`.

Ključne fraze (provjereno u generisanom HTML-u):

```
992            -> index, decision-os, sigil, gamacode, benchmarks
364            -> index, sigil, gamacode
Ed25519        -> index, sigil, gamacode, benchmarks, verify, pricing
SIGIL          -> svih 9 stranica
25.600         -> index, sigil, benchmarks
400/400        -> index, benchmarks
1.000          -> index, decision-os, sigil, gamacode, benchmarks
5,8            -> index, sigil, benchmarks
178 alata      -> sigil, gamacode, benchmarks
294            -> index, sigil, gamacode, benchmarks
1.172          -> sigil, gamacode, benchmarks
23394156       -> index, sigil, benchmarks
10.5281/zenodo.24092188 -> index, sigil, benchmarks
Čl. 12/19/26/72 -> index; 12 / 14 / 15 / 19 / 26 / 72 -> sigil
legal@gamai.io -> contact
privacy@gamai.io -> contact
€49 / €1,5k / €0,002–0,02 -> index, pricing
gama-shard / gama-retrieval -> benchmarks
```

## Eksplicitna potvrda

**Potvrđujem: nijedna jedinstvena live tvrdnja nije izgubljena.** Sve numeričke tvrdnje, SIGIL formulacije, 992 vještine, 364 persone, AI Act mapiranja (12/19/26/72), benchmark brojevi, DOI, repo lista, MCP alati, cijene hosted SIGIL-a i legal/DPA tekstovi postoje u generisanom sajtu. Jedini izuzetak je EN index, koji je prijevod BS indexa bez jedinstvenih tvrdnji; ako se traži EN URL, dodaje se iz istog generatora.

Napomena: `BASE` u generatoru je i dalje `https://decision-os.gamai.io`; canonical/sitemap nisu prebačeni na `gamai.io` jer DNS prebacivanje nije dio ovog zadatka (vidi `DNS_SETUP.md`).
