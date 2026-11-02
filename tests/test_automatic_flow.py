import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest
from test_sync import Library, inputs, sync

from pubmed_zotero.cli import FixtureReader, main
from pubmed_zotero.sync import APPROVED, apply_plan, bounded_plan
from pubmed_zotero.zotero import ZoteroError

ROOT = Path(__file__).parents[1]


def test_daily_batch_defers_excess_and_catches_up_without_duplicates(
    monkeypatch, capsys
):
    library = Library()
    monkeypatch.setenv("ZOTERO_LIBRARY_ID", "123")
    monkeypatch.setattr(
        "pubmed_zotero.cli.PubMedClient",
        lambda **kw: FixtureReader(ROOT / "tests/fixtures/pubmed.xml"),
    )
    monkeypatch.setattr("pubmed_zotero.cli.ZoteroClient", lambda *a, **kw: library)
    args = [
        "--config",
        str(ROOT / "config/searches.yaml"),
        "--live",
        "--zotero",
        "--apply",
        "--confirm-library",
        "123",
        "--max-imports",
        "1",
        "--batch-imports",
    ]
    for imported, deferred in [(1, 1), (1, 0), (0, 0)]:
        assert main(args) == 0
        report = json.loads(capsys.readouterr().out)
        assert report["sync"]["summary"]["imported"] == imported
        assert report["sync"]["summary"]["deferred"] == deferred
    assert (
        len([i for i in library.items if i["data"]["itemType"] == "journalArticle"])
        == 2
    )


def test_batch_splits_slots_between_topics():
    searches, report = inputs()
    base = report["articles"][0]
    entries = []
    for topic in range(2):
        for n in range(3):
            entry = deepcopy(base)
            entry["article"].update(pmid=str(100 + topic * 10 + n), doi=None)
            entry["provenance"] = [base["provenance"][topic]]
            entries.append(entry)
    report["articles"] = entries
    library = Library()
    selected, plan, deferred = bounded_plan(report, searches, library.snapshot(), 2)
    assert {e["article"]["pmid"] for e in selected["articles"]} == {"100", "110"}
    assert deferred == 4
    assert apply_plan(plan, library)["summary"]["imported"] == 2


def tag_module():
    spec = importlib.util.spec_from_file_location(
        "fix_tag", ROOT / "scripts/fix_approved_tag.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.TARGET = {"pmid": "10000001", "doi": None}
    return module


class TagLibrary(Library):
    tag_writes = 0

    def update_tags(self, key, tags):
        self.tag_writes += 1
        item = next(i for i in self.items if i["key"] == key)
        item["data"]["tags"] = deepcopy(tags)
        self.version += 1


def approved_library():
    library = TagLibrary()
    sync(library)
    approved = next(
        c["key"] for c in library.collections if c["data"]["name"] == APPROVED
    )
    item = next(i for i in library.items if "10000001" in i["data"].get("extra", ""))
    item["data"].update(
        collections=[approved],
        tags=[{"tag": "status/godkänd"}, {"tag": "personal", "type": 0}],
    )
    return library, item


def test_one_approved_tag_fix_preserves_every_other_field_and_is_repeatable():
    library, item = approved_library()
    before = deepcopy(item["data"])
    assert tag_module().repair(library) is True
    assert item["data"]["tags"] == [
        {"tag": "status/godkand"},
        {"tag": "personal", "type": 0},
    ]
    assert {k: v for k, v in item["data"].items() if k != "tags"} == {
        k: v for k, v in before.items() if k != "tags"
    }
    assert tag_module().repair(library) is False
    assert library.tag_writes == 1


def test_changed_status_prevents_approved_fix_from_overwriting_user():
    library, item = approved_library()
    item["data"]["tags"] = [{"tag": "status/exkluderad"}]
    with pytest.raises(ZoteroError, match="Statusen"):
        tag_module().repair(library)
    assert library.tag_writes == 0
