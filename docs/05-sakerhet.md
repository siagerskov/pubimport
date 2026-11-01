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
