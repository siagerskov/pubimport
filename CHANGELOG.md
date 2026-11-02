# Ändringslogg

## 2026-11-02

- Kategoritak verifierade i verklig körning 41471950206: 46 nya referenser
  importerade utan fel, med dagens sluträkning AI 20, NPH 20 och MSK 20.
  Tidigare importer räknades med; återstående kvot noll i varje kategori.

- Användaren godkände historisk import för AI och NPH från 2018, nyast först,
  och förtydligade **20 nya per kategori och svensk kalenderdag**, inte gemensamt.
- Ursprunglig importkategori sparas på nya poster. Samma dygnsräkning gäller
  schemalagda och manuella jobb; överlapp räknas mot båda kategorierna.
- Senaste publiceringsåret bearbetas först och därefter äldre år vid behov.
  Endast nödvändiga kandidatmetadata hämtas; kända referenser dupliceras inte.

- Dokumentationen konsoliderad till aktuellt flöde: 20-tak, timvis godkännande,
  separata NPH/AI-bevakningar och retrospektiv PDAT. Äldre utfall tydligt historik.
- Retrospektiv read-only-körning verifierad: AI 17977 och NPH 2008 träffar sedan
  2018-01-01. Föreslagen första NPH-batch: år 2018, högst 20 nya; ännu inte godkänd/startad.
- Sökverktyget bevarar egna utkast men lägger till nya standardbevakningar säkert.

- Separat NPH-bevakning utan radiologi-/AI-filter enligt användarens val.
  AI inom bilddiagnostik och MSK finns kvar som separata sökningar.
- Retrospektivt PDAT-läge med start 2018-01-01, val av bevakningar och slutdatum.
  Dagligt EDAT-fönster påverkas inte. Datumtyp/intervall sparas i ny proveniens.
- Automatisk uppdelning av sökintervall över PubMeds 9999-gräns och säker
  read-only kartläggning via nytt backfill-workflow och separat statusgren.

- Första livekontroll av godkännandeautomatiken lyckades: 14 kända appreferenser,
  inga väntande statusändringar, inga konflikter/fel och inga nya importer.

- Användargodkänd automatisk status: dragning till godkänd-samlingen sätter
  status/godkand och tar bort inkorgsmedlemskap, även i ämnesundersamlingar.
- Timvis kontroll utan nya importer, samt samma policy vid import. Egna
  taggar/metadata bevaras; konflikter med avvakta/exkluderad rapporteras.
- Separat review-status-gren gör att utfallet kan följas direkt via Git.

- På användarens begäran höjt dagligt importtak och standardbatch från 10 till 20
  nya referenser. Tidpunkten 05:23 UTC och datumfönstret är oförändrade.

- Verifierad startkörning 41454865904: taggrättning bekräftad, tio nya referenser
  importerade, fyra kända, noll fel. Maskinläsbar status kunde läsas direkt via Git.
- 427 träffar uppskjutna; tiotakets kapacitetsbegränsning dokumenterad.

- Maskinläsbar status på separat automation-status-gren gör att resultat kan
  följas via Git även när GitHubs API inte kan nås från utvecklingsmiljön.
  Endast räknare/utfall publiceras; separat jobb har skrivrättighet till repo.

- Användaren godkände rättning av pilot-taggen och hela det automatiska flödet.
- Dagligt schema 05:23 UTC, full EDAT-sökning och högst tio nya referenser per
  körning, fördelade mellan ämnena. Uppskjutna räknas; datumfönstrets köbegränsning dokumenterad.
- Engångsrättning av exakt PMID 42960128 med bevarade metadata/övriga taggar och
  verifiering efter PATCH. Vanlig synkning ändrar fortsatt aldrig manuella statusar.
- Actions uppgraderade till officiellt upplösta v6-commits och Ubuntu 24.04.

- Read-only pilotkontroll visar nu status-taggar, godkänd-samling och medlemskap
  i inkorgen inklusive undersamlingar efter användarens manuella granskning.

- Efter ändrad notes-behörighet verifierar verklig read-only-diagnos 41445005452
  fyra kända pilotposter, rätt befintlig proveniens och noll återstående åtgärder.
  Ingen reparation eller dubbelimport behövdes. Manuell kvalitetskontroll återstår.
- Valideringsdokumentet rättat och sammanställt med observerade utfall.

- Pilotdiagnos: fyra kända referenser men inga synliga barnanteckningar;
  återstående plan omfattar fyra notes, inga nya referenser.
- Infört kontroll av library/notes/write-permission via keys/current innan
  synkning. Read-only-diagnosen visar enbart booleska rättigheter, aldrig nyckeln.

- Användarens pilotlogg bekräftar fyra importerade referenser, men omkörningsplanen
  var inte tom. Fortsatt skrivning hålls avstängd under felsökningen.
- Separat read-only pilotdiagnos för exakt de fyra importerade PMID:erna:
  antal kända poster, återstående åtgärdstyper och igenkänd proveniens, utan att
  skriva ut övriga biblioteksanteckningar eller göra någon reparation.

- Användaren godkände pilot med högst fyra nya referenser. Engångsworkflow
  för exakt godkänd push, utan möjlighet till automatisk import via re-run.
- Pilot hämtar högst två träffar per sökning, fryser urvalet och verifierar
  efter import att en ny plan för samma urval inte kräver fler åtgärder.

- Infört användarens exakta MSK-query som version 4; fluoroskopi och tomosyntes
  borttagna ur den sökningen. AI kvar på version 3. Sökverktygets grundförslag uppdaterade.

- Fristående sökverktyg i `web/search-builder.html`: egna termer, OR/AND/NOT,
  val av titel/titel-abstract/alla fält, query-förhandsvisning och PubMed-länk.
- Export till validerbar searches.yaml, automatisk versionshöjning från medföljande
  query och valfritt lokalt utkast. Inga API-nycklar eller externa skrivningar.
- Sju JavaScript-tester och automatiserad browserkontroll tillagda.

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
