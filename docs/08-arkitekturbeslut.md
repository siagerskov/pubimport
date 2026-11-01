# Arkitekturbeslut

## ADR 001 – Stegvis läsning före import (2026-11-01)

Val: leverera etapp 0–1 först med explicit offline/live-läsning. Alternativ:
komplett import direkt. Skäl: testa metadata, sökningar och fel utan att röra ett
bibliotek. Konsekvens: inget påstående om färdig MVP eller drift.

## ADR 002 – Stateless och isolerad transport (2026-11-01)

Val: ingen lokal databas, dataclasses och injicerad urllib-transport/klocka/väntan.
Alternativ: beständig cache och större HTTP-ramverk. Skäl: mindre driftbehov,
små beroenden, snabba offline-tester. Konsekvens: upptäcktstid gäller per körning;
bibliotekets tillstånd måste läsas före senare import.

## ADR 003 – Versionslåsning och säkra parserbibliotek (2026-11-01)

Val: uv.lock, PyYAML safe_load med strikt schema och defusedxml. Alternativ:
egen YAML-parser eller osäkrad XML. Skäl: reproducerbar installation och robust
hantering av externa data. Konsekvens: beroenden måste uppdateras med tester.

## ADR 004 – EDAT och tydliga gränser (2026-11-01)

Val: 14 kalenderdagar EDAT, synlig trunkering vid användarvald limit och fel vid
överskriden okapad 9999-gräns. Alternativ: tyst första sida. Skäl: användaren ska
kunna bedöma fullständighet. Konsekvens: äldre backfill och sent ändrade poster
kräver fortsatt design; sökningen är inte kliniskt validerad.

## ADR 005 – Licensförslag (2026-11-01)

MIT föreslås för enkel återanvändning. Ingen licens aktiveras innan ägaren valt.

## ADR 006 – Försiktig synkning och återhämtning (2026-11-01)

Val: konsistent snapshot, biblioteksversionsskydd och en skrivning åt gången.
Oklara skrivsvar återförsöks inte automatiskt. Ny läsning hittar redan skapade
PMID/DOI och kompletterar saknade proveniensanteckningar. Alternativ: blinda
batch-retries eller lokal databas. Konsekvens: fler API-anrop men tydliga
återhämtningssteg, inget löfte om transaktionell rollback.

## ADR 007 – Respektera manuella data (2026-11-01)

Val: befintlig metadata och status skrivs aldrig över. Enbart appens ännu
ogranskade inkorgsposter kan få nya ämneskopplingar; proveniens skapas i separata
notes. Tvetydiga PMID/DOI-matchningar stoppar planen; ingen titelbaserad sammanslagning.
Papperskorgen läses också så att borttagna referenser inte oavsiktligt återimporteras.
Konsekvens: konflikt kräver manuell granskning, metadatauppdatering är separat framtida arbete.
