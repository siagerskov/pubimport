# Ändringslogg

## 2026-11-02

- Version 2 gav fortfarande irrelevanta provträffar. Sökförslag version 3
  kräver radiologisk modalitet i titel och prioriterar precision före recall.
- Actions visar nu en kort, HTML-escapad sammanfattning med artikelrubriker,
  sökversioner, antal och trunkering direkt på körningens översiktssida.

- Verklig dry-run verifierad via användarens Actions-logg: nio unika poster,
  noll importer och inga metadatafel i det begränsade urvalet.
- Sökförslag version 2 kräver tydligare radiologiska modaliteter efter
  irrelevanta spektroskopi-/fluorescensträffar i version 1; klinisk granskning återstår.

- Appkoden pushad till GitHub. Dry-run startas automatiskt vid appändringar
  på main; apply kräver fortsatt manuell trigger och biblioteksbekräftelse.

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
