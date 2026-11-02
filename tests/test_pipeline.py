import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from pubmed_zotero.cli import FixtureReader, main
from pubmed_zotero.config import ConfigurationError, load_searches
from pubmed_zotero.pipeline import discover

ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "config/searches.yaml"
FIXTURE = ROOT / "tests/fixtures/pubmed.xml"


def test_overlap_provenance_dates_and_no_imports():
    searches = load_searches(CONFIG)
    report = discover(
        searches, FixtureReader(FIXTURE), now=datetime(2026, 11, 1, tzinfo=UTC)
    )
    assert report["summary"] == {
        "searches": 2,
        "total_hits": 4,
        "unique_pmids": 2,
        "imported": 0,
        "errors": 0,
        "truncated": False,
    }
    assert report["searches"][0]["start"] == "2026/10/19"
    assert report["searches"][0]["end"] == "2026/11/01"
    for entry in report["articles"]:
        assert len(entry["provenance"]) == 2
        assert entry["status"] == "discovered"
        assert entry["provenance"][1]["search_version"] == "3"
        assert entry["provenance"][0]["discovered_at"].endswith("+00:00")


def test_disabled_version_and_limit():
    searches = load_searches(CONFIG)
    next_version = str(int(searches[0].version) + 1)
    searches = [
        replace(searches[0], version=next_version),
        replace(searches[1], enabled=False),
    ]
    report = discover(searches, FixtureReader(FIXTURE), limit=1)
    assert report["summary"]["searches"] == 1
    assert report["summary"]["truncated"] is True
    assert report["articles"][0]["provenance"][0]["search_version"] == next_version


def test_cli_offline_report(capsys, monkeypatch):
    def no_network(*a, **kw):
        raise AssertionError("Network must not be used")

    monkeypatch.setattr("pubmed_zotero.cli.PubMedClient", no_network)
    assert main(["--config", str(CONFIG), "--fixture", str(FIXTURE)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["source"] == "synthetic-fixture"
    assert report["summary"]["unique_pmids"] == 2


def test_cli_failure_has_no_partial_output(tmp_path, capsys):
    broken = tmp_path / "bad.xml"
    broken.write_text("<ERROR>SECRET</ERROR>")
    assert main(["--config", str(CONFIG), "--fixture", str(broken)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "SECRET" not in captured.err


@pytest.mark.parametrize(
    "mutation",
    [
        lambda rows: rows.append(rows[0].copy()),
        lambda rows: rows[0].update(enabled="false"),
        lambda rows: rows[0].update(lookback_days=True),
        lambda rows: rows[0].update(lookback_days=0),
        lambda rows: rows[0].update(version=1),
        lambda rows: rows[0].update(query=" "),
        lambda rows: rows[0].update(id="bad/id"),
        lambda rows: rows[0].update(unknown="value"),
    ],
)
def test_config_rejects_ambiguous_input(tmp_path, mutation):
    data = yaml.safe_load(CONFIG.read_text())
    mutation(data["searches"])
    path = tmp_path / "searches.yaml"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ConfigurationError):
        load_searches(path)


@pytest.mark.parametrize("value", ["", "searches: []", "searches: null", "[]", "x: ["])
def test_config_rejects_invalid_document(tmp_path, value):
    path = tmp_path / "bad.yaml"
    path.write_text(value)
    with pytest.raises(ConfigurationError):
        load_searches(path)


def test_live_cli_failure_does_not_emit_partial_json(capsys, monkeypatch):
    from pubmed_zotero.pubmed import PubMedError

    class FailingReader(FixtureReader):
        def __init__(self, **kwargs):
            super().__init__(FIXTURE)
            self.search_calls = 0

        def search(self, *args, **kwargs):
            self.search_calls += 1
            if self.search_calls == 2:
                raise PubMedError("PubMed kunde inte nås efter begränsade återförsök.")
            return super().search(*args, **kwargs)

    monkeypatch.setattr("pubmed_zotero.cli.PubMedClient", FailingReader)
    assert main(["--config", str(CONFIG), "--live"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "återförsök" in captured.err


def test_cli_zotero_offline_dryrun_has_no_network(capsys, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No network clients allowed")

    monkeypatch.setattr("pubmed_zotero.cli.PubMedClient", forbidden)
    monkeypatch.setattr("pubmed_zotero.cli.ZoteroClient", forbidden)
    assert (
        main(
            [
                "--config",
                str(CONFIG),
                "--fixture",
                str(FIXTURE),
                "--zotero-snapshot",
                str(ROOT / "tests/fixtures/zotero-empty.json"),
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "dry-run"
    assert report["sync"]["summary"]["new"] == 2
    assert report["summary"]["imported"] == 0


def test_apply_rejects_fixture_before_network():
    with pytest.raises(SystemExit) as exc:
        main(["--fixture", str(FIXTURE), "--zotero", "--apply"])
    assert exc.value.code == 2


def test_apply_wrong_confirmation_never_reads_or_writes_zotero(monkeypatch, capsys):
    monkeypatch.setattr(
        "pubmed_zotero.cli.PubMedClient", lambda **kw: FixtureReader(FIXTURE)
    )
    monkeypatch.setenv("ZOTERO_LIBRARY_ID", "123")

    def forbidden(*args, **kwargs):
        raise AssertionError("No Zotero requests allowed")

    monkeypatch.setattr("pubmed_zotero.cli.ZoteroClient", forbidden)
    assert (
        main(
            [
                "--config",
                str(CONFIG),
                "--live",
                "--zotero",
                "--apply",
                "--confirm-library",
                "wrong",
            ]
        )
        == 1
    )
    assert capsys.readouterr().out == ""


def test_apply_import_cap_prevents_all_writes(monkeypatch):
    from pubmed_zotero.zotero import Snapshot

    monkeypatch.setattr(
        "pubmed_zotero.cli.PubMedClient", lambda **kw: FixtureReader(FIXTURE)
    )
    monkeypatch.setenv("ZOTERO_LIBRARY_ID", "123")

    class ReadOnly:
        def __init__(self, *args, **kwargs):
            pass

        def snapshot(self):
            return Snapshot([], [], 0)

        def create(self, *args):
            raise AssertionError(
                "Import cap must be checked before collection creation"
            )

    monkeypatch.setattr("pubmed_zotero.cli.ZoteroClient", ReadOnly)
    assert (
        main(
            [
                "--config",
                str(CONFIG),
                "--live",
                "--zotero",
                "--apply",
                "--confirm-library",
                "123",
                "--max-imports",
                "1",
            ]
        )
        == 1
    )
