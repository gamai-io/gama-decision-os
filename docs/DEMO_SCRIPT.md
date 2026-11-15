# Demo — 10 minuta, korak po korak

> Cilj: kupac za 10 minuta **vidi** tri stvari — destruktivna akcija blokirana,
> benigna prošla, i receipt koji sam provjeri. Bez slajdova dok se nešto ne
> dogodi na ekranu.

**Prije demoa (checklist, 2 min):**
- [ ] Harness **1.2.2** radi (`gama --json doctor` ili `/health`).
- [ ] Otvoren `https://decision-os.gamai.io/verify.html` u drugom tabu.
- [ ] Pripremljen jedan `receipt.json` (iz prethodnog testa) za lijepljenje.
- [ ] Terminal sa vidljivim fontom; nijedan tajni ključ na ekranu.
- [ ] Unaprijed znaš **koji** je tier za svaku komandu (tabela ispod).

---

## 0:00–0:30 — Hook (jedna rečenica)

> „Pustićemo agenta da dira živi sistem. Prvo destruktivnu komandu — vidjećete da
> ne prolazi. Onda benignu — vidjećete da prolazi. Na kraju ćete sami provjeriti
> dokaz. Bez vjerovanja meni."

---

## 0:30–2:00 — Problem (30 s) + šta gledamo (30 s)

- Agent danas ima privilegije operatera, ali bez umora i odgovornosti.
- Većina alata loguje **poslije**; mi odlučujemo **prije**.
- Tri gate-a: **L0 odluka (~2 ms) → sandbox (ako treba) → Ed25519 receipt**.

Ne pričaj duže. Prelazi na ekran.

---

## 2:00–3:30 — Gate 1: destruktivna komanda blokirana

U terminalu (kroz harness/gate, ne zaobilazeći ga):

```
rm -rf /tmp/gama-demo-podaci
```

**Očekivano:** tier **IRREVERSIBLE** → **deny** (ili ask, zavisno od politike).
Na ekranu se vidi odluka i razlog; komanda **nije** izvršena.

Zatim SQL varijanta (ilustracija na `customers`):

```
DELETE FROM customers WHERE sifra = 123
```

**Očekivano:** **IRREVERSIBLE → deny**. Baza netaknuta.

> Reci: „Ovo se desilo za ~2 ms, prije nego što je ijedan bajt otišao u bazu."

---

## 3:30–5:00 — Benigna komanda prolazi

```
df -h
```

**Očekivano:** **READ → allow**. Izlaz se pojavi odmah.

```
SELECT TOP 5 sifra, naziv FROM customers
```

**Očekivano:** **READ → allow**. Upit prođe.

Zatim **SEND** primjer (bez stvarnog slanja!):

> „Pošalji ponudu kupcu X." → **SEND → ask**. Pojavi se zahtjev za ljudsku
> potvrdu. **Ne klikći „pošalji"** — demo ne smije poslati mejl. Pokaži da je
> zaustavljeno na čovjeku.

> Reci: „Benigno prolazi bez trenja. Mutacija čeka čovjeka. Destruktivno ne
> prolazi. To je cijela poenta."

---

## 5:00–6:30 — Gate 3: verify stranica (kupac provjerava sam)

1. Prebaci na tab `verify.html`.
2. Zalijepi `receipt.json` (ili 64-hex `receipt_hash`).
3. Klikni provjeri.

**Očekivano:** **„Potvrđeno"** — receipt postoji u ledgeru, hash se poklapa, potpis
je valjan (ako je javni ključ postavljen). Ako nešto ne valja: **„Nije potvrđeno"**
sa razlogom (hash ne postoji / lanac prekinut).

Pokaži i lokalnu provjeru (jedna linija):

```
curl -sS http://127.0.0.1:7125/gtl/verify -d '{"id":"<receipt_id>"}'
```

> Reci: „Hash se računa u vašem browseru. Privatni ključ nikad ne napušta našu
> infrastrukturu. Ne morate vjerovati nama — provjerite sami."

---

## 6:30–8:00 — Skala i kalibracija (dva broja, pa ograničenje)

- **398 alata**, kompresija šeme **90,6 %** (213.781 B → 20.076 B po upitu).
- **Kalibracija:** ECE **0,297 → 0,035** (T = 0,2), rangiranje **1,000** na
  held-out **1.200**.
- **Odmah dodaj ograničenje:** „Dataset je degenerisan, fit je na granici — zato
  T = 0,2 i zato ovo pišemo uz broj."

- **Benchmark:** 20 konkurenata; nijedno javno rješenje ne kombinuje pre-action
  L0 + sandbox ljestve + Ed25519 receipts.

> Ako kupac pita za sandbox: runc **110 ns** / gVisor **751 ns** / Firecracker
> **54 ns**, snapshot restore **2,28 ms** (interni test).

---

## 8:00–9:30 — Cijena (bez izvinjenja)

| Paket | Cijena |
|---|---|
| Community | **€0**, Apache-2.0, 1 čvor |
| Pro | **€299**/čvor/mj godišnje (€349 mjesečno), min. 2 čvora |
| Enterprise | od **€24.000**/god (10 čvorova) + **€7.500** onboarding |

> Reci: „Cijena je po čvoru, ne po korisniku. Bez mjerenja po pozivu. Pogrešan
> ulaz robe košta više od Pro čvora — ali tu uštedu **tek treba izmjeriti u
> pilotu**; neću vam je izmišljati."

---

## 9:30–10:00 — CTA (jedan konkretan korak)

> „Predlažem Community na jednom čvoru, read-only, nedjelju dana. Mjerimo koliko
> bi akcija bilo ask/deny — bez blokiranja ijedne. Ako brojevi imaju smisla,
> prelazimo na Pro. Dogovorimo termin?"

Zatvori sa: **https://decision-os.gamai.io** i **/verify.html**.

---

## Ako nešto pukne (fallback, bez panike)

- Gate ne odgovara → pokaži prethodno snimljeni `receipt.json` na `verify.html`
  (dokaz ostaje isti).
- Nema baze → `df -h` i `rm -rf` primjer rade bez baze.
- Nema interneta → sve osim verify stranice radi lokalno; verify pokaži iz
  lokalnog `curl …/gtl/verify`.

**Nikad** ne tvrdi da je nešto prošlo ako nisi vidio izlaz. Ako nije radilo, reci:
„ovo nije prošlo, evo gdje je stalo."
