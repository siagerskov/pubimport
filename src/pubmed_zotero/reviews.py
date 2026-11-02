"""User-authorized approval reconciliation, driven by collection membership."""

from copy import deepcopy

from .sync import APPROVED, INBOX, MARKER


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
            "review_updates": len(actions),
            "review_conflicts": conflicts,
            "imported": 0,
            "errors": 0,
        },
        "actions": actions,
    }
