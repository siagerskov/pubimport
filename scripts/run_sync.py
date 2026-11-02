"""Shared manual/scheduled Actions runner; inputs are never evaluated by a shell."""

import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

from pubmed_zotero.cli import main
from pubmed_zotero.reporting import action_summary


def run():
    mode = os.environ.get("SYNC_MODE", "dry-run")
    args = ["--config", "config/searches.yaml"]
    if mode == "offline":
        args += [
            "--fixture",
            "tests/fixtures/pubmed.xml",
            "--zotero-snapshot",
            "tests/fixtures/zotero-empty.json",
        ]
    elif mode in {"dry-run", "apply"}:
        args += ["--live", "--zotero"]
        limit = os.environ.get("SYNC_LIMIT", "5")
        if limit != "all":
            args += ["--limit", limit]
        if mode == "apply":
            args += [
                "--apply",
                "--confirm-library",
                os.environ.get("CONFIRM_LIBRARY", ""),
                "--max-imports",
                os.environ.get("MAX_IMPORTS", "20"),
            ]
        if os.environ.get("SYNC_BATCH") == "true":
            args += [
                "--batch-imports",
                "--max-imports",
                os.environ.get("MAX_IMPORTS", "20"),
            ]
    else:
        print("Okänt synkläge.", file=sys.stderr)
        return 2
    if mode != "offline":
        if from_date := os.environ.get("SYNC_FROM_DATE"):
            args += ["--from-date", from_date]
        if until_date := os.environ.get("SYNC_UNTIL_DATE"):
            args += ["--until-date", until_date]
        for search_id in os.environ.get("SYNC_SEARCH_IDS", "").split(","):
            if search_id.strip():
                args += ["--search-id", search_id.strip()]
    output = io.StringIO()
    with redirect_stdout(output):
        status = main(args)
    text = output.getvalue()
    print(text, end="")
    if text.strip() and (output_path := os.environ.get("GITHUB_OUTPUT")):
        completed = json.loads(text)
        counts = {
            **completed["summary"],
            **completed.get("sync", {}).get("summary", {}),
        }
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write("run_mode=" + completed["mode"] + "\n")
            search_stats = [
                {
                    k: row[k]
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
                for row in completed.get("searches", [])
            ]
            output.write(
                "search_summary="
                + json.dumps(search_stats, separators=(",", ":"))
                + "\n"
            )
            output.write(
                "import_summary=" + json.dumps(counts, separators=(",", ":")) + "\n"
            )
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path and status == 0:
        report = json.loads(text)
        with Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write(action_summary(report))
    return status


if __name__ == "__main__":
    raise SystemExit(run())
