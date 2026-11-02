import importlib.util
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from test_sync import Library, inputs

from pubmed_zotero.budget import ALLOCATION_PREFIX, daily_allowances
from pubmed_zotero.daily import discover_daily
from pubmed_zotero.models import Article
from pubmed_zotero.sync import MARKER, bounded_plan
from pubmed_zotero.zotero import Snapshot, ZoteroError

NOW = datetime(2026, 11, 2, 14, tzinfo=UTC)


def saved(key, categories, added="2026-11-02T12:00:00Z", deleted=False):
    return {
        "key": key,
        "data": {
            "itemType": "journalArticle",
            "extra": MARKER + "\n" + ALLOCATION_PREFIX + ",".join(categories),
            "dateAdded": added,
            "deleted": int(deleted),
        },
    }


def test_calendar_day_and_independent_category_budgets_include_trash():
    items = [saved(f"{i:08d}", ["ai-radiology"]) for i in range(1, 21)]
    items += [
        saved("00000021", ["nph"], deleted=True),
        saved("00000022", ["nph"], "2026-11-01T23:30:00Z"),
        saved("00000023", ["nph"], "2026-11-01T22:59:00Z"),
    ]
    budget = daily_allowances(Snapshot([], items, 1), ["ai-radiology", "nph"], now=NOW)
    assert budget["used"] == {"ai-radiology": 20, "nph": 2}
    assert budget["remaining"] == {"ai-radiology": 0, "nph": 18}


def test_overlap_counts_for_both_categories_and_unknown_origin_fails_closed():
    item = saved("00000001", ["ai-radiology", "nph"])
    budget = daily_allowances(Snapshot([], [item], 1), ["ai-radiology", "nph"], now=NOW)
    assert budget["used"] == {"ai-radiology": 1, "nph": 1}
    item["data"]["extra"] = MARKER
    with pytest.raises(ZoteroError, match="Kategoriunderlag"):
        daily_allowances(Snapshot([], [item], 1), ["nph"], now=NOW)


def test_legacy_provenance_notes_supply_categories_without_changing_records():
    item = saved("00000001", [])
    item["data"]["extra"] = MARKER
    note = {
        "key": "00000002",
        "data": {
            "itemType": "note",
            "parentItem": "00000001",
            "note": "<p>PubMed-Zotero provenance v1 hash</p>"
            "<pre>{&quot;search_id&quot;: &quot;nph&quot;, "
            "&quot;searched_at&quot;: &quot;2026-11-02T11:00:00Z&quot;}</pre>",
        },
    }
    snapshot = Snapshot([], [item, note], 1)
    before = deepcopy(snapshot)
    assert daily_allowances(snapshot, ["nph"], now=NOW)["used"]["nph"] == 1
    assert snapshot == before


def entry(pmid, topic, published):
    return {
        "article": {
            "pmid": str(pmid),
            "title": str(pmid),
            "doi": None,
            "journal": None,
            "abstract": None,
            "publication_date": published,
            "authors": [],
        },
        "provenance": [
            {
                "search_id": topic,
                "search_version": "1",
                "query": "q",
                "searched_at": "now",
                "discovered_at": "now",
            }
        ],
    }


def topics():
    base = inputs()[0][0]
    return [
        replace(base, id="ai-radiology", title="AI", query="ai"),
        replace(base, id="nph", title="NPH", query="nph"),
    ]


def test_newest_first_with_independent_caps_and_overlap():
    entries = [
        entry(1, "ai-radiology", "2026-Jan-03"),
        entry(2, "ai-radiology", "2026-Jan-02"),
        entry(3, "nph", "2026-Oct-03"),
        entry(4, "nph", "2026-Oct-02"),
    ]
    shared = entry(5, "nph", "2026-Nov-01")
    shared["provenance"] += entry(5, "ai-radiology", "x")["provenance"]
    report = {"articles": entries + [shared]}
    selected, plan, _ = bounded_plan(
        report,
        topics(),
        Snapshot([], [], 0),
        4,
        newest_first=True,
        category_limits={"ai-radiology": 2, "nph": 2},
    )
    assert [e["article"]["pmid"] for e in selected["articles"]] == ["5", "3", "1"]
    assert plan["summary"]["new"] == 3
    assert all(
        "PubMed-Zotero Import Categories:" in a["data"]["extra"]
        for a in plan["actions"]
        if a["action"] == "create_item"
    )


def test_zero_allowance_category_cannot_import_via_overlapping_topic():
    shared = entry(5, "nph", "2026-Nov-01")
    shared["provenance"] += entry(5, "ai-radiology", "x")["provenance"]
    report = {"articles": [shared, entry(6, "nph", "2026-Oct-01")]}
    selected, _, _ = bounded_plan(
        report,
        topics(),
        Snapshot([], [], 0),
        2,
        newest_first=True,
        category_limits={"ai-radiology": 0, "nph": 2},
    )
    assert [e["article"]["pmid"] for e in selected["articles"]] == ["6"]


