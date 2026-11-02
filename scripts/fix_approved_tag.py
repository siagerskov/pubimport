"""Explicitly approved correction of one pilot item's misspelled status tag."""

import os
from copy import deepcopy
from pathlib import Path

from pubmed_zotero.deduplication import match
from pubmed_zotero.sync import APPROVED, MARKER
from pubmed_zotero.zotero import ZoteroClient, ZoteroError

TARGET = {"pmid": "42960128", "doi": None}


def repair(client):
    snapshot = client.snapshot()
    item = match(TARGET, snapshot.items)
    if not item or MARKER not in item["data"].get("extra", "").splitlines():
        raise ZoteroError("Den godkända pilotposten kunde inte identifieras säkert.")
    approved_keys = {
        c["key"] for c in snapshot.collections if c["data"]["name"] == APPROVED
    }
    if not approved_keys.intersection(item["data"].get("collections", [])):
        raise ZoteroError(
            "Pilotposten ligger inte i godkänd-samlingen; ingen ändring görs."
        )
    tags = deepcopy(item["data"].get("tags", []))
    statuses = {t["tag"] for t in tags if t["tag"].startswith("status/")}
    if statuses - {"status/godkänd", "status/godkand"} or not statuses:
        raise ZoteroError("Statusen har ändrats; ingen tagg skrivs över.")
    changed = "status/godkänd" in statuses
    if changed:
        result = []
        for tag in tags:
            if tag["tag"] == "status/godkänd":
                if "status/godkand" in statuses:
                    continue
                tag["tag"] = "status/godkand"
            result.append(tag)
        client.update_tags(item["key"], result)
    verified = match(TARGET, client.snapshot().items)
    if not verified or {
        t["tag"]
        for t in verified["data"].get("tags", [])
        if t["tag"].startswith("status/")
    } != {"status/godkand"}:
        raise ZoteroError("Taggens slutstatus kunde inte verifieras.")
    return changed


def run():
    if os.environ.get("APPROVED_TAG_FIX") != "42960128-godkand":
        raise ZoteroError("Uttryckligt godkännande av taggrättningen saknas.")
    client = ZoteroClient(
        os.environ.get("ZOTERO_LIBRARY_ID", ""),
        os.environ.get("ZOTERO_API_KEY", ""),
        os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
        allow_writes=True,
    )
    changed = repair(client)
    message = "Pilotpostens status/godkand är verifierad. " + (
        "Taggen rättades." if changed else "Ingen ändring behövdes."
    )
    print(message)
    if path := os.environ.get("GITHUB_OUTPUT"):
        with Path(path).open("a", encoding="utf-8") as output:
            output.write("tag_fix=verified\n")
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(path).open("a", encoding="utf-8") as output:
            output.write("## Godkänd taggrättning\n\n" + message + "\n\n")


if __name__ == "__main__":
    run()
