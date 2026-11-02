import importlib.util
from pathlib import Path

from test_sync import Library, inputs

from pubmed_zotero.cli import FixtureReader


def pilot_module():
    path = Path(__file__).parents[1] / "scripts/pilot.py"
    spec = importlib.util.spec_from_file_location("pilot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pilot_freezes_input_and_verifies_zero_repeat_writes():
    class Once(FixtureReader):
        calls = 0

        def search(self, *args, **kwargs):
            self.calls += 1
            assert (
                self.calls <= 2
            )  # Two configured searches, never re-query during repeat.
            return super().search(*args, **kwargs)

    searches, _ = inputs()
    reader = Once(Path(__file__).parent / "fixtures/pubmed.xml")
    library = Library()
    report = pilot_module().execute(searches, reader, library)
    assert report["summary"]["imported"] == 2
    assert report["pilot_verified"] is True
    assert report["repeat_check"]["new"] == 0
    assert report["repeat_check"]["actions"] == 0
    assert report["repeat_apply"]["summary"]["imported"] == 0
    assert reader.calls == 2


def test_pilot_requires_explicit_approval_marker(monkeypatch):
    monkeypatch.delenv("APPROVED_PILOT", raising=False)
    assert pilot_module().run() == 1


def test_repeat_verification_never_writes_a_nonempty_second_plan():
    class InconsistentRead(Library):
        reads = 0

        def snapshot(self):
            snapshot = super().snapshot()
            self.reads += 1
            if self.reads == 2:
                snapshot.items = [
                    i for i in snapshot.items if i["data"]["itemType"] != "note"
                ]
            return snapshot

    searches, _ = inputs()
    library = InconsistentRead()
    reader = FixtureReader(Path(__file__).parent / "fixtures/pubmed.xml")
    report = pilot_module().execute(searches, reader, library)
    assert report["pilot_verified"] is False
    assert "repeat_apply" not in report
    assert len([i for i in library.items if i["data"]["itemType"] == "note"]) == 4
