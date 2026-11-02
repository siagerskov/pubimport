# Genomförandestatus och återstående arbete

## Implementerat och verifierat

- Pythonpaket, låsfil, CI, offline-fixtures, testbar HTTP och versionshanterad dokumentation.
- PubMed ESearch/EFetch med metadata, paginering, återförsök och fullständighetskontroller.
- Zotero-snapshot, behörighetskontroll, PMID/DOI-matchning, proveniens och versionsskyddad import.
- Fyrpostspilot verifierad via användarens loggar; notes-rättigheter åtgärdade.
- Användarens manuella granskning och en riktad taggrättning verifierade.
- Daglig import konfigurerad 05:23 UTC, nu 20 per kategori och svensk kalenderdag.
  Verklig startimport av tio referenser utan fel observerad. Första schematrigger
  är separat från startkörningen och ska fortfarande verifieras när den inträffar.
- Användargodkänd timvis godkännandesynk: första livekontrollen av 14 poster lyckades.
- Fristående sökverktyg med YAML-export och bevarande av utkast vid nya grundsökningar.
- Statusgrenar gör att resultat kan läsas direkt via Git.

## Nytillkommet enligt användarens önskemål

NPH är separat utan radiologifilter; AI inom bilddiagnostik är separat och MSK
behålls. Retrospektivt PDAT-läge från 2018 med datumuppdelning är implementerat.
Kartläggningen gav 17977 AI-träffar och 2008 NPH-träffar. Därefter godkände
användaren verklig återfyllnad från 2018, nyast först och 20 per kategori/dag.
Daglig körning arbetar sig bakåt från senaste året och delar kvoter med manuella jobb.

## Fortsatt validering och begränsningar

1. Följ första faktiska schemakörningen via automation-status och review-status.
2. Bedöm relevans och recall för varje query. Titelbaserad AI-strategi kan missa relevanta arbeten.
3. Följ den godkända återfyllnaden och de separata dygnstaken till dess hela perioden genomgåtts.
4. Övervaka deferred och review_conflicts; rullande fönster är ingen beständig kö.
5. Fulltext, automatisk kvalitetsgradering, destruktiv sammanslagning och automatisk
   metadataöverskrivning ingår inte. Licensförslag MIT är ännu inget valt licensavtal.

Faktiska testantal och kör-ID:n finns i 06-validering.md. Historiska formuleringar
i CHANGELOG/ADR ska läsas som historik; denna fil och driftguiden beskriver aktuell status.

Starten av kategorivis återfyllnad är verifierad i 41471950206: 46 nya utan fel,
slutlig förbrukning 20/20 per kategori efter att tidigare importer räknats med.
Återfyllnaden fortsätter automatiskt vid nya kalenderdagars utrymme, nyast först.
