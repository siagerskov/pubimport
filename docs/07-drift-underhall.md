# Drift och underhåll

## Manuell GitHub Actions-körning

`tests.yml` kör offline-kontroller på push/PR och manuellt. `pubmed-sync.yml`
har enbart `workflow_dispatch`, inget aktivt schema.

1. Granska och pusha koden till det valda GitHub-repositoryt.
2. Skapa environment `zotero-production` under Settings → Environments.
   Använd required reviewers där kontoplanen stöder det, särskilt för apply.
3. Lägg `ZOTERO_API_KEY` i environment Secrets. `NCBI_API_KEY` är valfri Secret.
4. Lägg `ZOTERO_LIBRARY_ID`, `ZOTERO_LIBRARY_TYPE=user` (eller group) och
   `NCBI_EMAIL` i environment Variables. Lägg aldrig nyckeln i Variables.
5. Under Actions → PubMed to Zotero → Run workflow: börja med `offline`.
6. Kör `dry-run`, limit 5, och granska JSON-planen. Detta gör ingen extern skrivning.
7. Efter uttryckligt pilotgodkännande: välj `apply`, limit 2, max_imports 4 och
   rätt ID i confirm_library. Val av apply är en verklig skrivåtgärd.
8. Kontrollera i Zotero och gör omkörning enligt installationsguiden.

Workflow har contents:read, inga tokens för push, timeout 30 minuter och
concurrency utan cancel-in-progress. Secrets används inte av PR-tester.
JSON och fel syns i körloggen; inga autentiseringsvärden skrivs ut.
En misslyckad körning ger icke-noll status. Bekräftade importer/slutförda steg
rapporteras vid partiellt fel; ett förlorat serversvar kan innebära ytterligare
sparad post. Kör alltid ny dry-run innan återförsök.

## Daglig körning – förberett, inte aktiverat

Efter verifierad pilot, godkända sökningar och separat godkännande för automatisk
drift kan `schedule` läggas under workflow-filens `on`:

```yaml
  schedule:
    - cron: '23 5 * * *'  # 05:23 UTC, ej lokal klocktid
```

Schemalagda händelser använder just nu säkert standardläge dry-run med limit 5.
För verklig daglig import behöver jobbet ge schedule-händelser `SYNC_MODE=apply`,
`SYNC_LIMIT=all`, `CONFIRM_LIBRARY` från det verifierade biblioteks-ID:t och ett
uttryckligt valt `MAX_IMPORTS`. Ändra detta först efter godkännande. Ett för litet
importtak stoppar hela planen före skrivning; välj ett rimligt tak efter pilot.
GitHub kan fördröja scheman; körningar är inte garanterade på minuten. Beakta
inaktivitetsregler, kvoter, privata repo-minuter och aktuell retention.

Sökfönstret är 14 kalenderdagar EDAT. Långt driftavbrott kan kräva granskad backfill;
MDAT-baserad uppdatering av gamla poster ingår inte. Ingen schemakonfiguration
har aktiverats av utvecklingsarbetet.

## Underhåll och återställning

Actions-historik visar fel. Aktivera GitHub-notifieringar för misslyckade körningar.
Rotera komprometterade nycklar hos Zotero/NCBI och ersätt dem i Secrets.
Uppdatera beroenden med `uv lock --upgrade`, granska diff och kör formattering,
lint, tester och build. API-förändringar kräver kontraktstester mot nya fixtures.

Git-versionera kod, sökningar och låsfil; aldrig hemligheter. Ta Zotero-export före
pilot och större manuella ändringar. Appen har ingen rollback eller destruktiv
återställning; följ Zoteros backupanvisningar vid behov. Molnmiljöns publicering
är separat och har inte utförts i detta kodarbete.
