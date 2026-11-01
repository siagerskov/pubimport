# Systemöversikt

Målet är daglig PubMed-bevakning med relevanta referenser i en särskild Zotero-inkorg.
Inkorgen är inte en evidensgranskad litteraturdatabas; godkännande är alltid manuellt.

Version 0.2:

```text
Versionshanterad YAML → PubMed ESearch/EFetch → normalisering + sökproveniens
                                                         ↓
Zotero samlingar + alla poster → konsistent snapshot → PMID/DOI-matchning
                                                         ↓
                                                JSON-plan (dry-run)
                                                         ↓ explicit apply
                                     samlingar → nya poster → proveniensanteckningar
                                                         ↓
                                              manuell granskning i Zotero
```

`--fixture` och `--zotero-snapshot` ersätter nätverk med syntetiska provdata.
`--live --zotero` läser båda API:erna utan skrivning. `--apply` kräver matchande
biblioteksbekräftelse och importtak. Verklig import har inte körts under utvecklingen.

Ingen lokal databas används. Omkörningar läser biblioteket på nytt. Vid avbrott
kan redan skapade referenser kännas igen och deras saknade proveniens kompletteras.
Biblioteksversioner skyddar mot samtidiga manuella ändringar. Alla ändringar är
additiva utom en PATCH som enbart utökar samlingsmedlemskap på appskapade,
ej granskade poster som fortfarande ligger i inkorgen.

Ingen automatisk radering, sammanslagning, metadatauppdatering, statusändring,
AI-gradering eller PDF-hämtning finns. Dagligt schema aktiveras separat efter pilot.
