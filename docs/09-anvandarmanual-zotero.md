# Granska referenser i Zotero

## Godkänn med en enda handling

1. Granska artikelns innehåll och metadata i inkorgen.
2. Dra artikeln till **01 – Granskade och godkända**. Vanlig dragning/kopiering
   räcker; samma referens kan ligga i flera samlingar utan att dupliceras.
3. Synkronisera Zotero. Vid nästa timkontroll eller import sätter appen
   `status/godkand`, tar bort `status/ej-granskad` och eventuell äldre stavning
   `status/godkänd`, samt tar bort medlemskap i `00 – Automatisk import` och alla
   dess undersamlingar.
4. Synkronisera igen för att se uppdateringen i programmet.

Du behöver inte ändra taggar eller tömma ämnesinkorgarna artikel för artikel.
Metadata, anteckningar, egna taggar och projekt-/ämnessamlingar utanför inkorgen
bevaras. Kontrollen gäller enbart appskapade referenser. Papperskorgen lämnas orörd.

Kontrollen körs varje timme (minut 08 UTC) och vid import. Det är inte realtid:
GitHub kan fördröja schemalagda jobb. Du kan även välja Actions → Automatic
approval tags → Run workflow för att kontrollera tidigare.

## Avvakta eller exkludera

Sätt vid behov manuellt `status/avvakta` eller `status/exkluderad` och ta bort
övriga status-taggar. Exkluderade poster bör behållas i biblioteket för att
förhindra framtida dubbelimport. Att ta bort ur samling är inte samma sak som
att radera ur biblioteket.

Om en sådan post också ligger i godkänd-samlingen ändras den inte automatiskt;
konflikten rapporteras. Rätta samlingsmedlemskapet eller statusen efter ditt beslut.
Ingen automatisk återgång till ej-granskad sker om godkänd-samlingen tas bort.

`02 – Projekt och litteraturöversikter` kan innehålla samma referenser utan kopior.
Den automatiska kontrollen ändrar inget där. Taggar filtreras i Zoteros tagglista;
PMID finns i Extra och sökproveniens i artikelns barnanteckning.
