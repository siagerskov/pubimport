"""Per-category calendar-day allowances shared by all import workflows."""

import html
import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from .sync import MARKER
from .zotero import ZoteroError

TIMEZONE = ZoneInfo("Europe/Stockholm")
ALLOCATION_PREFIX = "PubMed-Zotero Import Categories: "


def allocation(data):
    for line in data.get("extra", "").splitlines():
        if line.startswith(ALLOCATION_PREFIX):
            return {
                part.strip()
                for part in line[len(ALLOCATION_PREFIX) :].split(",")
                if part.strip()
            }
    return set()


def daily_allowances(snapshot, category_ids, cap=20, now=None):
    if cap < 1:
        raise ValueError("Positive daily cap required")
    day = (now or datetime.now(UTC)).astimezone(TIMEZONE).date()
    used = {category: 0 for category in category_ids}
    legacy = {}
    for item in snapshot.items:
        data = item["data"]
        if data.get(
            "itemType"
        ) == "note" and "PubMed-Zotero provenance v1 " in data.get("note", ""):
            text = html.unescape(data["note"])
            categories = re.findall(r'"search_id"\s*:\s*"([a-z0-9-]+)"', text)
            timestamps = re.findall(r'"searched_at"\s*:\s*"([^"]+)"', text)
            if timestamps:
                try:
                    searched = datetime.fromisoformat(
                        timestamps[0].replace("Z", "+00:00")
                    )
                    if searched.tzinfo is not None:
                        legacy.setdefault(data.get("parentItem"), []).append(
                            (set(categories), searched)
                        )
                except ValueError:
                    pass
    for item in snapshot.items:
        data = item["data"]
        if (
            data.get("itemType") != "journalArticle"
            or MARKER not in data.get("extra", "").splitlines()
        ):
            continue
        try:
            added = datetime.fromisoformat(data["dateAdded"].replace("Z", "+00:00"))
            if added.tzinfo is None:
                raise ValueError
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ZoteroError(
                "En appost saknar giltigt importdatum; dagstaket kan inte verifieras."
            ) from None
        if added.astimezone(TIMEZONE).date() != day:
            continue
        categories = allocation(data)
        if not categories:
            categories = set().union(
                *(
                    ids
                    for ids, searched in legacy.get(item["key"], [])
                    if searched <= added
                )
            )
        if not categories:
            raise ZoteroError("Kategoriunderlag saknas; dagstaket kan inte verifieras.")
        for category in categories & used.keys():
            used[category] += 1
    return {
        "date": day.isoformat(),
        "timezone": "Europe/Stockholm",
        "cap_per_category": cap,
        "used": used,
        "remaining": {c: max(0, cap - count) for c, count in used.items()},
    }
