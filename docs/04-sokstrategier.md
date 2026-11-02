# Sökstrategier

De fullständiga körbara strängarna finns i `config/searches.yaml`, MSK version `4` och AI version `3`.
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

## Bygg egna sökningar utan kod

`web/search-builder.html` är ett fristående formulär för termgrupper och färdiga
PubMed-queries. En term/fras per rad; OR inom grupp, AND mellan ämne och metod,
valfri NOT mot titel/abstract. Avancerad syntax används endast i query-läget.
Ord/fraselement citeras i term-läget; hur trunkering och fraser tolkas måste
kontrolleras i PubMeds Search Details efter provkörning. Ingen lokal simulering
påstår sig kunna validera PubMeds kliniska relevans eller kompletta querysyntax.

Exporten använder JSON-citerade YAML-strängar, booleskt enabled, unika stabila ID:n,
1–365 dagars fönster och query-version. Den kan läsas av appens befintliga validator.
Utkast lagras enbart efter ett uttryckligt klick i den lokala webbläsaren. Export
och provlänk aktiverar ingen import; införande av YAML och pilot är separata steg.

## MSK version 4 – användarens query, 2026-11-02

Användaren lämnade den fullständiga MSK-strängen direkt i chatten. Den är införd
exakt, med samma parenteser och fälttaggar. Jämfört med version 3 är enbart
`fluoroscop*[Title]` och `tomosynthesis[Title]` borttagna från MSK:s modalitetsgrupp.
AI-sökningen ligger kvar på version 3. Sökverktygets inbyggda grundförslag är
synkroniserade; ett tidigare lokalt sparat webbläsarutkast kan fortfarande ha
äldre innehåll och kan raderas med Radera lokalt utkast följt av omladdning.
Relevans bedöms i kommande dry-run. Detta innebär inget godkännande av import.

Användaren rapporterade 32 träffar vid sin manuella PubMed-sökning. Exakt
datumfilter och söktid för den jämförelsen är inte fastställda; antalet ska
inte direkt likställas med appens 14-dagars EDAT-resultat.
