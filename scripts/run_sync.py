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
                os.environ.get("MAX_IMPORTS", "10"),
            ]
        if os.environ.get("SYNC_BATCH") == "true":
            args += [
                "--batch-imports",
                "--max-imports",
                os.environ.get("MAX_IMPORTS", "10"),
            ]
    else:
        print("Okänt synkläge.", file=sys.stderr)
        return 2
    output = io.StringIO()
    with redirect_stdout(output):
        status = main(args)
    text = output.getvalue()
    print(text, end="")
    if text.strip() and (output_path := os.environ.get("GITHUB_OUTPUT")):
        completed = json.loads(text)
        counts = completed.get("sync", {}).get("summary", completed["summary"])
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write("run_mode=" + completed["mode"] + "\n")
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
