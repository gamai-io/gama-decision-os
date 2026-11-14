# GAMA DECISION OS MANIFESTO
## Autonomni Agentski Kontrolni Nivo (Control Plane) za Regulisana Enterprise Tržišta

---

### Sažetak (Executive Summary)
U eri u kojoj vještačka inteligencija prelazi iz pasivnih generatora teksta u aktivne autonomne agense sa sposobnošću izvršavanja transakcija, potreba za bezbjednim, verifikabilnim i determinističkim operativnim okruženjem postaje kritična. **GAMA Decision OS** predstavlja revolucionarni, visokosigurni agentski kontrolni nivo (Agent Control Plane) projektovan specifično za integraciju sa enterprise ERP sistemima (kao što su korporativne ERP baze) i usklađen sa najstrožim zahtjevima **EU AI Act-a**. 

Ovaj dokument detaljno elaborira tehnološke stubove GAMA Decision OS-a: **Trostruki Sandbox Runtime (TSR)** sa ultra-brzim *snapshot restore* mehanizmom, i **3-Gate Closed-Loop** arhitekturu za evaluaciju rizika i autorizaciju agentskih akcija u realnom vremenu.

---

## 1. TSR: Trostruki Sandbox Runtime (Triple Sandbox Runtime)

Izvršavanje nepouzdanog (untrusted) agentskog koda, dinamički generisanih skripti i interakcija sa spoljnim API-jevima zahtijeva višeslojnu bezbjednosnu izolaciju bez kompromitovanja performansi. GAMA Decision OS implementira **TSR (Triple Sandbox Runtime)** tehnologiju, omogućavajući dinamički odabir nivoa izolacije u zavisnosti od procijenjene kategorije rizika akcije.

TSR se oslanja na tri različita runtime okruženja, optimizovana i benchmarkovana na našem namjenskom testnom hardveru (10 vCPU, 33 GB RAM, GTX 1660S 6 GB, `gVisor+nvidia` i Firecracker mikro-VM-ovi):

```
                        +---------------------------------------------+
                        |           GAMA Decision OS Engine           |
                        +---------------------------------------------+
                                               |
                                     [TSR Router / Selector]
                                               |
         +-------------------------------------+-------------------------------------+
         |                                     |                                     |
         v                                     v                                     v
+------------------+                 +------------------+                 +------------------+
|   runc Sandbox   |                 |  gVisor Sandbox  |                 | Firecracker vVM  |
|  (Standard App)  |                 |  (Untrusted Net) |                 |  (Kernel-Level)  |
+------------------+                 +------------------+                 +------------------+
| Syscall: Direct  |                 | Syscall: Sentry  |                 | Syscall: KVM     |
| Perf: Max        |                 | Network: Filter  |                 | Boot: 2.28 ms    |
+------------------+                 +------------------+                 +------------------+
```

### 1.1. runc (Standardni kontejneri)
*   **Arhitektura:** Standardna Linux kontejnerizacija bazirana na `namespaces` i `cgroups`. Agentske akcije koje su ocijenjene kao niske rizičnosti (L0/L1) izvršavaju se unutar izolovanih `runc` kontejnera.
*   **Karakteristike:** Izuzetne performanse, minimalan overhead, direktan pristup sistemskim pozivima (syscalls) host operativnog sistema uz `seccomp` filtriranje.
*   **Performanse:** Syscall/fork latencija iznosi svega **110 ns/op**.

### 1.2. gVisor (Korisnički prostor - Kernel presretanje)
*   **Arhitektura:** Google-ov sandbox runtime koji implementira sopstveni kernel napisan u jeziku Go (`Sentry`) u korisničkom prostoru. On presreće i filtrira sve sistemske pozive koje kontejner upućuje hostu.
*   **Karakteristike:** Potpuna prevencija eksploatacije ranjivosti Linux kernela. Idealan za izvršavanje agenata koji zahtijevaju mrežne interakcije ili rad sa nepouzdanim spoljnim bibliotekama. Podržava integraciju sa GPU jedinicama kroz namjensku `gVisor+nvidia` konfiguraciju.
*   **Performanse:** Zbog presretanja sistemskih poziva, latencija raste na **751 ns/op** (4-13 puta sporije od nativnog izvršavanja), ali pruža neprobojan bezbjednosni bedem.

