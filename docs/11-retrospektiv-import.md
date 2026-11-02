# Retrospektiv sökning och import från 2018

## Omfattning

AI inom bilddiagnostik (`ai-radiology`) och normaltryckshydrocefalus (`nph`)
är separata bevakningar. NPH har inget krav på bilddiagnostik eller AI.
MSK finns kvar i den löpande bevakningen men ingår inte i standardvalet för historik.

Historiskt startdatum är **2018-01-01**, inklusive. Slutdatum är dagens UTC-datum
om inget annat anges. Datumtypen är **PDAT**, publiceringsdatum. Det är ett annat
urval än den dagliga bevakningens 14-dagars EDAT (registrering i PubMed).
PDAT följer PubMeds datumtolkning, inte ett lokalt antagande om online-/tryckdatum.

## Första steget: antal och provurval utan skrivning

Actions → Retrospective PubMed search → Run workflow:

- from_date: 2018-01-01
- until_date: tomt för idag, eller ett exakt datum
- search_ids: ai-radiology,nph
- mode: dry-run
- limit: 5

Det visar verkliga totalantal men hämtar bara fem artiklar per sökning. Urvalet
är trunkerat och sorteras enligt PubMeds publiceringsdatum; det är inte fem
slumpmässiga representanter från hela perioden. Ingen historisk import görs.
Resultat kan läsas från `backfill-status:backfill-status.json` och Actions Summary.

## Full genomgång och import

Välj limit `all` för att hämta alla identifierare/metadata i intervallet. Om ett
intervall har fler än 9999 träffar delas det automatiskt i två icke överlappande
datumintervall, rekursivt vid behov. Dubbla PMID mellan delintervall slås ihop;
ändrat totalantal stoppar körningen för att undvika tyst ofullständighet. Om ett
enda datum fortfarande har över 9999 träffar krävs snävare söksträng.

Efter granskad dry-run kan mode apply och explicit biblioteks-ID användas.
`max_imports` är standard 20. Endast så många nya referenser importeras; övriga
redovisas som uppskjutna. Befintliga PMID/DOI och manuella godkännanden respekteras.
Retrospektivt urval har ett fast startdatum och tappar därför inte automatiskt
2018-poster som en rullande 14-dagarskö gör.

En stor historisk sökning kan kräva många anrop och ta lång tid, även om bara
20 nya importeras. Kör gärna år för år med fasta slutdatum. Detta är inte en
schemalagd fullständig historisk kö: efterföljande manuella batchar eller en
uttryckligt planerad historikkörning behövs för att arbeta av hela urvalet.
Den dagliga tjugobatchen fortsätter separat. Vid tusentals historiska träffar
bör antal, urval och batchstorlek beslutas innan bulkimport.

CLI från repositoryroten:

```bash
uv run pubmed-zotero --live --zotero --from-date 2018-01-01 \
  --search-id ai-radiology --search-id nph --limit 5
```

För en granskad importbatch används dessutom --apply, --confirm-library med rätt
ID, --max-imports 20 och --batch-imports. Nycklar ges alltid via säker miljö.

## Proveniens och begränsningar

Nya proveniensanteckningar innehåller datumtyp och exakt sökintervall. Befintliga
anteckningar skrivs inte över: en post hittad tidigare via samma query/version
behåller sin första proveniens. Överlapp mellan bevakningar ger flera
sökprovenienser på samma referens. Ingen PDF-hämtning eller evidensgradering görs.
AI-strategins titelkrav prioriterar precision och kan missa arbeten som bara
nämner AI/modalitet i abstract; det är ingen garanterat komplett systematisk sökning.
