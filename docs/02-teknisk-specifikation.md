# Teknisk specifikation

## Implementerat i 0.1

Python 3.12+, PyYAML för strikt konfigurationsvalidering och defusedxml för
XML utan entity-expansion. Standardbibliotekets urllib använder miljöns proxy
och betrodda CA; TLS-verifiering är på. Transport, klocka och väntan kan injiceras.

Bas: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`.

| Endpoint | Format | Parametrar |
|---|---|---|
| `esearch.fcgi` | JSON | db=pubmed, term, datetype=edat, mindate/maxdate, retstart, retmax≤200, sort=pub date |
| `efetch.fcgi` | XML | db=pubmed, id (högst 100 per batch), retmode=xml |

Båda använder POST för att undvika nycklar i URL-loggar. `tool=pubmed-zotero`,
valfri `NCBI_EMAIL` och `NCBI_API_KEY` skickas i formulärkroppen. Inga kroppar
eller råa undantag loggas. Högst fyra försök, 30 sekunders timeout per anrop,
minst 0,35 sekunder mellan seriella anrop. Nätfel, 429 och 5xx återförsöks med
1/2/4 sekunders backoff. Retry-After i sekunder eller HTTP-datum respekteras;
över 120 sekunders begärd paus avbryter säkert. Andra HTTP-fel avbryter direkt.
Svar större än 20 MiB avvisas. Säker XML-parsning tillåter inte entity-expansion.

ESearch hämtar alla PMID inom fönstret, eller ett explicit maxantal. 9999 är
maxgräns för okapad sökning. Inkonsekventa counts, dubbla ID:n, tomma ofullständiga
sidor och saknad EFetch-metadata avbryter i stället för att tyst ge delresultat.
NCBI kan ändras mellan sidor; körningen är inte en transaktionell snapshot.
PubmedBookArticle stöds inte ännu och leder till tydligt fel, aldrig tyst bortfall.

`Article`: PMID, nullable titel, författare (family/given/collective), tidskrift,
nullable datum, abstract och DOI. Inline-XML blir text; strukturerade abstracts
behåller etiketter. Datum behåller precision (t.ex. `2026-Nov` eller
`2026 Winter`), inga dagar fabriceras. DOI blir gemener och DOI-URL-prefix tas
bort. Länk härleds från PMID. Saknat PMID är fel; andra saknade data blir null
eller tom författarlista.

`Provenance`: sök-ID, sökversion, exakt query, söktid och upptäcktstid i UTC.
JSON innehåller körsammanfattning, datumintervall, faktisk totalmängd och explicit
trunkering. Samma PMID i flera sökningar får en artikel med flera provenienser.
Detta är steget före dubblettkontroll mot biblioteket. Discoveryrapportens
`status=discovered` beskriver upptäckten. Vid dry-run är `imported=0`; sync-delen
redovisar nya/kända och apply uppdaterar antalet bekräftade importer.

## Zotero-kontrakt i 0.2

Bas: `https://api.zotero.org/users/{id}/` eller `/groups/{id}/`.
Header `Zotero-API-Version: 3` och `Zotero-API-Key` används. Redirects följs
aldrig med nyckeln. Läsning och skrivning har 30 sekunders timeout. GET kan
återförsökas högst fyra gånger vid nätfel/429/5xx. Backoff och numerisk
Retry-After respekteras, paus över 120 sekunder ger fel i stället för långt väntande.
Skrivningar återförsöks aldrig automatiskt: resultatet kan redan vara sparat.

| Operation | Användning |
|---|---|
| GET collections | Alla samlingar, 100 per sida, Total-Results och Last-Modified-Version |
| GET items, includeTrashed=1 | Alla poster inklusive notes och papperskorg, 100 per sida |
| POST collections | En samling per request, successful/failed verifieras |
| POST items | En referens eller proveniensanteckning per request |
| PATCH items/{key} | Endast union av samlingar på appens ännu ogranskade inkorgsposter |

Samtliga sidor måste ha samma biblioteksversion och konsekvent antal utan
dubbla nycklar. Skrivning använder If-Unmodified-Since-Version från snapshot
eller senast bekräftade skrivning. HTTP 412 avbryter säkert. POST använder även
Zotero-Write-Token från payloadens SHA-256 (32 tecken). Om skrivsvaret försvinner
avbryts körningen: ny läsning krävs och inga blinda POST-retries görs.

Mappning: journalArticle; titel → title, abstract → abstractNote,
tidskrift → publicationTitle, partiellt datum → date, författare → creators,
DOI → DOI, PubMed-länk → url. PMID sparas i extra tillsammans med
`PubMed-Zotero: managed-v1`. Saknad titel skapar ingen påhittad referens.
Bibliotekets befintliga titlar, metadata, taggar och egna notes uppdateras aldrig.

Matchning: PMID från extra eller exakt PubMed-URL först, normaliserad DOI
sekundärt. Flera matchningar, olika poster för PMID/DOI eller samma DOI med
olika PMID stoppar hela planen för manuell granskning. Poster utan DOI matchas
med PMID; befintliga poster utan någon igenkännbar identifierare kan inte säkert
identifieras. Titelmatchning och automatisk sammanslagning används inte.

Proveniens sparas i separata HTML-escapade notes på appskapade poster.
En deterministisk markör per sök-ID/version/query gör dem idempotenta;
söktid och första upptäckt i den sparade anteckningen bevaras vid omkörning.
Befintliga manuella poster får inga oombedda annoteringar. Notes som användaren
raderar kan återskapas på appskapade poster. Granskade och papperskorgslagda poster
flyttas aldrig tillbaka till inkorgen; papperskorgsposter annoteras inte heller.

Planen innehåller symboliska referenser för ännu oskapade samlingar/poster.
Apply löser dessa till bekräftade Zotero-nycklar i rätt ordning. Partiellt fel
ger exitkod 1 och räknare över bekräftade importer/slutförda steg. En okänd
skrivning kan ha genomförts trots att den inte räknats som bekräftad. Det finns
ingen transaktion över hela körningen och ingen automatisk rollback.

Mockade kontrakt är verifierade; verklig API-kompatibilitet, behörighet och pilot
återstår innan produktionsklarhet kan hävdas.
