# Validering

## Senast verifierad start av automatiken – 2026-11-02

Statusfilen från Actions **41454865904**, källcommit
`b5ffd5f24f4382950107c7166a70ad57872cce27`, lästes direkt via Git-grenen
`automation-status`. Sync-jobbet lyckades i apply-läge:

- Engångsrättning: `tag_fix=verified`, målpostens status/godkand läst tillbaka.
- Tio nya referenser importerade; fyra befintliga pilotposter kändes igen.
- Noll saknade titlar, noll fel, 21 av 21 plansteg slutförda.
- 427 nya träffar uppskjutna av tiotaket.

Dagligt schema 05:23 UTC är pushat på main. Första tidstyrda körningen är ännu
inte observerad. Statuspublicering till separat gren fungerar i verklig körning.
Det stora antalet uppskjutna träffar innebär att tiotaket inte garanterar att
allt hinner importeras innan 14-dagarsfönstret passerar. Ingen ytterligare
bulkimport eller höjning av taket görs utan nytt beslut om kapacitet.


## Aktuellt utfall – 2026-11-02

Användarens read-only Actions-resultat från körning **41445005452** bekräftar:

- Fyra kända pilotreferenser, noll nya och noll saknade titlar.
- Noll återstående åtgärder, noll importer och noll fel i diagnosen.
- Exakt en synlig barnanteckning med rätt proveniensmarkör per pilotreferens.
- Nyckelrättigheter: library=true, notes=true, write=true.

PMID: 42960128, 42959815, 42959533 och 42936410.
Den nya planen för piloturvalet är tom efter behörighetsändringen. Ingen
reparation, extra referens eller anteckning behövde skapas. Detta verifierar
omkörningsplanens idempotens för just dessa fyra poster, inte alla framtida fall.
Dagligt schema är fortsatt avstängt. Manuell kontroll i Zotero av metadata,
samlingar och status återstår, liksom separat godkännande av automatisk drift.

## Tidigare verkliga körningar

- **41438100545**, sökversion 1: 319 sökträffar totalt (kan överlappa), nio
  unika hämtade PMID vid högst fem per sökning, nio nya, noll metadatafel/importer.
  Irrelevanta provtitlar motiverade fortsatt sökarbete.
- **41438795739**, version 2: 1524 träffar totalt, tio unika hämtade poster,
  tio nya, noll metadatafel/importer. Fortfarande irrelevanta titlar. Version 3
  prioriterade tydligare modaliteter i titel; användarens exakta MSK-query blev v4.
- Användarens dry-run för MSK v4/AI v3: 469 träffar totalt, nio unika hämtade,
  nio nya, noll metadatafel/importer. Det trunkerade provurvalet var mer relevant;
  PET/CT-lymfomträffen i MSK visar att sökprecision fortfarande kräver granskning.
- **41443477199**, godkänd fyrpostspilot: fyra referenser importerades, men
  omkörningsplanen var inte tom. Ingen andra skrivomgång genomfördes.
- **41444085669**: alla fyra poster hittades, men deras barnanteckningar var
  osynliga; planen föreslog fyra notes och inga nya referenser. Ingen reparation
  gjordes. Efter användarens ändring av notes-behörighet visar **41445005452**
  att anteckningarna redan fanns och att inga ytterligare åtgärder behövs.

Node/Ubuntu-varningarna i Actions är separata från det tidigare kontrollfelet.
GitHub API är inte åtkomligt från utvecklingsmiljön; verkliga utfall ovan bygger
på användarens delade Actions-loggar och sammanfattningar.

## Lokala kontroller

```bash
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run pytest
node web/search-builder.test.cjs
uv build
```

Senaste kodkontrollen: **103 Python-tester passerar**, inga överhoppade eller
förväntade fel. Lint/format godkända. Sju JavaScript-tester för sökverktyget har
passerat. Källpaket/wheel och ren installation/CLI verifierades för version 0.2.
Alla standardtester använder syntetiska data och simulerade API:er, inga nycklar.

Täckning: metadatafall, saknade fält, ESearch-paginering, EFetch-batchar,
fullständighet, nätfel/429/5xx, sanerade fel, XML-säkerhet, UTC-datum, query-version,
PMID/DOI-konflikter, överlapp, samlingsmedlemskap, proveniens, manuella taggar/titlar/
notes, papperskorg, partiellt importfel, förlorat skrivsvar, versionsskydd,
importtak, fixture-spärr, fryst piloturval och kontroll av library/notes/write.

Chromiumkontroll av sökverktyget via tillfällig lokal HTTP-server verifierade
termgrupper, fältval, förhandsvisning, utkast efter omladdning, YAML-nedladdning,
ny bevakning och mobilbredd. Den faktiskt nedladdade filen godkändes av appens
konfigurationsläsare. PubMed-provlänkens query och datum kontrolleras separat av
JavaScript-test, inte genom klinisk relevanssimulering.

## Återstår före färdig drift

1. Användarens manuella kontroll av de fyra importerade posterna i Zotero.
2. Klinisk granskning av sökstrategier och beslut om önskad precision/recall.
3. Separat godkännande för dagligt schema, valt importtak och driftövervakning.
4. Observerad lyckad körning av det godkända schemat; ingen sådan körning finns ännu.

## Automatiskt flöde godkänt och förberett – 2026-11-02

Användaren godkände rättning av den sista taggen och full automatisk drift.
Lokalt: **110 Python-tester passerar**, inklusive uppdelning mellan sökningar,
uppskjutna referenser, flera ikappbatchar utan dubbletter samt en riktad tagg-PATCH
som bevarar andra fält och avbryter vid ändrad manuell status. Lint/format godkända.
GitHub Actions-v6-commits upplösta via officiella Git-remotes.
Verkligt utfall från engångsrättning/startimport och första tidstyrda körning
är ännu inte observerat. Tidigare stycken som anger att godkännande återstår
beskriver historiken; daglig drift är nu uttryckligen godkänd.

Statuspubliceringens två tester verifierar att enbart den separata grenen
uppdateras och att endast tillåtna heltalsräknare publiceras. Totalt **112
Python-tester** passerar tillsammans med sju JavaScript-tester. Faktisk
statuspublicering och startimport återstår tills körningen avslutats.

## Samlingsstyrda status-taggar – 2026-11-02

Användaren bad uttryckligen om automatiska taggar efter flytt till godkänd-samlingen.
Policyn testas med appskapade referenser: godkännande, borttagning från hela
inkorgsträdet, bevarade metadata/egna taggar, normalisering av godkänd/godkand,
konflikter med exkluderad, poster utanför sökfönstret, papperskorg/manuella poster,
omkörning och giltiga maskinstatusutdata. Importtaket är höjt till 20.
Lokalt: 119 Python-tester och sju JavaScript-tester passerar; lint/format godkända.
Första verkliga timkontrollens utfall återstår att läsa från review-status-grenen.

Första verkliga kontrollen är nu verifierad via review-status.json, Actions
41456837631, commit 835e8a39a85ed614cb8cf5219b8cd5cd3918012a: success i apply-läge,
14 kända appreferenser, noll godkännandeuppdateringar, noll konflikter och noll fel.
Ingen ny referens importerades. Denna första körning behövde inte ändra status;
positiva flytt-/PATCH-fall är verifierade i tester. Första senare timtrigger och
nästa verkliga användarflytt kan följas via samma säkra statusgren.
