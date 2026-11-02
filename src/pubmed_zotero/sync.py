"""Reviewable sync plans and conservative apply, preserving manual edits."""

import hashlib
import html
import json
from copy import deepcopy

from .deduplication import match, normalize_doi
from .zotero import Snapshot, ZoteroError, validate_records

MARKER = "PubMed-Zotero: managed-v1"
INBOX = "00 – Automatisk import"
APPROVED = "01 – Granskade och godkända"
PROJECTS = "02 – Projekt och litteraturöversikter"


def item_payload(article, collections, categories=()):
    creators = []
    for author in article["authors"]:
        if author["collective"]:
            creators.append({"creatorType": "author", "name": author["collective"]})
        elif author["family"] or author["given"]:
            creators.append(
                {
                    "creatorType": "author",
                    "lastName": author["family"] or "",
                    "firstName": author["given"] or "",
                }
            )
    return {
        "itemType": "journalArticle",
        "title": article["title"],
        "creators": creators,
        "publicationTitle": article["journal"] or "",
        "date": article["publication_date"] or "",
        "abstractNote": article["abstract"] or "",
        "DOI": normalize_doi(article["doi"] or ""),
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/",
        "extra": f"PMID: {article['pmid']}\n{MARKER}"
        + (
            "\nPubMed-Zotero Import Categories: " + ",".join(sorted(set(categories)))
            if categories
            else ""
        ),
        "collections": collections,
        "tags": [{"tag": "status/ej-granskad"}],
    }


def provenance_note(provenance, parent):
    # Stable identity: repeated query versions create no new note.
    identity = {k: provenance[k] for k in ("search_id", "search_version", "query")}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    marker = f"PubMed-Zotero provenance v1 {digest}"
    content = html.escape(json.dumps(provenance, ensure_ascii=False, sort_keys=True))
    return marker, {
        "itemType": "note",
        "parentItem": parent,
        "note": f"<p>{marker}</p><pre>{content}</pre>",
        "tags": [],
    }


def plan_sync(discovery, searches, snapshot: Snapshot):
    validate_records(snapshot.collections, "collections")
    validate_records(snapshot.items, "items")
    actions = []
    collection_refs = {}
    for name, parent in [(INBOX, False), (APPROVED, False), (PROJECTS, False)] + [
        (search.title, INBOX) for search in searches if search.enabled
    ]:
        ref = f"collection:{parent}:{name}"
        parent_key = False if parent is False else collection_refs[parent]
        matches = [
            c
            for c in snapshot.collections
            if c["data"]["name"] == name
            and c["data"].get("parentCollection", False) == parent_key
        ]
        if len(matches) > 1:
            raise ZoteroError(
                "Flera samlingar med samma namn och förälder; granska biblioteket."
            )
        key = matches[0]["key"] if matches else ref
        if not matches and ref not in {a["ref"] for a in actions if "ref" in a}:
            actions.append(
                {
                    "action": "create_collection",
                    "ref": ref,
                    "data": {"name": name, "parentCollection": parent_key},
                }
            )
        if parent is False:
            collection_refs[name] = key
        else:
            collection_refs[f"{parent}/{name}"] = key
    titles = {s.id: s.title for s in searches}
    # Local import avoids a module cycle while keeping the approval policy separate.
    from .reviews import review_plan

    items = deepcopy(snapshot.items)
    reviews = review_plan(snapshot)
    actions.extend(reviews["actions"])
    by_key = {item["key"]: item for item in items}
    for action in reviews["actions"]:
        by_key[action["item"]]["data"].update(deepcopy(action["data"]))
    stats = {
        "new": 0,
        "known": 0,
        "metadata_missing": 0,
        "review_updates": reviews["summary"]["review_updates"],
        "review_conflicts": reviews["summary"]["review_conflicts"],
    }
    for entry in discovery["articles"]:
        article = entry["article"]
        existing = match(article, items)
        desired = [collection_refs[INBOX]] + [
            collection_refs[f"{INBOX}/{titles[p['search_id']]}"]
            for p in entry["provenance"]
        ]
        desired = list(dict.fromkeys(desired))
        if existing:
            stats["known"] += 1
            data = existing["data"]
            if data.get("deleted"):
                continue  # A deliberate move to trash must not trigger re-import.
            # Never change existing titles, metadata, tags, or personal notes.
            managed = MARKER in data.get("extra", "").splitlines()
            statuses = {
                tag["tag"]
                for tag in data.get("tags", [])
                if tag["tag"].startswith("status/")
            }
            if (
                managed
                and statuses == {"status/ej-granskad"}
                and collection_refs[INBOX] in data.get("collections", [])
            ):
                merged = list(dict.fromkeys(data.get("collections", []) + desired))
                if merged != data.get("collections", []):
                    actions.append(
                        {
                            "action": "add_collections",
                            "item": existing["key"],
                            "collections": merged,
                        }
                    )
                    data["collections"] = merged
            if not managed:
                continue  # No unsolicited annotations on manually entered items.
            parent = existing["key"]
        else:
            if not article["title"]:
                stats["metadata_missing"] += 1
                continue
            stats["new"] += 1
            parent = f"item:{article['pmid']}"
            payload = item_payload(
                article, desired, [p["search_id"] for p in entry["provenance"]]
            )
            actions.append({"action": "create_item", "ref": parent, "data": payload})
            items.append({"key": parent, "data": payload})
        for provenance in entry["provenance"]:
            marker, note = provenance_note(provenance, parent)
            if any(
                i["data"].get("parentItem") == parent
                and marker in i["data"].get("note", "")
                for i in items
            ):
                continue
            actions.append({"action": "create_note", "data": note})
            items.append({"key": "planned-note", "data": note})
    return {
        "mode": "dry-run",
        "library_version": snapshot.version,
        "summary": {**stats, "actions": len(actions), "imported": 0, "errors": 0},
        "actions": actions,
    }


