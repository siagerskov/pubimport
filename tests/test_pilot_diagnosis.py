import importlib.util
from copy import deepcopy
from pathlib import Path

from test_sync import Library, inputs, sync

from pubmed_zotero.cli import FixtureReader


def module():
    path = Path(__file__).parents[1] / "scripts/check_pilot.py"
    spec = importlib.util.spec_from_file_location("check_pilot", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    result.TARGETS = {"msk-radiology": ["10000001"], "ai-radiology": ["10000002"]}
    return result


def test_readonly_diagnosis_reports_no_work_for_complete_library():
    library = Library()
    sync(library)
    before = deepcopy(library.items)
    searches, _ = inputs()
    articles = FixtureReader(Path(__file__).parent / "fixtures/pubmed.xml").articles
    result = module().inspect(searches, articles, library.snapshot())
    assert result["summary"]["known"] == 2
    assert result["summary"]["actions"] == 0
    assert all(c["found"] and c["expected_provenance_found"] for c in result["checks"])
    assert library.items == before


def test_diagnosis_identifies_missing_note_without_repairing_it():
    library = Library()
    sync(library)
    snapshot = library.snapshot()
    note = next(i for i in snapshot.items if i["data"]["itemType"] == "note")
    snapshot.items.remove(note)
    searches, _ = inputs()
    articles = FixtureReader(Path(__file__).parent / "fixtures/pubmed.xml").articles
    before = deepcopy(snapshot.items)
    result = module().inspect(searches, articles, snapshot)
    assert result["actions_by_type"] == {"create_note": 1}
    assert result["summary"]["new"] == 0
    assert snapshot.items == before


def test_manual_review_tags_and_collections_are_checked_without_changes():
    from pubmed_zotero.sync import APPROVED

    library = Library()
    sync(library)
    approved = next(
        c["key"] for c in library.collections if c["data"]["name"] == APPROVED
    )
    for item in library.items:
        if item["data"]["itemType"] == "journalArticle":
            item["data"].update(
                tags=[{"tag": "status/godkand"}], collections=[approved]
            )
    before = deepcopy(library.items)
    searches, _ = inputs()
    articles = FixtureReader(Path(__file__).parent / "fixtures/pubmed.xml").articles
    result = module().inspect(searches, articles, library.snapshot())
    assert result["summary"]["actions"] == 0
    assert all(
        c["correct_approved_tag"] and c["in_approved_collection"] and not c["in_inbox"]
        for c in result["checks"]
    )
    assert library.items == before


def test_conflicting_status_and_remaining_subcollection_membership_are_visible():
    from pubmed_zotero.sync import INBOX

    library = Library()
    sync(library)
    inbox = next(c["key"] for c in library.collections if c["data"]["name"] == INBOX)
    for item in library.items:
        if item["data"]["itemType"] == "journalArticle":
            item["data"]["tags"] = [
                {"tag": "status/godkand"},
                {"tag": "status/ej-granskad"},
            ]
            item["data"]["collections"].remove(inbox)
    searches, _ = inputs()
    articles = FixtureReader(Path(__file__).parent / "fixtures/pubmed.xml").articles
    result = module().inspect(searches, articles, library.snapshot())
    assert all(
        not c["correct_approved_tag"] and c["in_inbox"] for c in result["checks"]
    )
