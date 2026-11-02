# Validering och observerade utfall

## Aktuell verifieringsstatus 2026-11-02

- 139 Python-tester och nio JavaScript-tester passerar, utan överhoppade eller
  förväntade fel. Lint och formattering är godkända.
- Daglig import är godkänd och konfigurerad 05:23 UTC med tak **20 per kategori/dag**.
  Startkörning observerad; första senare schematrigger är ännu inte dokumenterad.
- Timvis samlingsstyrt godkännande är godkänt och dess första livekontroll lyckades.
- NPH är tillagd separat utan radiologi-/AI-filter. AI och MSK är egna bevakningar.
- Retrospektiv PDAT-kartläggning från 2018 är verkligt verifierad utan skrivning.
- AI och NPH från 2018, nyast först och 20 per kategori/dag, är uttryckligen
  godkänt. Den nya återfyllnadens startkörning är verifierad via publicerad status.

## Verklig retrospektiv kartläggning

Körning **41464377138**, commit 47bf06d009669d18fa1a1d5c00a788b2846ee89c,
lästes direkt från backfill-status-grenen. Success, dry-run, PDAT
2018-01-01–2026-11-02:

| Bevakning | Totalantal | Hämtat provurval |
|---|---:|---:|
| AI inom bilddiagnostik v3 | 17977 | 5 |
| NPH v1 | 2008 | 5 |

Summan 19985 kan överlappa mellan bevakningarna och är inte antal nya
biblioteksposter. I de tio provposterna var nio nya och en känd, inga
metadatafel och noll importer. Detta validerar åtkomst och urvalets datum,
inte klinisk relevans för hela historiken eller komplett historisk import.

## Verifierad driftstart och pilot

- **41454865904**, commit b5ffd5f24f4382950107c7166a70ad57872cce27:
  apply lyckades, riktad status/godkand-rättning verifierad, tio nya importerade,
  fyra kända, noll fel, 21 slutförda steg. Dåvarande tiotak sköt upp 427 poster.
  Taket höjdes därefter till 20; det gamla antalet är ett historiskt utfall.
- **41456837631**, commit 835e8a39a85ed614cb8cf5219b8cd5cd3918012a:
  första godkännandekontrollen lyckades med 14 kända referenser, noll väntande
  ändringar, konflikter eller fel. Inga nya referenser importerades.
- **41445005452**: fyra ursprungliga pilotreferenser hittades, var och en med
  exakt en befintlig proveniensanteckning; tom omkörningsplan, noll nya/fel.
  library/notes/write var true. Ingen reparation eller dubbelimport behövdes.
- **41443477199** importerade fyra referenser men första omkörningskontrollen
  såg inte notes. **41444085669** visade fyra osynliga notes, inga nya referenser.
  Efter notes-behörighetsändring visade 41445005452 att anteckningarna redan fanns.
- Användaren granskade pilotposterna och flyttade dem till godkänd-samlingen.
  Återstående stavningsvariant korrigerades av den godkända riktade startåtgärden.

Tidiga query-prov i 41438100545 (319 träffar) och 41438795739 (1524 träffar)
innehöll irrelevanta titlar. Därefter snävades titelmodaliteter in; användarens
exakta MSK-sträng blev v4. Detta är inte ett påstående om systematiskt validerad recall.

Tidiga utfall ovan kommer från användarens loggar. Nyare utfall kan läsas direkt
via säkra Git-statusgrenar; GitHub API är inte tillgängligt från utvecklingsmiljön.

## Reproducerbara kontroller

```bash
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run pytest
node web/search-builder.test.cjs
uv build
```

