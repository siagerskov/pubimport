# Sökstrategier och nya bevakningar

## Aktuella separata bevakningar

Användaren har valt NPH separat och AI inom bilddiagnostik separat. MSK ligger
kvar sedan tidigare. Sökningarna är arbetsförslag som kräver fortlöpande
relevansgranskning; de är inte validerade systematiska litteratursökningar.

### MSK-radiologi – `msk-radiology`, version 4

```text
("Musculoskeletal Diseases"[MeSH Terms] OR musculoskeletal[Title/Abstract] OR bone[Title/Abstract] OR joint[Title/Abstract] OR tendon*[Title/Abstract] OR ligament*[Title/Abstract] OR cartilage[Title/Abstract] OR menisc*[Title/Abstract] OR spine[Title/Abstract] OR spinal[Title/Abstract] OR knee[Title/Abstract] OR hip[Title/Abstract] OR shoulder[Title/Abstract] OR ankle[Title/Abstract]) AND (radiolog*[Title] OR MRI[Title] OR "MR imaging"[Title] OR "magnetic resonance imaging"[Title] OR CT[Title] OR "computed tomography"[Title] OR radiograph*[Title] OR ultrasound[Title] OR ultrasonograph*[Title])
```

Användarens MSK-sökning version 4; använd i verifierad pilot. Precision och relevans behöver fortsatt följas.

### AI inom radiologi – `ai-radiology`, version 3

```text
("artificial intelligence"[Title] OR "machine learning"[Title] OR "deep learning"[Title] OR "neural network"[Title] OR "neural networks"[Title] OR "AI-based"[Title] OR "AI-driven"[Title]) AND (radiolog*[Title] OR MRI[Title] OR "MR imaging"[Title] OR "magnetic resonance imaging"[Title] OR CT[Title] OR "computed tomography"[Title] OR radiograph*[Title] OR ultrasound[Title] OR ultrasonograph*[Title] OR fluoroscop*[Title] OR tomosynthesis[Title])
```

Förslag med högre precision för pilot: radiologisk modalitet i titeln. Lägre recall förväntas; klinisk granskning återstår.

### NPH – `nph`, version 1

```text
("Hydrocephalus, Normal Pressure"[MeSH Terms] OR "normal pressure hydrocephalus"[Title/Abstract] OR "normal-pressure hydrocephalus"[Title/Abstract] OR iNPH[Title/Abstract] OR (NPH[Title/Abstract] AND hydrocephalus[Title/Abstract]))
```

Separat bevakning av normaltryckshydrocefalus utan bilddiagnostiskt filter; användarens omfattning 2026-11-02.

## Tolkning och begränsningar

MSK och AI-strategierna kräver radiologisk modalitet i titel för högre precision.
AI kräver dessutom uttryckliga AI/ML/DL-begrepp i titel. Det kan missa relevanta
arbeten där metoden enbart framgår av abstract, liksom andra diagnostiska
modaliteter. Ingen automatisk evidensgradering eller tidskriftsbegränsning görs.
NPH omfattar även klinik, gång/kognition, shuntbehandling och prognos; inget
bilddiagnostiskt eller AI-filter används. NPH ensamt kräver hydrocephalus-kontext
för att minska andra betydelser av förkortningen.

En referens kan matcha både AI och NPH men får en Zotero-post med rätt
ämnesmedlemskap och flera provenienser. Förklaringar till tidigare query-versioner
och observerade provträffar finns i CHANGELOG och 06-validering.md.

## Lägg till fler sökningar

1. Öppna den senaste web/search-builder.html i webbläsaren.
2. Välj Ny bevakning, ge ett namn och ett unikt stabilt ID.
3. Bygg av söktermer eller klistra in en fullständig query i avancerat läge.
   Ändringar direkt i PubMed/MeSH-sidan förs inte automatiskt tillbaka till verktyget;
   kopiera den färdiga strängen tillbaka innan export.
4. Prova i PubMed och granska relevans. Ange om termer ska sökas i titel eller abstract.
5. Exportera searches.yaml. Filen innehåller alla bevakningar, inte bara den valda.
6. Dela filen i utvecklingschatten eller inför den som config/searches.yaml via Git.
   Validering/test och read-only-körning ska göras före fortsatt import.

ID ska behållas när en befintlig bevakning justeras; höj query-version vid ändrad
query. Verktyget gör versionshöjning från sin basversion och lägger till nya
medföljande bevakningar vid inläsning av äldre lokala utkast utan att kasta egna
queryändringar. En gammal nedladdad HTML-fil behöver ersättas med senaste versionen.

## Datum

MSK-bevakning: 14 kalenderdagar inklusive idag UTC på EDAT, när posten
registrerats i PubMed. AI och NPH använder nu fast start 2018 och PDAT även
i dagliga återfyllnadsjobbet, med nyaste kandidater först.
Retrospektivt: 2018-01-01 till vald slutdag på PDAT, publiceringsdatum enligt
PubMed. Resultatantal från dessa datumtyper kan inte direkt jämföras.
Se 11-retrospektiv-import.md för intervall, provurval och granskad import.