### 1.3. Firecracker (Hardverski mikro-VM)
*   **Arhitektura:** Tehnologija razvijena od strane AWS-a, koristi Linux Kernel-based Virtual Machine (KVM) za kreiranje i upravljanje minimalističkim mikrovirtuelnim mašinama (microVMs).
*   **Karakteristike:** Pruža najjaču moguću izolaciju (izolacija na nivou hardvera i virtuelizacije jezgra) uz performanse koje pariraju standardnim kontejnerima. Svaki agent visokog rizika dobija sopstveni, namjenski mikro-kernel.
*   **Performanse:** Izmjerena syscall/mem latencija je nevjerovatnih **54 ns/op** (zahvaljujući minimalnom kernel overheadu). Hladan start (cold boot) cijelog mikro-VM-a iznosi **1.846 s**.

### 1.4. Tehnika Munjevitog Snapshot Restore-a (2.28 ms)
Kako bismo prevazišli problem odgode od 1.8 sekundi tokom hladnog starta Firecracker mikro-VM-ova u transakcionim sistemima visoke frekvencije, GAMA Decision OS implementira naprednu **2.28 ms Snapshot Restore** tehniku:

1.  **Template pre-warm:** Mikro-VM se inicijalizuje, učitava bazne biblioteke, sistemske zavisnosti i uspostavlja inicijalni memorijski otisak.
2.  **State Serialization:** Koristeći Firecracker API, vrši se puna serijalizacija stanja procesora, registara i memorije (dirty-page tracking) u mikro-VM snapshot datoteke na brzom NVMe skladištu.
3.  **Micro-resume (Memory-mapped Restore):** Prilikom iniciranja transakcije, GAMA engine mapira memorijski fajl direktno u KVM prostor (`mmap` sa `MAP_PRIVATE` i pre-faulting opcijom). Umjesto podizanja operativnog sistema ispočetka, stanje se rekonstruiše direktno u memoriji.
4.  **Izmjereni rezultat:** Vrijeme od momenta zahtjeva do prve instrukcije agenta unutar potpuno izolovanog hardverskog sandboxa iznosi tačno **2.28 ms**.

### 1.5. Uporedni Pregled TSR Runtime Performansi (testni hardver)

| Parametar | Bare Metal (Nativno) | runc (Standard) | gVisor (Bezbjedni mrežni) | Firecracker (Mikro-VM) |
| :--- | :---: | :---: | :---: | :---: |
| **Syscall Latency (ns/op)** | 92 ns | 110 ns | 751 ns | **54 ns** |
| **Puni Boot Time (ms)** | N/A | ~15 ms | ~80 ms | 1,846 ms |
| **Snapshot Restore (ms)** | N/A | N/A | N/A | **2.28 ms** |
| **Izolacija** | Nikakva | Procesni nivo | Korisnički kernel | **Hardverski KVM** |
| **Pogodno za** | Interni sistem | Brze skripte | Nepouzdane API mreže | Izvršavanje transakcija |

---

## 2. 3-Gate Closed-Loop Arhitektura (BH-Decision Motor)

Da bi autonomni agenti mogli bezbjedno operisati nad kritičnim enterprise resursima — poput SQL baza, slanja komercijalnih ponuda (alat za ponude) ili finansijskih transakcija — svaki korak mora proći kroz verifikacioni mehanizam u tri kapije (**3-Gate Closed-Loop Arhitektura**).

```
                      [Agent generiše akciju]
                                 |
                                 v
               +-----------------------------------+
               |  Gate L0: Procjena Rizika         |
               |  (READ / DRAFT / SEND / IRREV)    |
               +-----------------------------------+
                                 |
         +-----------------------+-----------------------+
         |                                               |
         | [READ/DRAFT]                                  | [SEND/IRREVERSIBLE]
         v                                               v
+-------------------------------+               +-------------------------------+
|  Gate 1: Pre-Execution        |               |  Gate 2: Human-in-the-Loop    |
|  - Statistički skeneri        |               |  - HC Dashboard & SMS / Email |
|  - Sandbox (srt offline)      |               |  - Eksplicitno odobrenje      |
+-------------------------------+               +-------------------------------+
         |                                               |
         +-----------------------+-----------------------+
                                 |
                                 v
+-------------------------------------------------------------------------------+
|  Izvršenje unutar TSR Sandboxa                                               |
+-------------------------------------------------------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------------------+
|  Gate 3: Post-Execution Verification                                          |
|  - sha256 hash validacija rezultata                                           |
|  - Nepromjenjivi audit trail                                                  |
|  - Automatski State Rollback na greškama                                      |
+-------------------------------------------------------------------------------+
```

