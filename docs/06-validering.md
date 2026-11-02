# Validering

## Aktuellt utfall 0.2 – 2026-11-01

- **93 tester passerar**, inga överhoppade eller förväntade fel.
- Formatteringskontroll och lint godkända.
- Källpaket/wheel byggda; wheel installerad i en separat tom miljö.
- Installerad CLI och Actions-runner i offline-läge: fem planerade samlingar,
  två nya referenser, fyra proveniensanteckningar, totalt elva steg, noll importer.
- Simulerad full import och ny snapshot/omkörning: inga ytterligare steg.
- Testat avbrott vid flera steg, även serversparad post med förlorat svar;
  ny läsning reparerar saknad proveniens utan dubbelimport.
- Verifierat: manuella titlar/taggar/notes, godkänd status och papperskorg
  bevaras; överlapp kompletterar bara appens ej granskade inkorgsposter.
- Testat: DOI/PMID-konflikt, ändrad sökversion, saknad titel, pagination,
  versionskonflikt, read-retries, sanerade autentiseringsfel, inga blinda write-retries,
  bibliotekskonfirmation, importtak och förbud mot fixture-import.

**Uppdatering 2026-11-02:** användarens logg från Actions 41438100545
verifierar verklig PubMed/Zotero-läsning och dry-run för sökversion 1:
319 sökträffar totalt (inklusive överlapp), nio unika hämtade PMID vid cap 5
per sökning, nio nya, noll kända, noll metadatafel, 24 plansteg och noll importer.
Irrelevanta titlar motiverar sökversion 2; dess relevans är ännu inte verifierad.

**Återstår:** ny dry-run för version 2, pilot med
manuell bibliografisk kontroll, omkörning i Zotero och observerad Actions-körning.
Zotero-nyckel och biblioteks-ID är inte konfigurerade i miljön; API-domänerna
behöver tillåtas. Ingen verklig Zotero-skrivning, push eller publicering har gjorts.
Dagligt schema är avstängt. MVP-acceptans kan ännu inte hävdas.

## Historik: version 0.1

## Reproducerbara kontroller

```bash
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run pubmed-zotero --fixture tests/fixtures/pubmed.xml
```

Tester är offline; injicerad transport och väntan gör inga riktiga API-anrop.
Fixtures är påhittade. Utfall från leveransen dokumenteras nedan efter körning.

| Krav | Kontroll i etapp 0–1 |
|---|---|
| Bibliografisk normalisering | Inline-XML, strukturerat abstract, DOI, gruppförfattare, partiellt datum |
| Saknad metadata | Null/tom lista; inget fabricerat innehåll |
| Överlapp mellan sökningar | En artikel per PMID med flera provenienser |
| Ändrad query-version | Ny version i proveniens |
| Datum | UTC och 14 kalenderdagars överlapp |
| ESearch-paginering | Flera sidor, nollträffar, explicit cap och 9999-gräns |
| EFetch-fullständighet | Ordning återställs; saknade/oväntade ID:n avvisas |
| Retry | Timeout, nätfel, 429, 503, Retry-After; begränsat antal försök |
| Fel och hemligheter | Sanerade fel, ogiltig JSON/XML/YAML avvisas |
| Offline CLI | Verklig CLI till JSON, ingen nätverksklient skapas |
| Zotero-import och ny PMID | Inte implementerat |
| Biblioteksidempotens och DOI-konflikt | Inte implementerat |
| Manuella statusar, partiellt importfel | Inte implementerat |
| Verklig dry-run mot båda API:erna | Inte genomförd |
| Pilot och omkörning i Zotero | Kräver senare godkännande och integration |

Offline-rapporten är inte en komplett Zotero-dry-run. MVP är inte accepterad
innan riktig dry-run, pilotgranskning, omkörningsidempotens och dokumenterad
installation till verklig import har verifierats. Levande NCBI-test är valfritt
i denna etapp och kräver tillåten nätåtkomst.

## Genomfört 2026-11-01 – etapp 0–1

- `uv sync --frozen`: godkänd i projektmiljön och en separat tom miljö under `/tmp`.
- `uv run pytest`: **47 passerade**, inga hoppade över eller förväntade fel.
- `uv run ruff check .`: godkänd.
- `uv run ruff format --check .`: godkänd efter formattering.
- Installerad CLI i den rena miljön: fyra syntetiska sökträffar, två unika PMID,
  två proveniensposter per artikel, noll importer och ingen trunkering.
- Explicit `--limit 1`: en unik artikel och synlig trunkering.
- `uv build`: källpaket och wheel byggda, wheel-installation verifierad separat.

Live-anrop mot NCBI har inte körts. Miljöns tillåtna domäner innehåller inte
`eutils.ncbi.nlm.nih.gov`; ingen nätverkspolicy eller publicerad miljö har ändrats.
CI-filer har skapats men ingen GitHub Actions-körning har observerats.
Zotero har inte kontaktats. End-to-end-import, klinisk relevans, drift och
biblioteksidempotens återstår. Detta avslutar enbart etapp 0–1.

## Sökversion 2/3 och rapportsammanfattning – 2026-11-02

Användarlogg från körning 41438795739 verifierar 1524 träffar totalt, tio unika
hämtade poster, tio nya, noll metadatafel/importer och 25 plansteg för version 2.
Fortfarande irrelevanta provtitlar: ingen pilot godkänns på detta underlag.
Version 3 är ett snävare förslag med sämre förväntad recall, ännu inte livevaliderat.
Lokala tester: **95 passerar**, inklusive sammanfattning med escapad extern titel
och den riktiga offline-runnerns generering av Actions Summary. Lint och format godkända.

## Fristående sökverktyg – 2026-11-02

- 95 Python-tester och sju JavaScript-tester passerar; lint och format godkända.
- Chromium via tillfällig lokal HTTP-server: termgrupper, fältval, query-preview,
  sparat utkast efter omladdning, YAML-nedladdning, ny bevakning och mobilbredd
  verifierade utan JavaScript-fel. Ingen riktig PubMed-flik öppnades i browserprovet;
  provlänkens query och UTC-datumintervall verifieras av JavaScript-test.
- Den faktiskt browsernedladdade YAML-filen lästes av appens `load_searches`:
  två giltiga sökningar, ändrad query med höjd version och rätt term/fälttaggar.
- Verktyget saknar API-nycklar och externa skrivoperationer. En lokal HTML-fil
  kan inte automatiskt ersätta repositorykonfiguration; införande sker separat.
