# PubMed → Zotero

Automatisk litteraturbevakning för MSK-radiologi och AI inom radiologi med en
Zotero-inkorg för manuell granskning. **Version 0.2 implementerar synkningen och
manuell körning; verklig API-validering och godkänd pilot återstår.**

## Prova utan konton

Python 3.12+ och [uv](https://docs.astral.sh/uv/) behövs. Från repositoryroten:

```bash
uv sync --frozen
uv run pubmed-zotero --fixture tests/fixtures/pubmed.xml \
  --zotero-snapshot tests/fixtures/zotero-empty.json
```

Detta är en helt offline dry-run. Två syntetiska artiklar hittas av båda
sökningarna; planen visar fem samlingar, två referenser och fyra separata
proveniensanteckningar. **Noll externa skrivningar.** `sync.summary.new=2`,
`sync.summary.actions=11` och `imported=0`. Inga konton eller nycklar behövs.

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
Standardtaket är tio nya referenser. Saknas titel hoppas posten över och räknas
som `metadata_missing`. Konflikter stoppar hela planeringen före första skrivning.
Efter avbrott: kör ny dry-run. Det finns ingen automatisk återställning av redan
skapade poster och inget kommando raderar eller slår ihop referenser.

## Granskning och omkörning

Nya poster får `status/ej-granskad` i `00 – Automatisk import` och respektive
ämnessamling. Godkänn manuellt enligt [manualen](docs/09-anvandarmanual-zotero.md).
Omkörning känner igen PMID, annars DOI. Tvetydiga matchningar kräver granskning.
Titlar, taggar, bibliografiska metadata och privata anteckningar på befintliga
poster skrivs aldrig över. Endast appens ännu ogranskade inkorgsposter kan få
ytterligare ämnessamlingar. Proveniens sparas som separata anteckningar på
appskapade poster, en per sökning/version/query.

## Automatisering och kontroller

GitHub Actions har manuella lägen `offline`, `dry-run` och `apply`, skyddat av
importtak och concurrency. **Inget dagligt schema är aktiverat.** Se
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
- [Ändringslogg](CHANGELOG.md)

Söksträngarna i `config/searches.yaml` är förslag som behöver klinisk granskning.
Inga patientuppgifter, automatisk evidensgradering eller PDF-nedladdning ingår.
Briefens ZIP är oförändrad. MIT föreslås som licens; ingen licens är ännu vald.