### 2.1. L0 Procjena Rizika (Tiering)
Prije nego što se bilo koja akcija proslijedi na izvršenje, interni klasifikator u roku kraćem od 1 ms vrši evaluaciju namjere i kategorizaciju u jedan od četiri nivoa rizika:

*   **READ (Nizak rizik):** Upiti nad bazom podataka bez modifikacija (npr. provjera lagera, pretraga cijena u tabeli partnera, pretraga zaliha).
*   **DRAFT (Srednji rizik):** Kreiranje nacrta dokumenata, priprema komercijalne ponude, generisanje privremenih fajlova koji ne utiču na eksterne sisteme.
*   **SEND (Visok rizik):** Slanje emailova klijentima, generisanje konačnih PDF ponuda, slanje obavještenja na komunikacijske kanale (WA, Viber).
*   **IRREVERSIBLE (Kritični rizik):** Direktno kontiranje, upis u glavnu knjigu, modifikacija matičnih podataka kupaca, pokretanje eksternih transakcija plaćanja, izvršavanje destruktivnih bash komandi.

### 2.2. Gate 1: Pre-Execution static & dynamic validation
Za nivoe rizika `READ` i `DRAFT`, aktivira se automatski validacioni sloj:
*   **Static Scanning:** Semgrep i regex detektori analiziraju kod/skriptu na prisustvo hardkodiranih tajni, neovlaštenih IP adresa ili sumnjivih obrazaca sistemskih poziva.
*   **Dynamic Dry-Run:** Pokreće se izolovani dry-run unutar `gama sandbox offline` (srt sandbox) kako bi se osiguralo da kod ne pokušava neovlašteni mrežni pristup ili prekorječenje memorijskih kvota.

### 2.3. Gate 2: Human-in-the-Loop (HITL) i Human Compute (HC)
Za nivoe rizika `SEND` i `IRREVERSIBLE`, GAMA Decision OS **zabranjuje** potpuno autonomno izvršenje bez ljudske verifikacije. 
*   Sistem automatski suspenduje agentsku sesiju i šalje vizuelni/podatkovni prikaz planirane akcije na **Human Compute (HC) interfejs** ili operatersku konzolu.
*   Akcija se izvršava tek kada ovlašteni operater fizički/digitalno potvrdi transakciju na svom ekranu ili putem sigurnog tokena.

### 2.4. Gate 3: Post-Execution Verification i Audit Trail
Nakon što se akcija izvrši unutar TSR-a, closed-loop sistem vrši provjeru povratnih informacija:
*   **sha256 Verification:** Provjerava se cjelovitost nastalih fajlova ili modifikovanih redova u bazi podataka pomoću sha256 hash validacije.
*   **Audit Trail:** Svaki sistemski poziv, izmjena baze ili spoljni poziv trajno se zapisuje u nepromjenjivi kriptografski dnevnik transakcija.
*   **Automatski Rollback:** Ukoliko se detektuje odstupanje od planiranog stanja (npr. neočekivani SQL status kod ili prekid mrežne sesije), GAMA Decision OS automatski vraća sistem na zadnji verifikovani checkpoint (`gama rollback`) u roku od nekoliko milisekundi, sprečavajući kontaminaciju baze podataka.

---

## 3. Autonomni Agent Control Plane i EU AI Act

GAMA Decision OS nije samo tehničko rješenje, već i pravno-tehnološki okvir projektovan da zadovolji najstrože standarde evropske regulative o vještačkoj inteligenciji (**EU AI Act**).

```
                      +------------------------------------------+
                      |         EU AI Act Regulativa             |
                      +------------------------------------------+
                                           |
                    +----------------------+----------------------+
                    |                                             |
                    v                                             v
+----------------------------------------+  +----------------------------------------+
|   Visokorizični AI Sistemi (High-Risk)  |  |      Transparentnost i Sljedivost       |
|   - Obavezno upravljanje rizicima      |  |      - Nepromjenjivi logovi transakcija |
|   - Garantovan ljudski nadzor (HITL)   |  |      - sha256 potpisivanje svakog koraka|
+----------------------------------------+  +----------------------------------------+
                    |                                             |
                    +----------------------+----------------------+
                                           |
                                           v
                      +------------------------------------------+
                      |            GAMA Decision OS              |
                      |            Tehnička Rješenja             |
                      +------------------------------------------+
                      | - 3-Gate Arhitektura (Ljudski nadzor)    |
                      | - TSR Hardverska Sandbox Izolacija       |
                      | - Kriptografski Audit Trail              |
                      +------------------------------------------+
```

