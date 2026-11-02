"""One approved, capped pilot; recheck the identical frozen discovery set."""

import json
import os
import sys
from pathlib import Path

from pubmed_zotero.config import ConfigurationError, load_searches
from pubmed_zotero.pipeline import discover
from pubmed_zotero.pubmed import PubMedClient, PubMedError
from pubmed_zotero.reporting import action_summary
from pubmed_zotero.sync import ApplyError, apply_plan, plan_sync
from pubmed_zotero.zotero import ZoteroClient, ZoteroError


def execute(searches, reader, zotero):
    report = discover(searches, reader, limit=2)
    if len(report["articles"]) > 4:
        raise ZoteroError("Piloten får omfatta högst fyra referenser.")
    plan = plan_sync(report, searches, zotero.snapshot())
    if plan["summary"]["new"] > 4:
        raise ZoteroError("Pilotens importtak överskreds.")
    report["mode"] = "apply"
    report["sync"] = apply_plan(plan, zotero)
    report["summary"]["imported"] = report["sync"]["summary"]["imported"]
    # No second PubMed query: the authorized set cannot expand during verification.
    repeat = plan_sync(report, searches, zotero.snapshot())
    report["repeat_check"] = repeat["summary"]
    report["pilot_verified"] = not repeat["actions"]
    if report["pilot_verified"]:
        report["repeat_apply"] = apply_plan(repeat, zotero)
    return report


def run():
    try:
        if os.environ.get("APPROVED_PILOT") != "2026-11-02-four-items":
            raise ZoteroError("Pilotgodkännande saknas.")
        searches = load_searches(Path("config/searches.yaml"))
        zotero = ZoteroClient(
            os.environ.get("ZOTERO_LIBRARY_ID", ""),
            os.environ.get("ZOTERO_API_KEY", ""),
            os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
            allow_writes=True,
        )
        reader = PubMedClient(
            email=os.environ.get("NCBI_EMAIL"), api_key=os.environ.get("NCBI_API_KEY")
        )
        report = execute(searches, reader, zotero)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if summary_path := os.environ.get("GITHUB_STEP_SUMMARY"):
            summary = action_summary(report)
            summary += "\n### Omkörningskontroll\n"
            summary += (
                "Samma artikelurval: noll ytterligare åtgärder/importer.\n"
                if report["pilot_verified"]
                else "Kontrollera resultatet. Inga ytterligare skrivningar gjordes.\n"
            )
            with Path(summary_path).open("a", encoding="utf-8") as output:
                output.write(summary)
        return 0 if report["pilot_verified"] else 1
    except ApplyError as exc:
        print(json.dumps({"summary": exc.summary}, ensure_ascii=False))
        print(str(exc), file=sys.stderr)
        return 1
    except (ConfigurationError, PubMedError, ZoteroError, OSError) as exc:
        if isinstance(exc, OSError):
            print(
                "In-/utdata misslyckades; kontrollera pilotutfallet före omkörning.",
                file=sys.stderr,
            )
        else:
            print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
