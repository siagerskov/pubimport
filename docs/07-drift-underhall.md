# Drift och underhåll

## Automatisk import – godkänd 2026-11-02

Användaren godkände rättning av den sista pilot-taggen och hela det automatiska
flödet. `pubmed-sync.yml` kör nu varje dag **05:23 UTC**. Det motsvarar 06:23
svensk vintertid och 07:23 sommartid. GitHub kan fördröja schemalagda körningar;
ingen exakt leveranstid garanteras.

Varje schemalagd körning hämtar hela det konfigurerade 14-dagars EDAT-fönstret,
läser Zotero inklusive anteckningar och papperskorg och importerar **högst tjugo
nya referenser totalt**. Tillgängliga platser fördelas växelvis mellan sökningarna.
Nya referenser får status/ej-granskad och rätt ämnessamling under inkorgen.
Befintliga metadata bevaras. Status ändras enbart genom den användargodkända
samlingsstyrda godkännanderegeln som beskrivs nedan.

Hela urvalets identifierarkonflikter kontrolleras innan en delmängd väljs.
Överskjutande nya referenser redovisas som `deferred`/Uppskjutna av importtak.
De kan komma med vid senare körningar så länge de ligger kvar i EDAT-fönstret.
**Det finns ingen beständig kö:** om inflödet överstiger tjugo per dag, eller ett
långt driftavbrott inträffar, kan äldre ej importerade träffar falla ur fönstret.
Granska uppskjutna antal; kör fler manuella batchar eller ändra tak/fönster vid
behov. Appen hävdar inte fullständig litteraturbevakning under en växande kö.

`contents: read`, timeout 30 minuter och concurrency utan avbrott av pågående jobb
används. Körmiljön är Ubuntu 24.04; checkout/setup-python är låsta till officiella
v6-commits. Secrets lämnas inte till externa pull requests.

## Start och riktad taggrättning

Den uttryckligt godkända startpushen rättar bara taggen på PMID 42960128 från
status/godkänd till status/godkand. Den kräver att posten är appskapad, ligger i
godkänd-samlingen och saknar andra motstridiga statusar. Övriga taggar, metadata,
notes och samlingar bevaras; biblioteksversionen skyddar mot samtidiga ändringar.
Resultatet läses tillbaka. Rättningen kan bara köras på den exakta godkända
startcommitten och första run_attempt, aldrig på dagligt schema.

Samma startkörning gör en första begränsad fullfönsterimport med tiotak.
Framtida vanliga kodpushar kör **dry-run**, inte apply. Startkörningen är observerad och lyckades; den första tidstyrda körningen
ska observeras separat. Tekniska tester ersätter inte verkliga körresultat.

## Manuell körning och stopp

Actions → PubMed to Zotero → Run workflow:

- `offline`: syntetisk demonstration utan nätverk eller nycklar.
- `dry-run`: läser API:erna, skriver bara plan; säkert standardval.
- `apply`: import till explicit bekräftat bibliotek. Sätt confirm_library till
  rätt numeriskt ID. Limit `all` söker hela fönstret; positiv siffra begränsar
  antal hämtade per sökning. max_imports styr batchens globala tak, standard tjugo.

För extra ikappkörning: välj apply, limit all, max_imports 20 och bekräftat ID.
Inga redan kända referenser ska skapas igen. Normal CLI utan --batch-imports
behåller tidigare skydd: överskridet --max-imports avbryter hela planen.

Pausa automatiseringen via Actions → PubMed to Zotero → meny → Disable workflow.
Det raderar inget i Zotero. Återaktivera först efter felsökning. Vid behov kan
schedule tas bort ur workflowfilen i en granskad commit.

## Behörigheter, loggar och felsökning

Environment zotero-production eller repositoryinställningarna ska ge:

