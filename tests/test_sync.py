from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from pubmed_zotero.cli import FixtureReader
from pubmed_zotero.config import load_searches
from pubmed_zotero.pipeline import discover
from pubmed_zotero.sync import ApplyError, apply_plan, plan_sync
from pubmed_zotero.zotero import Snapshot, ZoteroError

ROOT = Path(__file__).parents[1]


class Library:
    """Mutable fake server, used to exercise full re-read and recovery."""

    allow_writes = True

    def __init__(self):
        self.collections = []
        self.items = []
        self.version = 0
        self.calls = 0
        self.fail_at = None

    def snapshot(self):
        return Snapshot(deepcopy(self.collections), deepcopy(self.items), self.version)

    def create(self, kind, data):
        self.calls += 1
        if self.calls == self.fail_at:
            raise ZoteroError("simulated timeout")
        self.version += 1
        key = f"{self.version:08d}"
        record = {"key": key, "data": {**deepcopy(data), "key": key}}
        (self.collections if kind == "collections" else self.items).append(record)
        return deepcopy(record)

    def add_collections(self, item, collections):
        record = next(i for i in self.items if i["key"] == item["key"])
        record["data"]["collections"] = collections
        self.version += 1


def inputs():
    searches = load_searches(ROOT / "config/searches.yaml")
    report = discover(searches, FixtureReader(ROOT / "tests/fixtures/pubmed.xml"))
    return searches, report


def sync(library):
    searches, report = inputs()
    plan = plan_sync(report, searches, library.snapshot())
    return plan, apply_plan(plan, library)


def test_new_import_then_rerun_is_idempotent():
    library = Library()
    plan, result = sync(library)
    assert plan["summary"]["new"] == result["summary"]["imported"] == 2
    assert len(library.collections) == 5
    articles = [i for i in library.items if i["data"]["itemType"] == "journalArticle"]
    assert len(articles) == 2
    assert all(len(i["data"]["collections"]) == 3 for i in articles)
    assert len([i for i in library.items if i["data"]["itemType"] == "note"]) == 4
    before = library.snapshot()
    second, result = sync(library)
    assert second["actions"] == []
    assert result["summary"]["known"] == 2
    assert result["summary"]["imported"] == 0
    assert library.snapshot() == before


def test_preserves_manual_approval_metadata_and_notes():
    library = Library()
    sync(library)
    item = library.items[0]
    item["data"].update(
        title="Manual title",
        collections=[],
        tags=[{"tag": "status/godkand"}, {"tag": "personal"}],
    )
    library.items.append(
        {
            "key": "PERSONAL",
            "data": {
                "itemType": "note",
                "parentItem": item["key"],
                "note": "Personal note",
            },
        }
    )
    before = deepcopy(library.items)
    sync(library)
    assert library.items == before


@pytest.mark.parametrize("fail_at", [1, 6, 7, 8, 10])
def test_partial_failure_recovery_never_duplicates(fail_at):
    library = Library()
    library.fail_at = fail_at
    with pytest.raises(ApplyError) as exc:
        sync(library)
    assert exc.value.summary["errors"] == 1
    assert exc.value.summary["completed_actions"] == fail_at - 1
    library.fail_at = None
    sync(library)
    assert (
        len([i for i in library.items if i["data"]["itemType"] == "journalArticle"])
        == 2
    )
    assert len([i for i in library.items if i["data"]["itemType"] == "note"]) == 4
    assert sync(library)[0]["actions"] == []


def test_changed_search_version_adds_only_provenance():
    library = Library()
    sync(library)
    searches, _ = inputs()
    searches[0] = replace(searches[0], version=str(int(searches[0].version) + 1))
    report = discover(searches, FixtureReader(ROOT / "tests/fixtures/pubmed.xml"))
    plan = plan_sync(report, searches, library.snapshot())
    assert [a["action"] for a in plan["actions"]] == ["create_note", "create_note"]
    apply_plan(plan, library)
    assert not plan_sync(report, searches, library.snapshot())["actions"]


