"""Newest-first daily candidates: current MSK and AI/NPH history since 2018."""

import re
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta

from .deduplication import match, pmids
from .pipeline import search_range
from .sync import MARKER, provenance_note
from .zotero import ZoteroError

HISTORY_IDS = {"ai-radiology", "nph"}
MONTHS = {
    name: i
    for i, name in enumerate(
        [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ],
        1,
    )
}


def publication_key(entry):
    value = entry["article"].get("publication_date") or ""
    year = re.search(r"\b(\d{4})\b", value)
    rest = value[year.end() :] if year else ""
    parts = re.findall(r"[A-Za-z]+|\d+", rest)
    month = (
        MONTHS.get(parts[0][:3].lower(), 0)
        if parts and parts[0].isalpha()
        else int(parts[0])
        if parts
        else 0
    )
    day = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return (
        int(year.group(1)) if year else 0,
        month if 1 <= month <= 12 else 0,
        day if 1 <= day <= 31 else 0,
        int(entry["article"]["pmid"]),
    )


def discover_daily(searches, reader, snapshot, allowances, now=None):
    now = now or datetime.now(UTC)
    today = now.astimezone(UTC).date()
    timestamp = now.astimezone(UTC).isoformat()
    records, notes = {}, {}
    for item in snapshot.items:
        data = item["data"]
        if data.get("itemType") == "note":
            notes.setdefault(data.get("parentItem"), []).append(data.get("note", ""))
        elif data.get("itemType") == "journalArticle":
            for pmid in pmids(data):
                if pmid in records:
                    raise ZoteroError(
                        "Biblioteket har dubbla PMID; granska före import."
                    )
                records[pmid] = item
    entries, sources, known = {}, [], set()
    fetched_ids = set()

    def add(article):
        pmid = article["pmid"]
        entry = entries.setdefault(
            pmid, {"article": article, "provenance": [], "status": "discovered"}
        )
        for source in sources:
            if pmid in source["idset"] and not any(
                p["search_id"] == source["search_id"] for p in entry["provenance"]
            ):
                entry["provenance"].append(source["provenance"])

    def register(search, start, end, date_type):
        ids, total = search_range(reader, search.query, start, end, None, date_type)
        provenance = {
            "search_id": search.id,
            "search_version": search.version,
            "query": search.query,
            "searched_at": timestamp,
            "discovered_at": timestamp,
            "date_type": date_type,
            "window_start": start.strftime("%Y/%m/%d"),
            "window_end": end.strftime("%Y/%m/%d"),
        }
        source = {
            "search_id": search.id,
            "ids": ids,
            "idset": set(ids),
            "total": total,
            "provenance": provenance,
            "fetched": 0,
        }
        sources.append(source)
        for entry in list(entries.values()):
            add(entry["article"])
        for pmid in ids:
            existing = records.get(pmid)
            if not existing:
                continue
            known.add(pmid)
            data = existing["data"]
            marker, _ = provenance_note(provenance, existing["key"])
            if (
                data.get("deleted")
                or MARKER not in data.get("extra", "").splitlines()
                or any(marker in t for t in notes.get(existing["key"], []))
            ):
                continue
            add(
                {
                    "pmid": pmid,
                    "title": data.get("title"),
                    "doi": data.get("DOI"),
                    "journal": data.get("publicationTitle"),
                    "publication_date": data.get("date"),
                    "authors": [],
                    "abstract": data.get("abstractNote"),
                }
            )
        return source

    def selected_counts():
        counts = {category: 0 for category in allowances}
        for entry in sorted(entries.values(), key=publication_key, reverse=True):
            if not entry["article"]["title"] or match(entry["article"], snapshot.items):
                continue
            categories = {p["search_id"] for p in entry["provenance"]}
            if any(counts[c] >= allowances[c] for c in categories):
                continue
            for category in categories:
                counts[category] += 1
        return counts

    def fetch_candidates(source):
        category = source["search_id"]
        if allowances.get(category, 0) == 0:
            return
        unknown = [
            pmid
            for pmid in source["ids"]
            if pmid not in records
            and pmid not in fetched_ids
            and not any(
                pmid in s["idset"] and allowances.get(s["search_id"], 0) == 0
                for s in sources
            )
        ]
        chunk = max(10, min(50, allowances[category] * 2))
        while unknown and selected_counts()[category] < allowances[category]:
            batch, unknown = unknown[:chunk], unknown[chunk:]
            parsed = reader.fetch(batch)
            source["fetched"] += len(parsed)
            fetched_ids.update(batch)
            for article in parsed:
                data = asdict(article)
                if match(data, snapshot.items):
                    known.add(article.pmid)
                add(data)

    active = [search for search in searches if search.enabled]
    earliest = today.year
    if any(allowances.values()):
        current = [
            register(s, today - timedelta(days=s.lookback_days - 1), today, "edat")
            for s in active
            if s.id not in HISTORY_IDS
        ]
        for year in range(today.year, 2017, -1):
            earliest = year
            year_sources = [
                register(s, date(year, 1, 1), min(today, date(year, 12, 31)), "pdat")
                for s in active
                if s.id in HISTORY_IDS
            ]
            while True:
                before = len(fetched_ids)
                for source in current + year_sources:
                    fetch_candidates(source)
                if len(fetched_ids) == before:
                    break
            counts = selected_counts()
            if all(
                counts[s.id] >= allowances[s.id] for s in active if s.id in HISTORY_IDS
            ):
                break
    runs = [
        {
            **{
                k: s["provenance"][k]
                for k in ("search_id", "search_version", "query", "searched_at")
            },
            "date_type": s["provenance"]["date_type"],
            "start": s["provenance"]["window_start"],
            "end": s["provenance"]["window_end"],
            "total_hits": s["total"],
            "fetched": s["fetched"],
            "truncated": bool(s["idset"] - records.keys() - fetched_ids),
        }
        for s in sources
    ]
    unexamined = (
        set().union(*(s["idset"] for s in sources)) - records.keys() - fetched_ids
        if sources
        else set()
    )
    return {
        "mode": "read-only",
        "searched_at": timestamp,
        "date_mode": "daily-with-history",
        "historical_since": "2018-01-01",
        "oldest_scanned_year": earliest,
        "known_skipped": len(known - entries.keys()),
        "summary": {
            "searches": len(runs),
            "total_hits": sum(r["total_hits"] for r in runs),
            "unique_pmids": len(entries),
            "imported": 0,
            "errors": 0,
            "unexamined_pmids": len(unexamined),
            "truncated": bool(unexamined) or earliest > 2018,
        },
        "searches": runs,
        "articles": sorted(entries.values(), key=publication_key, reverse=True),
    }
