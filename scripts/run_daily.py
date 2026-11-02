"""One newest-first historical/current import, within each category's daily cap."""

import json
import os
from pathlib import Path

from pubmed_zotero.budget import daily_allowances
from pubmed_zotero.config import load_searches
from pubmed_zotero.daily import discover_daily
from pubmed_zotero.pubmed import PubMedClient
from pubmed_zotero.reporting import action_summary
from pubmed_zotero.sync import apply_plan, bounded_plan
from pubmed_zotero.zotero import ZoteroClient


def execute(searches, reader, client):
    snapshot = client.snapshot()
    budget = daily_allowances(snapshot, [s.id for s in searches])
    report = discover_daily(searches, reader, snapshot, budget["remaining"])
    report["daily_budget"] = budget
    selected, plan, deferred = bounded_plan(
        report,
        searches,
        snapshot,
        sum(budget["remaining"].values()),
        newest_first=True,
        category_limits=budget["remaining"],
    )
    plan["summary"]["deferred"] = deferred
    plan["summary"]["known"] += report["known_skipped"]
    selected["sync"] = apply_plan(plan, client)
    selected["mode"] = "apply"
    selected["summary"]["imported"] = selected["sync"]["summary"]["imported"]
    # Includes server-assigned dateAdded, not local assumptions about creation time.
    after = daily_allowances(client.snapshot(), [s.id for s in searches])
    selected["daily_budget_after"] = after
    if any(value > 20 for value in after["used"].values()):
        raise RuntimeError(
            "Dagens kategoritak behöver granskas; inga fler skrivningar görs."
        )
    return selected


def run():
    if os.environ.get("APPROVED_DAILY_HISTORY") != "ai-nph-2018-newest-20-per-category":
        raise RuntimeError("Godkännande för det historiska dagliga flödet saknas.")
    searches = load_searches(Path("config/searches.yaml"))
    client = ZoteroClient(
        os.environ.get("ZOTERO_LIBRARY_ID", ""),
        os.environ.get("ZOTERO_API_KEY", ""),
        os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
        allow_writes=True,
    )
    reader = PubMedClient(
        email=os.environ.get("NCBI_EMAIL"), api_key=os.environ.get("NCBI_API_KEY")
    )
    report = execute(searches, reader, client)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if path := os.environ.get("GITHUB_OUTPUT"):
        counts = {**report["summary"], **report["sync"]["summary"]}
        stats = [
            {
                k: s[k]
                for k in (
                    "search_id",
                    "search_version",
                    "total_hits",
                    "fetched",
                    "date_type",
                    "start",
                    "end",
                )
            }
            for s in report["searches"]
        ]
        with Path(path).open("a", encoding="utf-8") as output:
            for key, value in {
                "import_summary": counts,
                "search_summary": stats,
                "daily_budget": report["daily_budget_after"],
            }.items():
                output.write(
                    key + "=" + json.dumps(value, separators=(",", ":")) + "\n"
                )
            output.write("run_mode=apply\n")
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(path).open("a", encoding="utf-8") as output:
            output.write(action_summary(report))
            output.write(
                "\nAI och NPH återfylls från 2018, nyast först. "
                "Tak: 20 per kategori och dag.\n"
            )


if __name__ == "__main__":
    run()