def test_new_topic_adds_membership_only_for_unreviewed_managed_item():
    library = Library()
    searches, report = inputs()
    first = deepcopy(report)
    for entry in first["articles"]:
        entry["provenance"] = entry["provenance"][:1]
    apply_plan(plan_sync(first, searches, library.snapshot()), library)
    plan = plan_sync(report, searches, library.snapshot())
    assert sum(a["action"] == "add_collections" for a in plan["actions"]) == 2
    apply_plan(plan, library)
    assert all(
        len(i["data"]["collections"]) == 3
        for i in library.items
        if i["data"]["itemType"] == "journalArticle"
    )


def test_doi_match_manual_item_is_never_modified():
    library = Library()
    library.items = [
        {
            "key": "MANUAL01",
            "data": {
                "itemType": "journalArticle",
                "DOI": "https://doi.org/10.0000/TEST",
                "title": "Mine",
            },
        }
    ]
    searches, report = inputs()
    report["articles"] = report["articles"][:1]
    plan = plan_sync(report, searches, library.snapshot())
    assert plan["summary"]["known"] == 1
    assert not [a for a in plan["actions"] if a["action"] != "create_collection"]


def test_identifier_conflict_blocks_whole_plan():
    library = Library()
    library.items = [
        {
            "key": "MANUAL01",
            "data": {"itemType": "journalArticle", "extra": "PMID: 10000001"},
        },
        {
            "key": "MANUAL02",
            "data": {"itemType": "journalArticle", "DOI": "10.0000/test"},
        },
    ]
    searches, report = inputs()
    with pytest.raises(ZoteroError, match="olika"):
        plan_sync(report, searches, library.snapshot())
    assert library.version == 0


def test_same_doi_different_pmid_is_explicit_conflict():
    library = Library()
    library.items = [
        {
            "key": "MANUAL01",
            "data": {
                "itemType": "journalArticle",
                "DOI": "10.0000/test",
                "extra": "PMID: 999",
            },
        }
    ]
    searches, report = inputs()
    with pytest.raises(ZoteroError, match="olika PMID"):
        plan_sync(report, searches, library.snapshot())


def test_missing_title_is_reported_without_fabrication():
    library = Library()
    searches, report = inputs()
    report["articles"][0]["article"]["title"] = None
    plan = plan_sync(report, searches, library.snapshot())
    assert plan["summary"]["metadata_missing"] == 1
    assert plan["summary"]["new"] == 1


def test_apply_requires_current_snapshot_and_write_opt_in():
    library = Library()
    searches, report = inputs()
    plan = plan_sync(report, searches, library.snapshot())
    library.version += 1
    with pytest.raises(ZoteroError):
        apply_plan(plan, library)
    library.version = 0
    library.allow_writes = False
    with pytest.raises(ZoteroError):
        apply_plan(plan, library)


def test_response_lost_after_server_commits_item_is_recovered():
    class LostResponse(Library):
        def create(self, kind, data):
            result = super().create(kind, data)
            if self.calls == 6:
                raise ZoteroError("response lost after commit")
            return result

    library = LostResponse()
    with pytest.raises(ApplyError):
        sync(library)
    assert len(library.items) == 1
    sync(library)
    assert (
        len([i for i in library.items if i["data"]["itemType"] == "journalArticle"])
        == 2
    )
    assert len([i for i in library.items if i["data"]["itemType"] == "note"]) == 4
    assert sync(library)[0]["actions"] == []


def test_trashed_reference_is_not_reimported_or_annotated():
    library = Library()
    sync(library)
    article = library.items[0]
    article["data"].update(deleted=1, collections=[])
    library.items = [
        i for i in library.items if i["data"].get("parentItem") != article["key"]
    ]
    before = deepcopy(library.items)
    sync(library)
    assert library.items == before


def test_url_only_pmid_matches_existing_reference():
    library = Library()
    library.items = [
        {
            "key": "MANUAL01",
            "data": {
                "itemType": "journalArticle",
                "url": "https://pubmed.ncbi.nlm.nih.gov/10000002/",
            },
        }
    ]
    searches, report = inputs()
    report["articles"] = report["articles"][1:]
    assert plan_sync(report, searches, library.snapshot())["summary"]["known"] == 1
