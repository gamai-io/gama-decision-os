# Outbound email sekvenca — 4 emaila (bosanski)

> Pravila: kratko, bez žargona, jedan CTA po emailu. **Nijedna izmišljena brojka,
> kupac ni referenca.** Gdje nema mjerenja, piše „cilj" ili se ne navodi.
> Pošiljalac potpisuje svojim imenom; zamijeni `[Ime]`, `[Firma]`, `[link]`.

---

## Email 1 — Prvi kontakt (Dan 0)

**Subject:** Vaš AI agent mijenja sistem. Ko ga zaustavlja prije izvršenja?

Zdravo [Ime],

vidim da [Firma] koristi automatizaciju nad ERP-om. Praktično pitanje: kad agent
pošalje ponudu ili proknjiži ulaz robe — šta se desi **prije** nego što akcija
stigne u bazu?

Većina timova ima logove **poslije**. Mi smo napravili gate **prije**: svaka
akcija se klasifikuje za ~2 ms (READ / DRAFT / SEND / IRREVERSIBLE), destruktivna
se blokira, mutacija čeka čovjeka, a na kraju ostaje Ed25519 potpisan receipt
koji revizor može sam provjeriti.

Nije prezentacija — 10 minuta na živom sistemu: pokažem blokiran `DELETE`, propušten
`SELECT`, i dam vam receipt da ga sami provjerite.

Da probamo u četvrtak ili petak?

[Ime]
[link]

---

## Email 2 — Follow-up sa benchmarkom (Dan 3)

**Subject:** 90,6 % kompresije šeme — zašto to znači da gate može biti brz

Zdravo [Ime],

kratko, bez ponavljanja prvog mejla. Tri mjerena broja iz internih testova:

- **398 alata**, kompresija šeme **90,6 %** (213.781 B → 20.076 B po upitu) —
  cijeli alatni set staje u kontekst.
- **L0 odluka 2,31 ms p50** — gate prije izvršenja, ne poslije.
- **Kalibracija ECE 0,297 → 0,035** (T = 0,2), rangiranje 1,000 na 1.200
  held-out uzoraka.

Ograničenje odmah: kalibracija je rađena na **degenerisanom datasetu** i fit je
na granici — zato to pišemo uz broj, a ne krijemo.

Benchmark 20 konkurenata: nijedno javno rješenje ne kombinuje pre-action L0 +
sandbox ljestve + Ed25519 receipts.

Ako želite, pošaljem jedan ovakav izvještaj za vaš scenario. 10 minuta, [link].

[Ime]

---

## Email 3 — Follow-up sa case study (Dan 7)

**Subject:** ERP + PDV 17 %: šta gate stvarno blokira (i šta je ilustracija)

Zdravo [Ime],

napisao sam kratak case study za ERP distributera (tabela `customers`, PDV 17 %).
Namjerno je podijeljen na **mjereno** i **ilustraciju**:

**Mjereno (interni test):** `DELETE` i „cijena na 0" → deny prije baze;
`SELECT`/`df` → allow; L0 2,31 ms p50; receipt provjerljiv na javnoj stranici.

**Ilustracija (nije mjereno):** novčana ušteda za konkretnu firmu — **nemamo
stvarnog kupca**, pa ne izmišljamo broj. Poslovni efekat tek treba izmjeriti u
pilotu.

To je cijela poenta: možete vjerovati onome što je reproducibilno, a ne onome što
zvuči dobro. Case study: [link].

Da vam pošaljem i jednosmerni brief za vaš tim?

[Ime]

---

## Email 4 — Break-up (Dan 14)

**Subject:** Zatvaram temu — da ostavim vrata otvorena?

Zdravo [Ime],

neću više da vam punim inbox. Pretpostavljam da sad nije prioritet — i to je
legitimno.

Ostavljam dvije stvari bez obaveze:

1. **Community je €0** (Apache-2.0, 1 čvor, bez telemetrije) — možete pustiti L0
   u „posmatraj" režimu i vidjeti koliko bi akcija bilo ask/deny, bez blokiranja
   ijedne.
2. **Javni verifikator**: [link]/verify.html — zalijepite receipt i provjerite
   sami, bez nas.

Ako se vratite na temu za mjesec-dva, samo odgovorite na ovaj mejl. Srećno sa
projektom.

[Ime]
