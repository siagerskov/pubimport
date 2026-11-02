"""User-authorized approval reconciliation, driven by collection membership."""

import html
import re
from copy import deepcopy

from .sync import APPROVED, INBOX, MARKER
from .zotero import ZoteroError

TOPICS = {
    "msk-radiology": "MSK-radiologi",
    "ai-radiology": "AI inom radiologi",
    "nph": "NPH",
}


def topic_evidence(snapshot):
    from .budget import allocation

    evidence = {}
    for item in snapshot.items:
        data = item["data"]
        if data.get("deleted"):
            continue
        if data.get("itemType") == "journalArticle":
            evidence.setdefault(item["key"], set()).update(allocation(data))
        elif data.get("itemType") == "note":
            note = data.get("note", "")
            if "PubMed-Zotero provenance v1 " in note:
                evidence.setdefault(data.get("parentItem"), set()).update(
                    re.findall(r'"search_id"\s*:\s*"([a-z0-9-]+)"', html.unescape(note))
                )
    return evidence


def collection_tree(snapshot, name):
    keys = {
        c["key"]
        for c in snapshot.collections
        if c["data"]["name"] == name and not c["data"].get("parentCollection")
    }
    while True:
        expanded = keys | {
            c["key"]
            for c in snapshot.collections
            if c["data"].get("parentCollection") in keys
        }
        if expanded == keys:
            return keys
        keys = expanded


def review_plan(snapshot):
    approved = collection_tree(snapshot, APPROVED)
    inbox = collection_tree(snapshot, INBOX)
    actions = []
    roots = [
        c["key"]
        for c in snapshot.collections
        if c["data"]["name"] == APPROVED and not c["data"].get("parentCollection")
    ]
    if len(roots) > 1:
        raise ZoteroError("Flera godkänd-samlingar; granska biblioteket.")
    evidence = topic_evidence(snapshot)
    topic_refs = {}

    def topic_ref(category):
        name = TOPICS[category]
        if category not in topic_refs:
            matches = [
                c["key"]
                for c in snapshot.collections
                if c["data"]["name"] == name
                and c["data"].get("parentCollection") == roots[0]
            ]
            if len(matches) > 1:
                raise ZoteroError("Dubbla ämnessamlingar; granska biblioteket.")
            ref = matches[0] if matches else f"approved-topic:{category}"
            if not matches:
                actions.append(
                    {
                        "action": "create_collection",
                        "ref": ref,
                        "data": {"name": name, "parentCollection": roots[0]},
                    }
                )
            topic_refs[category] = ref
        return topic_refs[category]

    conflicts = 0
    known = 0
    for item in snapshot.items:
        data = item["data"]
        if (
            data.get("itemType") != "journalArticle"
            or data.get("deleted")
            or MARKER not in data.get("extra", "").splitlines()
        ):
            continue
        known += 1
        memberships = data.get("collections", [])
        if not approved.intersection(memberships):
            continue
        statuses = {
            tag["tag"]
            for tag in data.get("tags", [])
            if tag["tag"].startswith("status/")
        }
        if statuses - {"status/godkand", "status/godkänd", "status/ej-granskad"}:
            conflicts += 1
            continue  # Preserve explicit excluded/deferred/unknown statuses.
        collections = [key for key in memberships if key not in inbox]
        for category in sorted(evidence.get(item["key"], set()) & TOPICS.keys()):
            ref = topic_ref(category)
            if ref not in collections:
                collections.append(ref)
        if statuses == {"status/godkand"}:
            tags = deepcopy(data.get("tags", []))
        else:
            tags = [
                deepcopy(tag)
                for tag in data.get("tags", [])
                if not tag["tag"].startswith("status/")
            ]
            tags.append({"tag": "status/godkand"})
        if tags != data.get("tags", []) or collections != memberships:
            actions.append(
                {
                    "action": "approve_item",
                    "item": item["key"],
                    "data": {"tags": tags, "collections": collections},
                }
            )
    return {
        "mode": "dry-run",
        "library_version": snapshot.version,
        "summary": {
            "new": 0,
            "known": known,
            "metadata_missing": 0,
            "actions": len(actions),
            "review_updates": sum(a["action"] == "approve_item" for a in actions),
            "review_conflicts": conflicts,
            "imported": 0,
            "errors": 0,
        },
        "actions": actions,
    }
