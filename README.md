# PubMed → Zotero

Automatisk litteraturbevakning för MSK-radiologi och AI inom radiologi med en
Zotero-inkorg för manuell granskning. **Version 0.2 implementerar synkningen och
manuell körning. En fyrpostspilot och tom omkörningsplan är verifierade;
daglig drift är godkänd och konfigurerad. Startkörningen importerade tio nya
referenser utan fel och verifierade taggrättningen. Första tidstyrda körningen
återstår att observera.**

## Bevakningar och historik

Tre separata bevakningar finns: **MSK-radiologi**, **AI inom bilddiagnostik**
och **NPH**. NPH gäller normaltryckshydrocefalus och är inte begränsad till radiologi.
För fler bevakningar: använd Ny bevakning i verktyget, exportera YAML och inför
filen enligt instruktionen nedan. En ny bevakning behöver ett unikt stabilt ID.

AI och NPH återfylls nu automatiskt från **2018-01-01**, nyast först enligt
publiceringsdatum, med separata tak på **20 nya per kategori och svensk kalenderdag**.
Artiklar som matchar båda skapas en gång men räknas mot båda kategoriernas tak.
Actions → Retrospective PubMed search finns också för avgränsad manuell dry-run/import.
Extra manuella körningar använder samma dygnsräkning.
Se [retrospektiv import](docs/11-retrospektiv-import.md) för antal, full genomgång,
årsvise batchar och skillnaden mot daglig EDAT-bevakning.

## Eget sökverktyg

Öppna `web/search-builder.html` i en vanlig webbläsare (ladda ned HTML-filen
först om du tittar på GitHub). Den är fristående och behöver ingen installation,
server, nyckel eller internet för redigering och export.

Välj en bevakning eller **Ny bevakning**, sedan **Bygg av söktermer**. Ange en
engelsk term/fras per rad, välj sökfält och prova med **Prova i PubMed**. Termer
inom gruppen kombineras med OR, ämne och metod med AND. NOT är valfritt och bör
användas försiktigt. PubMed öppnas i en ny flik med samma EDAT-fönster som appen.

**Ladda ned searches.yaml** exporterar alla bevakningar med stabila ID:n och
uppdaterad query-version. Granska och ersätt `config/searches.yaml` eller dela
filen i utvecklingschatten för införande. Verktyget ändrar inte GitHub eller
Zotero. **Spara utkast i webbläsaren** är valfritt; filen sparas annars inte
mellan sessioner. Inkludera aldrig patientuppgifter i söktermer.

## Prova utan konton

