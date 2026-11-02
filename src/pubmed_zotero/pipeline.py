"""Read-only discovery pipeline; overlap is merged by PMID within this run."""

from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from .models import Article, DiscoveredArticle, Provenance, Search
from .pubmed import PubMedError, SearchLimitError


class Reader(Protocol):
    def search(
        self, query: str, *, start: str, end: str, limit: int | None = None
    ) -> tuple[list[str], int]: ...
    def fetch(self, ids: list[str]) -> list[Article]: ...


def search_range(client, query, start, end, limit, date_type):
    kwargs = {
        "start": start.strftime("%Y/%m/%d"),
        "end": end.strftime("%Y/%m/%d"),
        "limit": limit,
    }
    if date_type != "edat":
        kwargs["date_type"] = date_type
    try:
        return client.search(query, **kwargs)
    except SearchLimitError as exc:
        if start == end or limit is not None:
            raise
        midpoint = start + (end - start) // 2
        left, _ = search_range(client, query, start, midpoint, None, date_type)
        right, _ = search_range(
            client, query, midpoint + timedelta(days=1), end, None, date_type
        )
        ids = list(dict.fromkeys(left + right))
        if len(ids) != exc.count:
            raise PubMedError(
                "Träffantalet ändrades vid datumuppdelning; kör igen."
            ) from None
        return ids, len(ids)


def discover(
    searches: list[Search],
    client: Reader,
    *,
    limit: int | None = None,
    now: datetime | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    date_type: str = "edat",
) -> dict:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware timestamp required")
    now = now.astimezone(UTC)
    timestamp = now.isoformat()
    if date_type not in {"edat", "pdat"}:
        raise ValueError("Unsupported date type")
    end_day = end_date or now.date()
    if start_date and start_date > end_day:
        raise ValueError("Start after end")
    found: dict[str, DiscoveredArticle] = {}
    runs = []
    for search in searches:
        if not search.enabled:
            continue
        start_day = start_date or (end_day - timedelta(days=search.lookback_days - 1))
        start, end = start_day.strftime("%Y/%m/%d"), end_day.strftime("%Y/%m/%d")
        ids, total = search_range(
            client, search.query, start_day, end_day, limit, date_type
        )
        articles = client.fetch(ids)
        provenance = Provenance(
            search.id,
            search.version,
            search.query,
            timestamp,
            timestamp,
            date_type=date_type,
            window_start=start,
            window_end=end,
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
                "date_type": date_type,
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
        "date_mode": "retrospective" if start_date else "monitoring",
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
