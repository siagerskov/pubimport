# Retrospektiv återfyllnad från 2018 – AI och NPH

## Godkänd omfattning och dygnstak

Användaren har uttryckligen godkänt återfyllnad för **AI inom bilddiagnostik** och
**NPH**, separat, från 2018-01-01. Ordning: **nyast först**. Taket är **20 nya
referenser per kategori och svensk kalenderdag**, inte ett gemensamt tjugotak.
MSK har kvar sitt eget tak på 20 och sitt rullande 14-dagarsfönster.

En artikel som matchar både AI och NPH skapas en gång i Zotero men belastar båda
kategoriernas tak. Är ett av taken fullt väntar den överlappande nya artikeln.
Tidigare kända referenser dupliceras inte. Metadata/manuella statusar bevaras;
samlingsstyrt godkännande fungerar även för äldre importer.

## Automatisk arbetsgång

PubMed to Zotero kör dagligen 05:23 UTC. AI och NPH söker på **PDAT**, PubMeds
publiceringsdatum. Körningen börjar med innevarande år och går bakåt till 2018
när nyare material redan importerats eller inte fyller återstående kategoriutrymme.
MSK körs parallellt mot EDAT, registrering i PubMed, i 14 kalenderdagar.

Sökningarna hämtar först identifierare. Kända PMID kräver inte ny metadatahämtning
när proveniensen redan finns. Metadata hämtas i kandidatbatchar för att hitta
återstående nya referenser. Kandidater sorteras efter källans bibliografiska
publiceringsdatum; okänd dag/månad fabriceras inte. PMID används vid lika datum.
PubMeds server-sortering används för identifierarsidorna. Poster med osäker
eller ofullständig datering kan inte garanteras en exakt kronologisk inbördes ordning.

Stora datumintervall över 9999 träffar delas rekursivt i icke överlappande delar.
Oförenliga counts eller saknad metadata stoppar körningen i stället för att ge
tyst ofullständiga resultat. Fler än 9999 på en enskild dag kräver snävare query.

## En gemensam dygnsräkning per kategori

Dagen räknas i **Europe/Stockholm**, inte GitHubs UTC-dygn. Alla importvägar,
även manuella historikkörningar, räknar redan sparade appreferenser via Zoteros
dateAdded. Papperskorgsposter räknas fortfarande. Nya referenser får en stabil
kategoriangivelse i appens Extra-metadata vid skapandet. Äldre appposter utan
den markören räknas via sina proveniensanteckningar. Om datum/kategori inte kan
verifieras stoppas importen; programmet antar inte att dagens förbrukning är noll.

Manuell flytt till godkänd-samlingen påverkar inte förbrukningen. Att köra jobbet
igen ger bara dagens återstående utrymme. Fullständig permanent radering eller
manuell borttagning av appens ursprungsmetadata kan göra historisk räkning
omöjlig; gör inte det för att försöka skapa mer importutrymme.

## Manuell kontroll och avgränsad körning

Actions → Retrospective PubMed search → Run workflow:

- from_date: 2018-01-01, eller annat avgränsat startdatum.
- until_date: tomt för idag UTC, eller exakt slutdatum.
- search_ids: ai-radiology,nph (en eller båda kan väljas).
- mode: dry-run som standard; apply gör faktisk import.
- limit: 5 för provurval, all för full genomgång av valt intervall.
- max_imports: batchtak per kategori, fortfarande begränsat av återstående dygnstak 20.
- confirm_library: rätt numeriskt bibliotek vid apply.

CLI kan använda --from-date/--until-date, upprepade --search-id samt --per-category,
--newest-first och --batch-imports. Nycklar ges bara via säker miljö. Rå CLI utan
batchläge behåller sitt avbrottsskydd när urvalet inte ryms; inget läge får skapa
fler nya än dagens återstående kategoritak.

## Kartläggning och rapportering

Read-only-körning 41464377138 gav **17977 AI-träffar** och **2008 NPH-träffar**
på PDAT 2018-01-01–2026-11-02. Summan 19985 är före överlapp och befintliga poster.
Fem provposter hämtades per sökning; inga importer gjordes i den kartläggningen.

Daglig kandidatbearbetning räknar bara besökta år och granskade kandidater;
deferred är överskott i hämtat urval, inte en ny exakt totalsiffra för hela
historiken. unexamined_pmids avser ännu ej metadatahämtade ID:n i sökta år.
Äldre ännu obesökta år återstår också. Med högt nytillflöde kan återfyllnaden gå
långsamt; inget färdigdatum utlovas. Fast startår gör att äldre AI/NPH inte faller
ur en 14-dagarskö. Historiken är klar först när hela perioden kontrollerats.

Körresultat och dygnsräkning finns i automation-status/automation-status.json.
Manuell historikkörning har separat backfill-status/backfill-status.json, men
använder samma Zotero-baserade dygnsräkning. Inga nycklar eller privata notes publiceras.