- Secret ZOTERO_API_KEY och valfri NCBI_API_KEY.
- Variables ZOTERO_LIBRARY_ID, ZOTERO_LIBRARY_TYPE (user/group), NCBI_EMAIL.
- Biblioteksåtkomst, notes-åtkomst för personligt bibliotek och skrivrättighet.

Appen verifierar rättigheterna innan synkning. Nycklar skrivs aldrig ut.
Summary visar antal, uppskjutna poster, query-versioner och titlar i körplanen.
Detaljerad JSON och sanerade fel finns i loggen. Aktivera GitHub-notifieringar
för misslyckade Actions-körningar i kontots notifieringsinställningar.

Vid 412/samtidig ändring eller okänt skrivresultat: ny dry-run före återförsök.
POST återförsöks aldrig blint. Redan skapade poster och proveniens läses tillbaka.
Identifierarkonflikter kräver manuell granskning; ingen automatisk sammanslagning
eller rollback görs. Ett feljobb betyder inte att inga tidigare steg hann sparas.

## Underhåll och backup

Versionshantera kod, sökningar och låsfil; aldrig nycklar. Uppdatera beroenden
med uv lock --upgrade och kör formattering, lint, tester och build. API-ändringar
kräver uppdaterade kontraktstester, inte avstängd verifiering.
Ta Zotero-export före större ändringar. Följ Zoteros återställningsanvisningar;
appen gör ingen destruktiv återställning. Beakta aktuella GitHub-kvoter,
schemainaktivitet och loggretention. Molnmiljöns publicering är separat från
kodpush och har inte utförts av detta arbete.

## Maskinläsbar körstatus

Efter sync-jobbet sparar ett separat jobb `automation-status.json` på grenen
`automation-status`. Den innehåller enbart kör-ID/länk, källcommit, utfall,
körläge, heltalsräknare och status för engångsrättningen. Inga titlar, notes,
biblioteksdata eller nycklar publiceras. Sync-jobbet har fortsatt contents:read;
endast statusjobbet har contents:write och får inte Zotero-nyckeln.
Statusgrenen startar inte appimport eftersom push-triggern bara gäller main.
En felande statuspublicering ändrar inte utfallet av redan utförda Zotero-steg.
Kontrollera alltid källcommit och run_id för att undvika att läsa en gammal status.

## Automatisk status efter samlingsändring – godkänd 2026-11-02

`review-status.yml` kör varje timme, minut 08 UTC, och kan startas manuellt.
Appens importerade referenser i godkänd-samlingen (inklusive dess undersamlingar)
får status/godkand och lämnar inkorgsträdet. Egna taggar och övriga fält bevaras.
Explicit avvakta/exkluderad/okänd status stoppar ändring för posten och räknas
som review_conflicts. Ingen automatisk nedgradering görs om samlingen tas bort.
Samma policy används vid import, även för poster utanför PubMed-datumfönstret.

Godkännande-PATCH innehåller enbart tags och collections med biblioteksversionens
konkurrensskydd. Kontrolljobbet importerar aldrig nya referenser och delar
concurrency med importen. Separat säker status finns på grenen review-status,
i review-status.json. Det ändrar inte den dagliga importens automation-status.
Statusjobbet har repository-skrivrättighet men saknar Zotero-nyckel.

## Fler bevakningar och retrospektiv import

För nya sökningar används web/search-builder.html och config/searches.yaml.
Aktuella separata bevakningar är MSK, AI inom bilddiagnostik och NPH. En ny query
behöver inget nytt workflow; dess samling identifieras/skapas vid import.
Daglig bevakning använder fortfarande EDAT och ett gemensamt tjugotak.

Retrospective PubMed search använder separat PDAT-intervall från 2018 och egna
sök-ID:n; se 11-retrospektiv-import.md. Standardläget är dry-run. Faktisk återfyllnad föreslås börja med NPH,
publiceringsår 2018 och högst 20 nya, men behöver uttryckligt batchgodkännande.
Vanliga pushar startar ingen historisk import. Retrospektiv status ligger i
backfill-status/backfill-status.json.