Standardtester är offline, använder syntetiska data och injicerad transport/klocka.
De täcker metadata, saknade fält, XML-säkerhet, ESearch-paginering, EFetch-batchar,
nätfel/429/5xx, sanerade fel, identifierarkonflikter, proveniens, samtidiga ändringar,
papperskorg, manuella data, avbrott/förlorade skrivsvar, fryst piloturval,
behörigheter, batchtak/ikappkörning, fördelning mellan ämnen och godkännandesynk.
Retrospektiva tester täcker PDAT, start/slutdatum, val av bevakningar, felaktiga
datum, rekursiv datumuppdelning och count-förändringar som inte får döljas.

Chromiumkontroll via lokal HTTP-server verifierade sökverktygets termgrupper,
fältval, preview, utkast efter omladdning, nedladdning, ny bevakning och mobilbredd.
Senast exporterade tre-sökningsfil godkändes av appens riktiga konfigurationsläsare.
Utkast-migrering testas så att nya grundsökningar läggs till och egna ändringar
bevaras. Provlänkens datum/query testas; ingen lokal klinisk relevanssimulering påstås.
Källpaket/wheel och ren installation/CLI verifierades vid version 0.2:s införande.

## Begränsningar och fortsatt arbete

Klinisk relevans/recall behöver följas per query. Hela materialet från 2018 har
inte importerats. Historik körs separat i granskade batchar; stora intervall kan
kräva mycket tid och metadata. Rullande EDAT med tjugotak är inte en beständig kö.
Följ deferred, review_conflicts och verkliga schemakörningar. Ingen automatisk
metadataöverskrivning, radering, PDF-hämtning eller evidensgradering finns.

Automatisk godkännandegranskning stoppade pushen som skulle starta faktisk
återfyllnad. Granskningen bedömde att tillstånd för retrospektiv sökning inte
omfattade den specifika tjugopostsbatchens externa skrivning. Engångsstarten
har därför tagits bort; dokumentation och read-only-funktioner publiceras separat.
Ingen ny historisk referens har importerats av detta arbete.

## Godkänd drift: nyast först, 20 per kategori/dag

Användaren godkände faktisk historisk import för både AI och NPH från 2018 och
förtydligade därefter 20 per kategori/dag. Detta ersätter det tidigare förslaget
om enbart NPH år 2018 och det tidigare gemensamma taket. Nyast först gäller båda.
138 Python-tester och nio JavaScript-tester passerar före driftsättning.
Nya tester täcker svensk kalenderdag, oberoende tak, papperskorg, legacy-proveniens,
överlapp som belastar båda, noll kvar i en kategori, nyast först, framflyttning
till äldre år, begränsad metadatahämtning och upprepad faktisk runner med noll
nya importer efter uppnådda kategoritak. Liveutfall från nya driftstarten återstår.

Legacy-räkningen verifierar också att senare tillagda provenienser inte flyttar
ursprungskategori för en referens som skapats tidigare under dagen. Totalt 139
Python-tester och nio JavaScript-tester passerar inför starten.

## Verifierad start med kategorivisa dygnstak

Actions **41471950206**, commit 223ba7ded6e8295c76a2f85f82531306fdd8c037,
rapporterade success/apply 2026-11-02. Resultatet lästes direkt från automation-status.
46 nya referenser importerades, 14 tidigare poster kändes igen, noll fel och
93/93 plansteg slutfördes. Dagens återlästa kvoter i Europe/Stockholm var:

| Kategori | Importerade under kalenderdagen | Återstående |
|---|---:|---:|
| MSK | 20 | 0 |
| AI | 20 | 0 |
| NPH | 20 | 0 |

AI/NPH-kandidatfönstren började med 2026-01-01–2026-11-02 på PDAT; nyare material
fyllde kvoterna, så tidigare år behövde inte besökas i denna körning. Det är
avsiktligt nyast-först, inte ett påstående att 2018 redan är genomgånget.
Endast 92 kandidatmetadata hämtades trots 4206 träffar i de besökta fönstren.
Rapportens 46 deferred avser urvalet, inte hela återstående historiken.
Nästa kalenderdag ger nytt utrymme. Första faktiska schedule-triggern är
separat från denna lyckade startpush och återstår att observera.
