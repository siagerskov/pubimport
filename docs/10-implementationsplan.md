# Implementationsplan

Aktuellt 2026-11-02: verklig läsning, godkänd import av fyra referenser och
noll återstående åtgärder för samma urval är verifierade via användarens
Actions-resultat. Notes-åtkomst är åtgärdad. Manuell Zotero-granskning och
daglig drift är nu godkänd och konfigurerad. Startutfall och första schemakörning
återstår; se 06-validering.md.

## Etapp 0 – Bootstrap

Leverera paketstruktur, projektregler, README, licensförslag, låsfil, offline-CI,
dokumentationsstruktur och kontochecklista. Acceptans: installation och verktyg
fungerar utan hemligheter. Status: implementerad, verifieringsutfall i 06.

## Etapp 1 – PubMed-läsning

Leverera validerad sökkonfiguration, ESearch/EFetch, bibliografiska modeller,
proveniens, paginering, tidsgränser och retry. Fixtures och CLI ska visa
provdata utan externa skrivningar. Acceptans: offline-kontraktstester och CLI
passerar; verklig relevans bedöms separat. Status: implementerad, utfall i 06.

## Etapp 2 – Zotero-inkorg

Implementerat i 0.2, verklig API-validering återstår: mockbar API-version-3-klient, bibliotekskonfiguration, paginerad
läsning, samlingsidentifiering, metadata-mappning och strikt dry-run. Testa payloads,
headers och fel utan riktiga nycklar. Dokumentera åtkomst och minsta behörighet.
Ingen verklig skrivning behövs för att utveckla eller testa detta.

## Etapp 3 – Idempotens

Implementerat i 0.2 och verifierat mot simulerat bibliotek.

PMID först, DOI sekundärt, explicit konfliktpolicy; överlapp och nya samlingskopplingar
utan att förlora manuella statusar. Testa omkörning, partiellt batchfel och
återupptagning med simulerat bibliotek. Full körsammanfattning och separata
proveniensanteckningar. Acceptans: alla relevanta brief-testfall offline.

## Etapp 4 – Automatisering

Manuella lägen och körinstruktioner finns i 0.2. Actions-körning återstår;
dagligt schema är avstängt.

Utöka manuellt workflow till riktig dry-run och dokumentera Secrets,
concurrency, notifieringar och kvoter. Schema förbereds men aktiveras först efter
uttryckligt godkännande. Inga hemligheter till externa PR-jobb.

## Etapp 5 – Pilot och drift

Kräver användarens beslut om bibliotek, säkert konfigurerade credentials,
granskade sökningar och uttryckligt godkännande av pilotimport. Begränsa antal,
granska poster manuellt och verifiera omkörning. Dokumentera faktiska utfall.
Separat godkännande före daglig körning. Inget steg markeras klart på grund av
enbart mockade tester.

## Automatikens start verifierad 2026-11-02

Godkänd startkörning lyckades: taggen verifierad och tio nya referenser importerade
utan fel. Statusgrenen möjliggör direkt uppföljning utan manuellt kopierade loggar.
Första schemalagda körningen återstår att observera; kapacitet för 427 uppskjutna
träffar behöver beslutas separat om full täckning inom datumfönstret önskas.
