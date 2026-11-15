# GAMA Decision OS

**Kontrola i dokaz za svaku akciju AI agenta — prije nego što se izvrši.**

---

## Problem

AI agenti danas šalju ponude, mijenjaju cijene, knjiže fakture i diraju zalihe u
produkcijskim sistemima. Većina alata ih posmatra **poslije** — loguje trag i
pita se šta je pošlo naopako. Kad agent pogriješi, trošak nije token, nego
pogrešna ponuda, pogrešan ulaz robe i izgubljeno povjerenje kupca.

Uz to, EU AI Act traži dokazivu evidenciju i ljudski nadzor (čl. 12, 14, 15,
19, 26, 72) — a „imamo logove" rijetko prolazi reviziju.

---

## Rješenje — 3 Gate-a na svakoj akciji

| Gate | Šta radi | Dokaz (mjereno) |
|---|---|---|
| **Gate 1 — L0 odluka** | Klasifikuje svaku akciju prije izvršenja: READ / DRAFT / SEND / IRREVERSIBLE → allow / ask / deny | **2,31 ms p50** |
| **Gate 2 — Sandbox ljestve** | Izolovano izvršavanje prema riziku | runc **110 ns** · gVisor **751 ns** · Firecracker **54 ns** · snapshot restore **2,28 ms** |
| **Gate 3 — Dokaz** | Ed25519 potpisani receipts + SHA-256 hash-lanac | Svaki receipt se javno provjerava |

Agent ne može „samo odraditi" destruktivnu akciju. Ona se klasifikuje, po potrebi
izoluje, i na kraju ostavlja kriptografski dokaz ko je šta odlučio i zašto.

---

## Dokaz da radi

- **398 alata** u sistemu; **kompresija šeme 90,6 %** (213.781 B → 20.076 B po
  upitu) — cijeli alatni set staje u kontekst bez sečenja.
- **Kalibracija:** ECE **0,297 → 0,035** (T = 0,2), rangiranje **1,000** na
  held-out **1.200** uzoraka. *Ograničenje: dataset je degenerisan, fit je na
  granici — navedeno namjerno.*
- **RLDF DPO:** train_loss **0,10052**, 600 near-miss parova (300 teških + 300
  kontrole).
- **Flota 6 čvorova**, harness **1.2.2**, **296 alata u runtime promptu / 398 u katalogu** u OpenCode/harness šemi.
- **Benchmark 20 konkurenata:** nijedno javno rješenje ne kombinuje pre-action
  L0 + sandbox ljestve + Ed25519 receipts.

---

## Cijena

| Paket | Cijena | Za koga |
|---|---|---|
| **Community** | **€0** (Apache-2.0) | prvi prototip, 1 čvor, bez telemetrije |
| **Pro** | **€299**/čvor/mj godišnje (€349 mjesečno), min. 2 čvora | timovi koji puštaju agente na žive sisteme |
| **Enterprise** | od **€24.000**/god (do 10 čvorova) + **€7.500** onboarding | banke, osiguranja, ERP distributeri, javni sektor |

Cijena je po čvoru, ne po korisniku — jer se rizik i dokaz mjere po mašini koja
izvršava akcije. Bez mjerenja potrošnje po pozivu i bez iznenađenja na računu.

---

## CTA

**Zakaži 10-minutni demo** i vidi kako destruktivna komanda biva blokirana, a
benigna prođe — na živom sistemu, sa receiptom koji sam provjeriš.

→ https://decision-os.gamai.io · Javni verifikator: https://decision-os.gamai.io/verify.html

---

<sub>Svi brojevi su iz internih testova i ponovljivi su; gdje nešto nije mjereno,
piše „cilj" ili „nije mjereno". Nemamo izmišljene kupce ni reference. Ograničenja
(kalibracija na degenerisanom setu) objavljujemo zajedno sa rezultatom.</sub>
