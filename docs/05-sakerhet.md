# Säkerhet

Inga patientuppgifter får förekomma i sökningar, loggar, fixtures eller Zotero.
Referenser är publika men personliga sökintressen och bibliotek kan vara känsliga.

Nycklar anges i säker processmiljö eller GitHub Actions Secrets, aldrig i kod,
chatten eller versionshanterade filer. `.env*` ignoreras förutom namnmallen.
Autentiserade URL:er, svarskroppar och råa nätverksundantag skrivs inte ut.
E-utilities använder POST och TLS-verifiering. Proxy och CA-konfiguration behålls.
XML parsas med defusedxml; externa entiteter expanderas inte. YAML safe_load
kombineras med typkontroll. Fel stoppar körningen utan partiell JSON-rapport.

CI kör endast offline-test och behöver inga hemligheter. Behörigheten är
`contents: read`, inga privilegierade pull_request_target-jobb används.
Beroenden och Actions låses; uppdateringar ska granskas och testas.

Zotero-integrationen använder en nyckel med minsta möjliga biblioteksåtkomst.
Verklig skrivning kräver uttryckligt godkännande och CLI:s apply/biblioteksbekräftelse.
Fixtures kan inte importeras till ett verkligt bibliotek. Biblioteksversioner
förhindrar blind överskrivning vid samtidiga ändringar; redirects med nycklar följs inte. Rotera eller
återkalla komprometterad nyckel i Zotero/NCBI och ersätt den i Secrets; rensa
exponerade loggar och granska biblioteket. Att ta bort en nyckel ur senaste
commit räcker inte om den funnits i Git-historik.

Personliga bibliotek kräver Allow notes access utöver library. Appen kontrollerar
key-metadata via `/keys/current` och stoppar synkning om notes inte får läsas.
Endast booleska behörigheter behålls; nyckelvärdet i metadata skrivs aldrig ut.
Utan notes-åtkomst kan redan skapade anteckningar vara osynliga, vilket gör
omkörningskontrollen ofullständig. Skapa inga ersättningsanteckningar förrän
full läsåtkomst verifierats.

Samlingsstyrd statusändring är uttryckligen användargodkänd. Endast appskapade
referenser i godkänd-samlingen får status/godkand och lämnar inkorgsträdet;
avvakta/exkluderad och andra konflikter rapporteras utan överskrivning.
Retrospektiva datum utökar urvalet, inte behörigheten: granska antal och
batchstorlek innan stora historiska importer. Statusgrenar publicerar bara
räknare, datum/sök-ID, run-länk och källcommit, aldrig API-nycklar eller privata notes.
