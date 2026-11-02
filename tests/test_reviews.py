from copy import deepcopy

from test_sync import Library, inputs, sync

from pubmed_zotero.cli import FixtureReader
from pubmed_zotero.pipeline import discover
from pubmed_zotero.reviews import review_plan
from pubmed_zotero.sync import APPROVED, apply_plan, plan_sync


class ReviewLibrary(Library):
    def approve_item(self, key, data):
        item = next(i for i in self.items if i["key"] == key)
        item["data"].update(deepcopy(data))
        self.version += 1


def prepared():
    library = ReviewLibrary()
    sync(library)
    approved = next(
        c["key"] for c in library.collections if c["data"]["name"] == APPROVED
    )
    items = [i for i in library.items if i["data"]["itemType"] == "journalArticle"]
    for item in items:
        item["data"]["collections"].append(
            approved
        )  # Copy/drag, retain inbox initially.
        item["data"]["tags"].append({"tag": "my-project", "type": 0})
    return library, items, approved


def test_collection_move_approves_and_removes_inbox_without_changing_metadata():
    library, items, approved = prepared()
    metadata = [
        {
            k: deepcopy(v)
            for k, v in i["data"].items()
            if k not in {"tags", "collections"}
        }
        for i in items
    ]
    plan = review_plan(library.snapshot())
    assert plan["summary"]["review_updates"] == 2
    result = apply_plan(plan, library)
    assert result["summary"]["reviews_completed"] == 2
    for item, before in zip(items, metadata, strict=True):
        assert approved in item["data"]["collections"]
        assert len(item["data"]["collections"]) == 3
        assert item["data"]["tags"] == [
            {"tag": "my-project", "type": 0},
            {"tag": "status/godkand"},
        ]
        assert {
            k: v for k, v in item["data"].items() if k not in {"tags", "collections"}
        } == before
    assert review_plan(library.snapshot())["actions"] == []


def test_explicit_conflicting_status_is_preserved_and_reported():
    library, items, _ = prepared()
    items[0]["data"]["tags"] = [{"tag": "status/exkluderad"}]
    before = deepcopy(items[0])
    plan = review_plan(library.snapshot())
    assert plan["summary"]["review_conflicts"] == 1
    apply_plan(plan, library)
    assert items[0] == before


def test_approval_does_not_require_article_to_remain_in_pubmed_window():
    library, items, approved = prepared()
    searches, _ = inputs()
    report = {"articles": []}
    plan = plan_sync(report, searches, library.snapshot())
    assert len([a for a in plan["actions"] if a["action"] == "approve_item"]) == 2
    apply_plan(plan, library)
    assert all(approved in i["data"]["collections"] for i in items)


def test_typo_status_is_normalized_and_approved_item_never_reenters_inbox():
    library, items, approved = prepared()
    items[0]["data"]["tags"] = [{"tag": "status/godkänd"}]
    searches, _ = inputs()
    from pathlib import Path

    report = discover(
        searches, FixtureReader(Path(__file__).parent / "fixtures/pubmed.xml")
    )
    plan = plan_sync(report, searches, library.snapshot())
    assert not any(a["action"] == "add_collections" for a in plan["actions"])
    apply_plan(plan, library)
    assert items[0]["data"]["tags"] == [{"tag": "status/godkand"}]
    assert approved in items[0]["data"]["collections"]


def test_unmanaged_or_trashed_items_are_not_automatically_reviewed():
    library, items, _ = prepared()
    items[0]["data"]["extra"] = "PMID: 10000001"
    items[1]["data"]["deleted"] = 1
    before = deepcopy(library.items)
    assert review_plan(library.snapshot())["actions"] == []
    assert library.items == before


def test_hourly_runner_produces_valid_status_outputs(monkeypatch, tmp_path):
    import importlib.util
    import sys
    from pathlib import Path

    library, _, _ = prepared()
    path = Path(__file__).parents[1] / "scripts/reconcile_reviews.py"
    spec = importlib.util.spec_from_file_location("reconcile_reviews", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ZoteroClient", lambda *a, **kw: library)
    monkeypatch.setattr(sys, "argv", [str(path), "--apply"])
    output = tmp_path / "outputs"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    module.run()
    import json

    lines = output.read_text().splitlines()
    assert lines[0] == "run_mode=apply"
    assert json.loads(lines[1].split("=", 1)[1])["reviews_completed"] == 2


def test_legacy_provenance_sorts_already_approved_and_preserves_project():
    from pubmed_zotero.sync import MARKER

    library, items, approved = prepared()
    project = library.create(
        "collections", {"name": "Mitt projekt", "parentCollection": False}
    )["key"]
    for item in items:
        item["data"].update(
            extra=MARKER,
            tags=[{"tag": "status/godkand"}],
            collections=[approved, project],
        )
    apply_plan(review_plan(library.snapshot()), library)
    for item in items:
        assert project in item["data"]["collections"]
        assert len(item["data"]["collections"]) == 4
    assert not review_plan(library.snapshot())["actions"]


def test_missing_topic_evidence_does_not_guess_from_title():
    from pubmed_zotero.sync import MARKER

    library, items, approved = prepared()
    library.items = items
    for item in items:
        item["data"].update(
            extra=MARKER, tags=[{"tag": "status/godkand"}], collections=[approved]
        )
    assert not review_plan(library.snapshot())["actions"]


def test_nph_allocation_and_recovery_after_partial_write():
    import pytest

    from pubmed_zotero.sync import MARKER, ApplyError

    library, items, approved = prepared()
    library.items = items
    for item in items:
        item["data"].update(
            extra=MARKER + "\nPubMed-Zotero Import Categories: nph",
            tags=[{"tag": "status/godkand"}],
            collections=[approved],
        )
    original = library.approve_item
    from pubmed_zotero.zotero import ZoteroError

    def fail(*args):
        raise ZoteroError("simulated")

    library.approve_item = fail
    with pytest.raises(ApplyError):
        apply_plan(review_plan(library.snapshot()), library)
    library.approve_item = original
    apply_plan(review_plan(library.snapshot()), library)
    assert len([c for c in library.collections if c["data"]["name"] == "NPH"]) == 1
    assert not review_plan(library.snapshot())["actions"]