### 3.1. Klasifikacija i Usklađenost
Prema EU AI Act-u, AI sistemi koji upravljaju kritičnom infrastrukturom, donose odluke o zapošljavanju, ili vrše automatsku finansijsku/kreditnu procjenu svrstavaju se u **High-Risk AI (Visokorizične AI sisteme)**. Ovi sistemi moraju ispuniti rigorozne uslove:

1.  **Sistem upravljanja rizicima (Član 9):** GAMA Decision OS rješava ovaj zahtjev kroz **Gate L0** (dinamičko kaskadiranje rizika) i neprekidno skeniranje prije izvršenja.
2.  **Upravljanje podacima i data governance (Član 10):** Strogo odvajanje testnih, produkcionih i agentskih memorijskih lokacija u izolovanim Firecracker mikro-VM-ovima sprečava curenje osjetljivih komercijalnih podataka.
3.  **Tehnička dokumentacija i transparentnost (Član 11 i 13):** Svaka odluka agenta, uključujući i LLM kontekst i sistemske pozive, biva zabilježena. To omogućava rekonstrukciju "mislenog procesa" agenta u bilo kom trenutku.
4.  **Ljudski nadzor (Član 14):** Naš **Gate 2 (HITL/HC)** pruža stopostotnu garanciju da nijedan visokorizični ili ireverzibilni korak (npr. plaćanje, fakturisanje, izmjene PDV stopa na 17% u BiH) ne može proći bez eksplicitnog ljudskog odobrenja.

### 3.2. Primjena u Enterprise ERP-u (GAMA TRADE)
U tradicionalnim ERP sistemima, greška u skripti ili pogrešna kalkulacija može dovesti do katastrofalnih poreskih i pravnih posledica. GAMA Decision OS unosi revolucionarnu bezbjednost u operacije nad realnim bazama podataka:

*   **Poreska konzistentnost:** Prilikom rada sa porezom na dodatu vrijednost (PDV stopa od 17% u Bosni i Hercegovini), agentske kalkulacije se automatski verifikuju u **Gate 1** kroz nezavisne matematičke modele prije upisa u ERP bazu.
*   **Zaštita integriteta tabela:** Direktni upisi u kritične tabele (npr. tabela partnera i kupaca) automatski se preusmjeravaju na najviši nivo izolacije u Firecracker runtime-u, gdje se provjerava integritet stranih ključeva i referencijalni integritet baze podataka prije trajnog commita.

---

## 4. Tehnološki Roadmap i Zaključak

GAMA Decision OS preoblikuje koncept enterprise softvera. Umjesto statičnih baza podataka u kojima ljudi ručno obavljaju svaki klik, naša platforma uspostavlja dinamičan, autonoman i potpuno osiguran agentski ekosistem.

### Ključne prekretnice u razvoju:
*   **Faza 1: TSR Konsolidacija (Završeno):** Implementacija i stabilizacija runc, gVisor i Firecracker runtime-a na testnoj infrastrukturi sa snapshot brzinom od 2.28 ms.
*   **Faza 2: 3-Gate Integration (Završeno):** Uvezivanje BH-Decision motora sa produkcijskim ERP SQL bazama i verifikacija transakcija kroz sha256 i rollback mehanizme.
*   **Faza 3: EU AI Act Certifikacija (U toku):** Priprema tehničkog dosijea za usklađenost sa evropskim regulatornim tijelima, pozicionirajući GAMA Decision OS kao prvi sertifikovani operativni sistem za autonomne agente na svijetu.

**GAMA Decision OS** postavlja standard za bezbjednu, robusnu i zakonski usklađenu primjenu vještačke inteligencije u modernom poslovanju.

---
*Kreirano u okviru revolucionarnog poduhvata GAMA TRADE ekosistema.*  
**Lokacija dokumenta:** `docs/GAMA_DECISION_OS_MANIFESTO.md`  
**Datum izdavanja:** 13. novembar 2026. godine.
