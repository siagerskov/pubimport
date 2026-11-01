# Manuellt arbetsflöde i Zotero

Version 0.2 skapar dessa samlingar vid godkänd apply. Dry-run visar bara planen.
Ingen verklig import har ännu verifierats.

1. Ny import ska hamna i `00 – Automatisk import`, ämnesundersamlingarna
   `MSK-radiologi`/`AI inom radiologi`, och ha `status/ej-granskad`.
2. Vid godkännande: ta bort övriga status-taggar, sätt `status/godkand`, lägg samma
   post i `01 – Granskade och godkända` och ta bort dess inkorgsmedlemskap.
3. Vid avvaktan: sätt enbart `status/avvakta` och behåll i inkorgen.
4. Vid exkludering: sätt enbart `status/exkluderad`, ta bort från inkorgen men
   behåll posten i biblioteket så att framtida körningar känner igen den.
5. `02 – Projekt och litteraturöversikter` kan innehålla samma godkända poster.

Samlingar är medlemskap, inte kopior. Välj ta bort ur samling, inte radera ur
biblioteket. Använd taggfiltret för status och kontrollera att varje post har
exakt en status-tagg. Sök på titel/DOI/PMID för att hitta poster. Automatiken ska
respektera dessa val och aldrig återställa en granskad post till ej granskad.
Det beteendet är verifierat med simulerat bibliotek; kontrollera det också i piloten.
