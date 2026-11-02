# Sökstrategier

De fullständiga körbara strängarna finns i `config/searches.yaml`, version `3`.
De är förslag, inte kliniskt validerade slutliga strategier.

## Verklig dry-run 2026-11-02, version 1

Användarens Actions-logg från körning 41438100545 visar 130 MSK-träffar och
189 AI-träffar under EDAT 2026-10-20–2026-11-02. Fem hämtades per sökning:
nio unika PMID, inga metadatafel, nio nya poster och noll importer.
Urvalet är trunkerat och visar inte relevansen för hela träffmängden.
Bland titelträffarna fanns mangopuréspektroskopi och fluorescerande prober;
ämnesprecisionen var otillräcklig för en oövervakad import.

## Version 2: snävare förslag

Det breda exploderande MeSH-begreppet Diagnostic Imaging är borttaget från
båda sökningarna. I stället krävs något av de uttryckliga modalitetsbegreppen
radiologi, MRI, CT, radiografi eller ultraljud i titel/abstract eller MeSH.
Radiology/Radiography/Ultrasonography använder noexp för att begränsa automatiska
MeSH-undergrenar. MRI- och CT-MeSH får fortfarande sina relevanta undergrenar.

MSK-delen kombinerar Musculoskeletal Diseases/System med fritext för bland annat
ben, leder, senor, ligament, brosk, menisk och ryggrad. AI-delen kräver AI-MeSH
eller explicita begrepp för artificial intelligence/machine learning/deep learning.
Fullständiga queries i YAML är den enda körbara källan och versionshanteras ihop
med denna dokumentation. Inget tidskriftsfilter eller evidensurval införs.

Version 2 behöver en ny verklig dry-run och klinisk bedömning. Den garanterar
inte att irrelevanta arbeten försvinner: modaliteter kan användas i prekliniska
studier och breda anatomiska ord kan ge falska träffar. Samtidigt kan artiklar om
andra modaliteter eller utan explicita termer missas. Ingen retrospektiv titel-
eller MeSH-granskning av alla 319 träffar har genomförts.

## Datum och proveniens

14 kalenderdagar inklusive dagens UTC-datum används mot EDAT, inte publiceringsdatum.
Överlappet garanterar inte att mycket sent ändrade poster fångas; MDAT/backfill
är separata framtida beslut. Sök-ID, exakt query och version sparas per träff.
Proveniens från version 1 skrivs inte över när version 2 används.

Syntetiska fixtures visar tekniskt överlapp, inte relevans. Dokumentera verkliga
träffantal och granskade exempel när varje query-version utvärderas.

## Verklig dry-run version 2 och nästa förslag

Körning 41438795739, 2026-11-02: 954 MSK-träffar och 570 AI-träffar,
fem hämtade per sökning, tio unika PMID, tio nya, noll importer/metadatafel.
Provurvalet innehöll fortfarande irrelevanta titlar, bland annat NMR-spektra
för geografiskt ursprung av Lycium barbarum och gliomacellsbiologi.
Version 2 blev bredare än avsett när fler anatomibegrepp lades till.
Den kliniska precisionen förbättrades inte tillräckligt.

Version 3 är ett uttryckligen mer specifikt pilotförslag: radiologisk modalitet
måste nämnas i titeln (radiologi, MRI/MR imaging, magnetic resonance imaging, CT,
computed tomography, radiografi, ultraljud, fluoroskopi eller tomosyntes).
Det generella uttrycket magnetic resonance och modalitets-MeSH används inte
längre som alternativ. MSK-delen behåller anatomisk fritext/ämnesindexering,
men AI-delen kräver explicita AI/ML/DL-begrepp i titeln. Detta kan missa relevanta
arbeten där AI eller modalitet bara framgår av abstract/indexering. Det är ett
medvetet precisionsförslag för pilot, inte en komplett litteratursökningsstrategi.
Verklig relevans och träffantal för version 3 återstår att granska.
