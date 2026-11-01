# Ändringslogg

## 0.2.0 – 2026-11-01

- Etapp 2: Zotero API-v3-klient, konsistent paginerad snapshot, samlingsplanering,
  bibliografisk mappning och offline/live dry-run.
- Etapp 3: PMID/DOI-matchning, konfliktstopp, proveniensanteckningar,
  explicit apply med importtak och versionsskydd, säker omkörning efter partiella fel.
- Manuella statusar, metadata, personliga notes och papperskorgsval bevaras.
- Etapp 4: manuellt Actions-flöde med offline/dry-run/apply, concurrency
  och körinstruktioner; dagligt schema förblir avstängt.
- Mockade integrations- och återhämtningsprov; ingen verklig import genomförd.

## 0.1.0 – 2026-11-01

### Etapp 0 – Projektbootstrap
- Pythonpaket, CLI, versionslåsta beroenden och CI för offline-kontroller.
- Projektregler, installationsanvisningar, dokumentation och etappplan.

### Etapp 1 – PubMed-läsning
- Två versionshanterade sökförslag med överlappande EDAT-datumfönster.
- ESearch/EFetch med paginering, batchar, timeout, hastighetsbegränsning,
  sanerade fel och begränsade återförsök, inklusive Retry-After.
- Normalisering av PMID, DOI, titel, författare, datum, tidskrift och abstract.
- JSON-rapport med proveniens och sammanslagning av överlappande PMID inom körningen.
- Syntetiskt offline-läge och mockade integrationstester. Ingen Zotero-skrivning.