class ApplyError(ZoteroError):
    def __init__(self, summary):
        super().__init__(
            "Synkningen avbröts. Vissa steg kan vara klara; kör ny dry-run."
        )
        self.summary = summary


def apply_plan(plan, client):
    if not client.allow_writes or client.version != plan["library_version"]:
        raise ZoteroError("Apply kräver skrivläge och samma lästa biblioteksversion.")
    resolved = {}
    summary = {**plan["summary"], "completed_actions": 0, "reviews_completed": 0}

    def resolve(value):
        if isinstance(value, str):
            return resolved.get(value, value)
        if isinstance(value, list):
            return [resolve(v) for v in value]
        if isinstance(value, dict):
            return {k: resolve(v) for k, v in value.items()}
        return value

    try:
        for action in plan["actions"]:
            if action["action"] == "approve_item":
                client.approve_item(action["item"], action["data"])
                summary["reviews_completed"] += 1
            elif action["action"] == "add_collections":
                client.add_collections(
                    {"key": resolve(action["item"])}, resolve(action["collections"])
                )
            else:
                kind = (
                    "collections"
                    if action["action"] == "create_collection"
                    else "items"
                )
                record = client.create(kind, resolve(action["data"]))
                if "ref" in action:
                    resolved[action["ref"]] = record["key"]
                if action["action"] == "create_item":
                    summary["imported"] += 1
            summary["completed_actions"] += 1
    except ZoteroError:
        summary["errors"] = 1
        raise ApplyError(summary) from None
    return {"mode": "apply", "summary": summary}


def bounded_plan(
    report, searches, snapshot, maximum, *, newest_first=False, category_limits=None
):
    """Validate the full set, then fairly select at most maximum new references."""
    if maximum < 0:
        raise ValueError("Nonnegative import allowance required")
    if newest_first:
        from .daily import publication_key

        report = {
            **report,
            "articles": sorted(report["articles"], key=publication_key, reverse=True),
        }
    full = plan_sync(report, searches, snapshot)
    if category_limits is None and full["summary"]["new"] <= maximum:
        return report, full, 0
    buckets = {}
    included = set()
    for entry in report["articles"]:
        article = entry["article"]
        if match(article, snapshot.items) or not article["title"]:
            included.add(article["pmid"])
        else:
            topic = entry["provenance"][0]["search_id"]
            buckets.setdefault(topic, []).append(article["pmid"])
    selected = 0
    remaining = dict(category_limits) if category_limits is not None else None
    if newest_first or remaining is not None:
        for entry in report["articles"]:
            pmid = entry["article"]["pmid"]
            if pmid not in included and selected < maximum:
                categories = {p["search_id"] for p in entry["provenance"]}
                if remaining is not None and any(
                    remaining.get(c, 0) < 1 for c in categories
                ):
                    continue
                included.add(pmid)
                selected += 1
                if remaining is not None:
                    for category in categories:
                        remaining[category] -= 1
    while (
        not newest_first
        and remaining is None
        and selected < maximum
        and any(buckets.values())
    ):
        for bucket in buckets.values():
            if bucket and selected < maximum:
                included.add(bucket.pop(0))
                selected += 1
    limited = {
        **report,
        "articles": [e for e in report["articles"] if e["article"]["pmid"] in included],
    }
    plan = plan_sync(limited, searches, snapshot)
    deferred = full["summary"]["new"] - plan["summary"]["new"]
    return limited, plan, deferred