class Reader:
    def __init__(self):
        self.calls = []
        self.fetched = []

    def search(self, query, **kwargs):
        self.calls.append((query, kwargs))
        if kwargs["start"].startswith("2026"):
            return (
                [
                    str(i)
                    for i in (range(100, 125) if query == "ai" else range(200, 225))
                ],
                25,
            )
        return [], 0

    def fetch(self, ids):
        self.fetched += ids
        return [
            Article(
                pmid,
                str(pmid),
                (),
                None,
                f"2026-Oct-{int(pmid) % 100 + 1:02d}",
                None,
                None,
            )
            for pmid in ids
        ]


def test_daily_history_starts_with_latest_year_and_fetches_only_candidates():
    reader = Reader()
    report = discover_daily(
        topics(), reader, Snapshot([], [], 0), {"ai-radiology": 2, "nph": 2}, now=NOW
    )
    assert all(call[1]["start"] == "2026/01/01" for call in reader.calls)
    assert len(reader.fetched) == 20  # candidate chunks, not every ID in either source
    assert report["oldest_scanned_year"] == 2026
    assert (
        report["articles"][0]["article"]["publication_date"]
        > report["articles"][-1]["article"]["publication_date"]
    )


def test_exhausted_daily_budgets_do_not_requery_or_import():
    reader = Reader()
    report = discover_daily(
        topics(), reader, Snapshot([], [], 0), {"ai-radiology": 0, "nph": 0}, now=NOW
    )
    assert report["articles"] == [] and reader.calls == []


def test_actual_daily_runner_uses_twenty_per_category_then_imports_zero_on_repeat():
    path = Path(__file__).parents[1] / "scripts/run_daily.py"
    spec = importlib.util.spec_from_file_location("run_daily", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Freeze discovery year while keeping saved import timestamps on the real day.
    original = module.discover_daily
    module.discover_daily = lambda searches, reader, snapshot, allowances: original(
        searches, reader, snapshot, allowances, now=NOW
    )
    library = Library()
    result = module.execute(topics(), Reader(), library)
    assert result["sync"]["summary"]["imported"] == 40
    assert result["daily_budget_after"]["used"] == {"ai-radiology": 20, "nph": 20}
    again = module.execute(topics(), Reader(), library)
    assert again["sync"]["summary"]["imported"] == 0


def test_zero_category_budget_is_respected_during_cross_topic_discovery():
    class CrossReader:
        def search(self, query, **kwargs):
            return (["1"], 1) if query == "ai" else (["1", "2"], 2)

        def fetch(self, ids):
            assert ids == ["2"]
            return [Article("2", "NPH only", (), None, "2026-Nov-01", None, None)]

    report = discover_daily(
        topics(),
        CrossReader(),
        Snapshot([], [], 0),
        {"ai-radiology": 0, "nph": 1},
        now=NOW,
    )
    assert [e["article"]["pmid"] for e in report["articles"]] == ["2"]
    assert [p["search_id"] for p in report["articles"][0]["provenance"]] == ["nph"]


def test_completed_year_advances_without_refetching_known_metadata():
    item = saved("00000001", ["ai-radiology"], "2020-01-01T00:00:00Z")
    item["data"]["extra"] += "\nPMID: 1"

    class OlderReader:
        years = []

        def search(self, query, **kwargs):
            self.years.append(kwargs["start"][:4])
            return (["1"], 1) if kwargs["start"].startswith("2026") else (["2"], 1)

        def fetch(self, ids):
            assert ids == ["2"]
            return [Article("2", "Older AI", (), None, "2025-Dec-01", None, None)]

    reader = OlderReader()
    report = discover_daily(
        topics()[:1], reader, Snapshot([], [item], 1), {"ai-radiology": 1}, now=NOW
    )
    assert reader.years == ["2026", "2025"]
    assert report["oldest_scanned_year"] == 2025


def test_later_provenance_does_not_reassign_legacy_import_day_category():
    item = saved("00000001", [])
    item["data"]["extra"] = MARKER

    def note(key, category, searched):
        return {
            "key": key,
            "data": {
                "itemType": "note",
                "parentItem": "00000001",
                "note": "<p>PubMed-Zotero provenance v1 hash</p><pre>"
                + f'{{"search_id":"{category}",'
                + f'"searched_at":"{searched}"}}</pre>',
            },
        }

    initial = note("00000002", "nph", "2026-11-02T11:00:00Z")
    later = note("00000003", "ai-radiology", "2026-11-02T13:00:00Z")
    budget = daily_allowances(
        Snapshot([], [item, initial, later], 1), ["nph", "ai-radiology"], now=NOW
    )
    assert budget["used"] == {"nph": 1, "ai-radiology": 0}
