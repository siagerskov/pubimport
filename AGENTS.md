# Projektregler

- Läs README och docs/10-implementationsplan.md före förändringar.
- Ändra aldrig beteende utan relevanta tester, dokumentation och CHANGELOG.
- Håll nätverk, klocka och väntan injicerbara; standardtester är offline.
- Kör `uv run ruff format --check .`, `uv run ruff check .` och `uv run pytest` före leverans.
- Lagra eller logga aldrig hemligheter, råa HTTP-fel eller autentiserade URL:er.
- Gör inga verkliga Zotero-skrivningar, destruktiva externa åtgärder eller aktivering av schema utan uttryckligt godkännande.
- Respektera manuella statusar och användarens data. Tester får inte använda ett verkligt bibliotek.
- Redovisa antaganden, genomförda kontroller och återstående risker per etapp.
- Använd befintlig checkout i den isolerade miljön; skapa inte worktrees utan begäran.
