"""Read-only discovery pipeline; overlap is merged by PMID within this run."""

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from typing import Protocol

from .models import Article, DiscoveredArticle, Provenance, Search


class Reader(Protocol):
    def search(
        self, query: str, *, start: str, end: str, limit: int | None = None
    ) -> tuple[list[str], int]: ...
    def fetch(self, ids: list[str]) -> list[Article]: ...


def discover(
    searches: list[Search],
    client: Reader,
    *,
    limit: int | None = None,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware timestamp required")
    now = now.astimezone(UTC)
    timestamp = now.isoformat()
    found: dict[str, DiscoveredArticle] = {}
    runs = []
    for search in searches:
        if not search.enabled:
            continue
        start = (now.date() - timedelta(days=search.lookback_days - 1)).strftime(
            "%Y/%m/%d"
        )
        end = now.strftime("%Y/%m/%d")
        ids, total = client.search(search.query, start=start, end=end, limit=limit)
        articles = client.fetch(ids)
        provenance = Provenance(
            search.id, search.version, search.query, timestamp, timestamp
        )
        for article in articles:
            entry = found.setdefault(article.pmid, DiscoveredArticle(article))
            entry.provenance.append(provenance)
        runs.append(
            {
                "search_id": search.id,
                "search_version": search.version,
                "query": search.query,
                "searched_at": timestamp,
                "date_type": "edat",
                "start": start,
                "end": end,
                "total_hits": total,
                "fetched": len(articles),
                "truncated": len(ids) < total,
            }
        )
    return {
        "mode": "read-only",
        "searched_at": timestamp,
        "summary": {
            "searches": len(runs),
            "total_hits": sum(r["total_hits"] for r in runs),
            "unique_pmids": len(found),
            "imported": 0,
            "errors": 0,
            "truncated": any(r["truncated"] for r in runs),
        },
        "searches": runs,
        "articles": [
            {**asdict(entry), "url": entry.article.url} for entry in found.values()
        ],
    }
