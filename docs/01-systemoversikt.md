# Systemöversikt

Appen bevakar PubMed och importerar nya referenser till en Zotero-inkorg för
manuell granskning. Tre separata bevakningar finns: MSK-radiologi, AI inom
bilddiagnostik och NPH (normaltryckshydrocefalus utan radiologiskt filter).
En referens kan matcha flera bevakningar utan att dupliceras.

```text
Versionshanterad YAML → PubMed ESearch/EFetch → metadata + proveniens
                                                        ↓
Zotero bibliotek + notes → konsistent snapshot → PMID/DOI-kontroll
                                                        ↓
                                     dry-run eller begränsad import
                                                        ↓
                              00 – Automatisk import / ämnessamlingar
                                                        ↓ användaren godkänner
                              01 – Granskade och godkända
                                                        ↓ timkontroll
                              status/godkand + borttagning ur inkorgsträdet
```

Daglig körning: 05:23 UTC, 14-dagars EDAT-fönster och högst **20 nya referenser
per körning**. Timkontroll: minut 08 UTC, inga nya referenser. GitHub kan fördröja
körningar. En manuell retrospektiv sökning använder PDAT-publiceringsdatum från
2018-01-01; den ändrar inte den dagliga bevakningens datumfönster.

Det fristående sökverktyget bygger queries och exporterar searches.yaml utan
credentials eller server. GitHub Actions håller API-nycklar i Secrets. Diagnostik
och små statusfiler gör utfall läsbara via Git utan att exponera nycklar/notes.

Stateless innebär att Zotero läses på nytt före ändringar. Ingen lokal databas
eller beständig importkö krävs. Överskott i rullande datumfönster kan falla ur
fönstret om kapaciteten är för liten; historisk import behöver planeras separat.

Automatiken ändrar inte befintlig bibliografisk metadata eller egna anteckningar.
Det användargodkända undantaget för status är samlingsstyrt godkännande på
appskapade poster. Andra manuella statusar, papperskorg och personliga taggar skyddas.
Ingen automatisk radering, sammanslagning, PDF-hämtning eller AI-evidensgradering finns.
Verifierade utfall och återstående begränsningar finns i 06-validering.md.
