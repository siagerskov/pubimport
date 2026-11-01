# Sökstrategier

De fullständiga körbara strängarna finns i `config/searches.yaml`, version `1`.
Båda är förslag som kräver klinisk granskning; varken relevans eller recall är
validerade mot verkliga träffar.

## MSK-radiologi

```text
("Musculoskeletal Diseases"[MeSH Terms] OR musculoskeletal[Title/Abstract])
AND ("Diagnostic Imaging"[MeSH Terms] OR radiology[Title/Abstract])
```

MeSH ger ämnesindexering, fritext fångar en del ännu oindexerade artiklar.
Sökningen är avsiktligt begränsad och kan missa organ- eller modalitetsspecifika
artiklar som inte nämner MSK. Utöka med kliniskt granskade synonymer i nästa version.

## AI inom radiologi

```text
("Artificial Intelligence"[MeSH Terms] OR "machine learning"[Title/Abstract]
OR "deep learning"[Title/Abstract])
AND ("Radiology"[MeSH Terms] OR radiology[Title/Abstract]
OR "Diagnostic Imaging"[MeSH Terms])
```

Inget tidskriftsfilter eller automatiskt kvalitetsurval. AI utan dessa begrepp kan
missas och tekniska, icke-kliniska arbeten kan inkluderas.

## Datum och utvärdering

14 kalenderdagar inklusive dagens UTC-datum används mot PubMed EDAT (entry date),
inte publiceringsdatum. Detta ger överlapp men garanterar inte att mycket sent
ändrade/indexerade poster fångas; MDAT-baserad uppdatering och större backfill är
framtida beslut. Sök-ID och query-version sparas per träff. Höj version vid
ändrad sträng och dokumentera motivering i changelog.

Provträffar nu: två syntetiska poster i `tests/fixtures/pubmed.xml`, avsiktligt
samma resultat för båda sökningarna. De visar överlapp, inte klinisk träffsäkerhet.
Verkliga träffantal och manuell bedömning återstår. Spara datum, query-version,
antal och ett granskat piloturval när en sådan validering görs.
