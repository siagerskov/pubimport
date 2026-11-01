"""Shared manual/scheduled Actions runner; inputs are never evaluated by a shell."""

import os
import sys

from pubmed_zotero.cli import main


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
    else:
        print("Okänt synkläge.", file=sys.stderr)
        return 2
    return main(args)


if __name__ == "__main__":
    raise SystemExit(run())
