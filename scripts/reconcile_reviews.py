"""Hourly approval reconciliation; does not query PubMed or import references."""

import argparse
import json
import os
from pathlib import Path

from pubmed_zotero.reviews import review_plan
from pubmed_zotero.sync import apply_plan
from pubmed_zotero.zotero import ZoteroClient


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    client = ZoteroClient(
        os.environ.get("ZOTERO_LIBRARY_ID", ""),
        os.environ.get("ZOTERO_API_KEY", ""),
        os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
        allow_writes=args.apply,
    )
    plan = review_plan(client.snapshot())
    result = apply_plan(plan, client) if args.apply else plan
    # A fresh read must no longer propose updates after a successful apply.
    if args.apply and review_plan(client.snapshot())["actions"]:
        raise RuntimeError("Godkännandestatus behöver kontrolleras efter skrivning.")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if path := os.environ.get("GITHUB_OUTPUT"):
        with Path(path).open("a", encoding="utf-8") as output:
            output.write("run_mode=" + result["mode"] + "\n")
            output.write(
                "import_summary="
                + json.dumps(result["summary"], separators=(",", ":"))
                + "\n"
            )
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        summary = result["summary"]
        with Path(path).open("a", encoding="utf-8") as output:
            output.write("## Automatisk godkännandekontroll\n\n")
            output.write(
                f"Uppdaterade: {summary.get('reviews_completed', 0)} · "
                f"Konflikter: {summary['review_conflicts']}\n\n"
            )
            output.write(
                "Inga nya referenser importerades. Godkända poster lämnar "
                "inkorgen och får status/godkand.\n"
            )


if __name__ == "__main__":
    run()
