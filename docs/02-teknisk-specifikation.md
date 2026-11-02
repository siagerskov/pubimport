# Teknisk specifikation

## Verktyg och konfiguration

Python 3.12+, PyYAML safe_load med strikt fälttypkontroll och defusedxml.
uv.lock låser beroenden. HTTP använder urllib, miljöns proxy och betrodda CA;
TLS-verifiering behålls. Transport, klocka och väntan är injicerbara i tester.

Varje sökning har unikt id, title, enabled, strängversion, description, query
samt lookback_days (1–365). Query-version höjs när query ändras. Nya sökningar
läggs till i YAML; inga separata kodmoduler behövs per ämne.

## PubMed E-utilities

Bas: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/.

| Endpoint | Funktion |
|---|---|
| POST esearch.fcgi | db=pubmed, term, retmode=json, retstart, retmax≤200, datetype, mindate/maxdate, sort=pub date |
| POST efetch.fcgi | db=pubmed, id i batchar om högst 100, retmode=xml |

Valfri NCBI_EMAIL/NCBI_API_KEY skickas i formulärkroppen, aldrig loggad URL.
Timeout 30 sekunder, fyra försök, konservativ seriell pacing på 0,35 sekunder.
Timeout/nätfel/429/5xx återförsöks med begränsad backoff. Retry-After respekteras;
paus över 120 sekunder avbryter. Andra HTTP-fel avbryter direkt. Svar är
begränsade till 20 MiB; osäker XML/entity-expansion avvisas.

MSK:s dagliga EDAT-sökning använder 14 kalenderdagar inklusive dagens UTC-datum.
AI/NPH återfylls dagligen från 2018 via årsvisa PDAT-intervall, nyast först.
Retrospektivt läge använder explicita datum och normalt PDAT. Om en okapad
sökning har fler än 9999 träffar delar pipeline intervallet i två icke
överlappande datumintervall tills varje del kan hämtas. PMID dedupliceras över
delar och antal jämförs med ursprungssvaret. Oförenliga antal, saknade sidor
eller metadata stoppar körningen. Över 9999 på en enda dag kräver snävare query.
En explicit limit ger ett synligt trunkerat provurval utan full datumuppdelning.
NCBI är ingen transaktionell snapshot; förändrade resultat kan kräva omkörning.
PubmedBookArticle stöds inte och ger ett tydligt fel i stället för tyst bortfall.

## Data och proveniens

Article har PMID, nullable titel, författare (family/given/collective), tidskrift,
datum med källans precision, abstract och DOI. Inline-XML blir text och
strukturerade abstracts behåller etiketter. Saknade data fabriceras inte.
DOI normaliseras och PubMed-länk härleds från PMID. Saknat PMID är fel;
saknad titel räknas som metadata_missing och importeras inte.

Proveniens innehåller sök-ID, query-version, exakt query, UTC-söktid/upptäcktstid,
datumtyp och fönstrets start/slut. Första sparade proveniens behålls för samma
sök-ID/version/query; senare datumfönster skriver inte över den. Överlappande
bevakningar ger flera proveniensanteckningar på samma referens.

## Zotero API v3

Bas: https://api.zotero.org/users/{id}/ eller groups/{id}/. Headers:
Zotero-API-Version:3 och Zotero-API-Key. Redirects följs inte med credentials.
GET /keys/current kontrollerar rättigheter och rätt personligt bibliotek; bara
booleska library/notes/write behålls. Personliga bibliotek kräver Allow notes access.

GET collections och items (includeTrashed=1) läser 100 per sida. Samma
Last-Modified-Version och konsekvent Total-Results krävs för hela snapshoten.
POST skapar en samling/referens/note per request och successful/failed verifieras.
PATCH ändrar enbart avsiktliga tags/collections. Alla ändringar använder
If-Unmodified-Since-Version; 412 stoppar samtidiga överskrivningar. POST har
även Zotero-Write-Token. Skrivningar återförsöks aldrig blint efter oklart svar.
Ny läsning före omkörning återanvänder redan skapade referenser/notes.

journalArticle-mappning: title, creators, publicationTitle, date, abstractNote,
DOI, url och extra med PMID samt appmarkör. Notes innehåller HTML-escapad
proveniens med deterministisk markör. Användarens egna notes ersätts inte.

## Matchning, batchar och godkännande

PMID i Extra eller exakt PubMed-URL matchas först, normaliserad DOI sekundärt.
Flera träffar, olika poster för PMID/DOI eller samma DOI med olika PMID stoppar
hela planen. Ingen osäker titelmatchning eller automatisk sammanslagning görs.

Manuellt batchläge validerar hämtade kandidatposter. Dagligt flöde hämtar först
ID:n och bara nödvändiga kandidatmetadata; kända PMID/provenienser återanvänds.
Nya kandidater sorteras på publiceringsdatum och begränsas per kategori.
Tak: 20 per kategori/svenskt kalenderdygn, med debitering av alla källkategorier
för en överlappande post. dateAdded och en stabil importkategorirad används
för räkning; äldre poster använder proveniens. Överskott i urvalet blir deferred. Kända poster
bevaras. Utan --batch-imports avbryter överskridet max-imports hela planen.
Det finns ingen transaktion över hela körningen eller automatisk rollback.

review_plan behandlar även appposter utanför aktuellt PubMed-fönster. Medlemskap
i godkänd-samlingen är användarens godkännandesignal: status/godkand sätts och
inkorgsträdet tas bort. Egna taggar, andra samlingar och metadata bevaras.
Status avvakta/exkluderad/okänd lämnas orörd och räknas som review_conflicts.
Borttagning ur godkänd-samlingen ger ingen automatisk nedgradering.

## Drift och status

Import, godkännandesynk och backfill delar concurrency. Separata statusjobb har
contents:write men inga Zotero-credentials. De publicerar bara räknare, utfall,
källcommit, datum/sök-ID och run-länk till separata grenar. Fulla queries,
privata notes och credentials ingår inte i statusfilerna. Verkliga utfall ska
kontrolleras mot rätt källcommit och run_id; tester ersätter inte livevalidering.

## Godkänd återfyllnadsdrift

Användaren har godkänt båda AI och NPH från 2018, nyast först, och korrigerat
ett tidigare gemensamt tak till 20 per kategori/dag. scripts/run_daily.py
samordnar samtliga kategorier och räknar om förbrukningen efter skrivning.
Normal kodpush kör dry-run. En exakt godkänd startcommit/första attempt får
starta återfyllnaden direkt; därefter fortsätter dagligt schema. Manuella
historikjobb delar samma kategorivisa dygnsräkning och concurrency.
