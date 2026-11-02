"""Read-only diagnosis of the four actually imported pilot references."""

import json
import os
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from pubmed_zotero.config import load_searches
from pubmed_zotero.deduplication import match
from pubmed_zotero.pubmed import PubMedClient
from pubmed_zotero.sync import MARKER, plan_sync, provenance_note
from pubmed_zotero.zotero import ZoteroClient

TARGETS = {
    "msk-radiology": ["42960128", "42959815"],
    "ai-radiology": ["42959533", "42936410"],
}


def inspect(searches, articles, snapshot):
    now = datetime.now(UTC).isoformat()
    by_id = {a.pmid: a for a in articles}
    entries = []
    for search in searches:
        for pmid in TARGETS.get(search.id, []):
            entries.append(
                {
                    "article": asdict(by_id[pmid]),
                    "provenance": [
                        {
                            "search_id": search.id,
                            "search_version": search.version,
                            "query": search.query,
                            "searched_at": now,
                            "discovered_at": now,
                        }
                    ],
                }
            )
    report = {"articles": entries}
    plan = plan_sync(report, searches, snapshot)
    checks = []
    for entry in entries:
        existing = match(entry["article"], snapshot.items)
        row = {"pmid": entry["article"]["pmid"], "found": existing is not None}
        if existing:
            notes = [
                i
                for i in snapshot.items
                if i["data"].get("parentItem") == existing["key"]
                and i["data"]["itemType"] == "note"
            ]
            marker, _ = provenance_note(entry["provenance"][0], existing["key"])
            row.update(
                managed=MARKER in existing["data"].get("extra", "").splitlines(),
                child_notes=len(notes),
                expected_provenance_found=any(
                    marker in i["data"].get("note", "") for i in notes
                ),
            )
        checks.append(row)
    return {
        "summary": plan["summary"],
        "actions_by_type": dict(Counter(a["action"] for a in plan["actions"])),
        "checks": checks,
        "planned_actions": plan["actions"],
    }


def run():
    searches = load_searches(Path("config/searches.yaml"))
    reader = PubMedClient(
        email=os.environ.get("NCBI_EMAIL"), api_key=os.environ.get("NCBI_API_KEY")
    )
    articles = reader.fetch([pmid for ids in TARGETS.values() for pmid in ids])
    client = ZoteroClient(
        os.environ.get("ZOTERO_LIBRARY_ID", ""),
        os.environ.get("ZOTERO_API_KEY", ""),
        os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
        allow_writes=False,
    )
    permissions = client.permissions()
    if not permissions["library"] or not permissions["notes"]:
        result = {
            "key_permissions": permissions,
            "diagnosis": "Läsbehörighet saknas. Ingen reparation görs.",
        }
    else:
        result = inspect(searches, articles, client.snapshot())
        result["key_permissions"] = permissions
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        summary = "## Pilotdiagnos – enbart läsning\n\n"
        summary += (
            "```json\n"
            + json.dumps(
                {k: v for k, v in result.items() if k != "planned_actions"},
                ensure_ascii=False,
                indent=2,
            )
            + "\n```\n"
        )
        summary += (
            "\nInga nya referenser eller anteckningar har skapats av kontrollen.\n"
        )
        with Path(path).open("a", encoding="utf-8") as output:
            output.write(summary)


if __name__ == "__main__":
    run()
