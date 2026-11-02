# Installation

## Utveckling och offline-demo

Installera Python 3.12+ och uv från officiella distributionskanaler.
Använd befintlig checkout i molnmiljön, utan extra worktree.
Från repositoryroten:

```bash
uv sync --frozen
uv run pubmed-zotero --fixture tests/fixtures/pubmed.xml \
  --zotero-snapshot tests/fixtures/zotero-empty.json
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

I molnmiljön kan `export UV_CACHE_DIR=/workspace/.cache/uv` behövas för skrivbar
cache. Inga konton eller hemligheter behövs för dessa kontroller.

## Konto och bibliotek – krävs inför verklig pilot

1. Skapa/logga in på ditt Zotero-konto och välj personligt bibliotek eller grupp.
2. På Zoteros webbplats, Settings → Feeds/API, skapa en ny privat API-nyckel.
   Ge endast åtkomst till det avsedda biblioteket. Aktivera även **Allow notes access**
   för personliga bibliotek, så att appen kan läsa proveniensanteckningar vid omkörning.
   För verklig import krävs
   skrivrättighet; börja med read-only om du vill prova enbart dry-run.
3. Notera numeriskt user ID (eller group ID för gruppbibliotek). Det är inte
   användarnamnet. `ZOTERO_LIBRARY_TYPE` är `user` eller `group`.
4. Ange `ZOTERO_API_KEY` säkert i miljöinställningar eller GitHub Secrets.
   Ange `ZOTERO_LIBRARY_ID` och `ZOTERO_LIBRARY_TYPE` som miljövariabler.
   Använd aldrig chatten, Git-filer eller kommandoradsargument för nyckeln.
5. `NCBI_EMAIL` rekommenderas för kontakt; `NCBI_API_KEY` är valfri.
   CLI laddar inte `.env` automatiskt.
6. För molnläsning måste HTTPS till `eutils.ncbi.nlm.nih.gov` och
   `api.zotero.org` tillåtas i miljöinställningarna. Befintliga proxy- och
   CA-inställningar behålls. Avstängd TLS-kontroll är inte en lösning.

Verifiera först med bara läsning:

```bash
uv run pubmed-zotero --live --zotero --limit 5
```

Granska planen, söksträngarna, antal träffar och rätt bibliotek. Höj query-version
när du ändrar sträng. Gör en separat Zotero-export som backup före pilot.

## Pilot – kräver explicit godkännande

Med rätt bibliotek och säkert konfigurerad nyckel, och först efter godkännande:

```bash
uv run pubmed-zotero --live --zotero --limit 2 --max-imports 4 \
  --apply --confirm-library 123456
```

Byt 123456 mot ditt ID. Verifiera manuellt titel, författare, DOI/PMID,
abstract, samlingar, status och proveniens. Kör samma kommando igen: inga nya
poster eller samma proveniensanteckningar ska skapas. Prova en manuell statusändring
och kontrollera att den bevaras. Dokumentera faktiska resultat i 06-validering.md.
Ingen sådan pilot har ännu genomförts.

## Felsökning

- 401/403: kontrollera nyckel, valt bibliotek och rättigheter utan att logga nyckeln.
- 412 eller ändrad snapshot: stäng samtidiga körningar, kör ny dry-run och försök igen.
- PMID/DOI-konflikt: granska dubbletter i Zotero; appen slår aldrig ihop dem.
- Avbrott/okänt skrivresultat: ny dry-run före omkörning; redan skapade poster återanvänds.
- Metadata saknas: `metadata_missing` redovisar överhoppad titel; inga falska titlar skapas.
- För många PubMed-träffar: minska datumfönster/sökning; explicit limit trunkerar synligt.
- Proxy blockerar domän: ändra tillåtna domäner via miljöinställningarna.
- Inga nya träffar: granska EDAT-fönstret; klinisk relevans och backfill är separata frågor.

Kod behöver finnas på GitHub för Actions. Lokalt skapade filer/snapshot innebär
inte att de är pushade. Granska och versionshantera ändringarna innan workflow körs.