Python 3.12+ och [uv](https://docs.astral.sh/uv/) behövs. Från repositoryroten:

```bash
uv sync --frozen
uv run pubmed-zotero --fixture tests/fixtures/pubmed.xml \
  --zotero-snapshot tests/fixtures/zotero-empty.json
```

Detta är en helt offline dry-run. Två syntetiska artiklar hittas av tre
sökningar; planen visar sex samlingar, två referenser och sex separata
proveniensanteckningar. **Noll externa skrivningar.** `sync.summary.new=2`,
`sync.summary.actions=14` och `imported=0`. Inga konton eller nycklar behövs.

I molnmiljön kan `export UV_CACHE_DIR=/workspace/.cache/uv` behövas om den
vanliga cachen är skrivskyddad. `uv.lock` låser även transitiva beroenden.

## Verklig dry-run

Konfigurera miljövariabler säkert enligt [installation](docs/03-installation.md):
`ZOTERO_LIBRARY_ID`, `ZOTERO_LIBRARY_TYPE=user` (eller `group`) och
`ZOTERO_API_KEY`. `NCBI_EMAIL` rekommenderas; `NCBI_API_KEY` är valfri.
`.env` läses inte automatiskt. Ange aldrig nycklar i kommandoraden eller Git.

```bash
uv run pubmed-zotero --live --zotero --limit 5
```

Det läser biblioteket, jämför PMID/DOI och skriver en granskningsbar JSON-plan
på stdout. Inget ändras i Zotero. Utan `--zotero` får du bara PubMed-resultat.
`--limit` begränsar per sökning och rapporterar eventuell trunkering.

## Godkänd pilotimport

**Kör först efter explicit godkännande av bibliotek, urval och verklig skrivning.**
Ersätt 123456 med rätt bibliotek, inte en nyckel:

```bash
uv run pubmed-zotero --live --zotero --limit 2 --max-imports 4 \
  --apply --confirm-library 123456
```

`--apply` kräver live-källor, matchande bibliotek och explicit skrivläge.
Standardtaket är tjugo nya referenser per kategori och svensk kalenderdag. Saknas titel hoppas posten över och räknas
som `metadata_missing`. Konflikter stoppar hela planeringen före första skrivning.
Efter avbrott: kör ny dry-run. Det finns ingen automatisk återställning av redan
skapade poster och inget kommando raderar eller slår ihop referenser.

## Granskning och omkörning

Nya poster får `status/ej-granskad` i `00 – Automatisk import` och respektive
ämnessamling. Godkänn manuellt enligt [manualen](docs/09-anvandarmanual-zotero.md).
Omkörning känner igen PMID, annars DOI. Tvetydiga matchningar kräver granskning.
Titlar, egna taggar, bibliografiska metadata och privata anteckningar på befintliga
poster skrivs inte över. Godkännandestatus synkroniseras från samlingen enligt nedan. Endast appens ännu ogranskade inkorgsposter kan få
ytterligare ämnessamlingar. Proveniens sparas som separata anteckningar på
appskapade poster, en per sökning/version/query.

## Godkänn utan att ändra taggar för hand

Dra en importerad artikel till **01 – Granskade och godkända**. Vid nästa
kontroll sätts `status/godkand` och medlemskap i inkorgen och dess undersamlingar
tas bort. Kopiering/dragning räcker; du behöver inte flytta bort artikeln manuellt.
Egna projekt-/ämnessamlingar utanför inkorgen bevaras.

Kontrollen körs varje timme via Actions och vid import. GitHub kan fördröja jobb;
ändringen sker efter Zotero-synkning och nästa genomförda kontroll, inte i realtid.
Enbart appskapade referenser hanteras. Motstridiga statusar som `status/avvakta`
eller `status/exkluderad` bevaras och redovisas som konflikter. Att ta bort en
artikel ur godkänd-samlingen återställer inte status automatiskt.

## Automatisering och kontroller

GitHub Actions har manuella lägen `offline`, `dry-run` och `apply`, skyddat av
importtak och concurrency. Överskjutande träffar redovisas och kan hämtas
vid nästa körning. AI/NPH har fast historiskt startdatum 2018 och tappar därför
inte äldre poster ur ett rullande fönster. MSK behåller 14-dagars EDAT och ett eget tak på 20.
**Dagligt schema: 05:23 UTC, högst 20 nya per kategori och svensk kalenderdag.** Se
[drift](docs/07-drift-underhall.md) för Secrets, miljöskydd och senare schema.

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

## Dokumentation

- [Systemöversikt](docs/01-systemoversikt.md), [teknisk specifikation](docs/02-teknisk-specifikation.md)
- [Installation](docs/03-installation.md), [sökstrategier](docs/04-sokstrategier.md)
- [Säkerhet](docs/05-sakerhet.md), [verifieringsutfall](docs/06-validering.md)
- [Drift](docs/07-drift-underhall.md), [arkitekturbeslut](docs/08-arkitekturbeslut.md)
- [Zotero-manual](docs/09-anvandarmanual-zotero.md), [etappplan](docs/10-implementationsplan.md)
- [Retrospektiv import från 2018](docs/11-retrospektiv-import.md)
- [Ändringslogg](CHANGELOG.md)

Söksträngarna i `config/searches.yaml` är förslag som behöver klinisk granskning.
Inga patientuppgifter, automatisk evidensgradering eller PDF-nedladdning ingår.
Briefens ZIP är oförändrad. MIT föreslås som licens; ingen licens är ännu vald.
