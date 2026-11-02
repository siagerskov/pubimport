# Projektregler

- Läs README och docs/10-implementationsplan.md före förändringar.
- Ändra aldrig beteende utan relevanta tester, dokumentation och CHANGELOG.
- Håll nätverk, klocka och väntan injicerbara; standardtester är offline.
- Kör `uv run ruff format --check .`, `uv run ruff check .` och `uv run pytest` före leverans.
- Vid ändring av sökverktyget: kör även `node web/search-builder.test.cjs` (Node 20+) och kontrollera exporterad YAML med appens konfigurationsläsare.
- Lagra eller logga aldrig hemligheter, råa HTTP-fel eller autentiserade URL:er.
- Gör inga verkliga Zotero-skrivningar, destruktiva externa åtgärder eller aktivering av schema utan uttryckligt godkännande.
- Respektera manuella statusar och användarens data. Tester får inte använda ett verkligt bibliotek.
- Redovisa antaganden, genomförda kontroller och återstående risker per etapp.
- Använd befintlig checkout i den isolerade miljön; skapa inte worktrees utan begäran.

- Godkännandesynk är uttryckligen godkänd: för appskapade poster signalerar
  medlemskap i godkänd-samlingen status/godkand och borttagning ur inkorgsträdet.
  Bevara egna taggar/metadata och rapportera avvakta/exkluderad-konflikter.

- Importtak: 20 nya per kategori och svensk kalenderdag, även över flera jobb.
  AI och NPH återfylls från 2018, nyast först. Överlapp belastar båda kategorier.
  Kontrollera sparade ursprungsdatum/kategorier; nollställ inte kvot vid omkörning.
