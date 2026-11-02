import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from pubmed_zotero.cli import FixtureReader, main
from pubmed_zotero.config import load_searches
from pubmed_zotero.pipeline import discover, search_range
from pubmed_zotero.pubmed import PubMedError, SearchLimitError

ROOT = Path(__file__).parents[1]


def test_retrospective_uses_publication_dates_and_inclusive_bounds():
    class Reader(FixtureReader):
        calls = []

        def search(self, query, **kwargs):
            self.calls.append(kwargs)
            return super().search(query, **kwargs)

    reader = Reader(ROOT / "tests/fixtures/pubmed.xml")
    searches = load_searches(ROOT / "config/searches.yaml")[-1:]
    report = discover(
        searches,
        reader,
        now=datetime(2026, 11, 2, tzinfo=UTC),
        start_date=date(2018, 1, 1),
        date_type="pdat",
    )
    assert reader.calls == [
        {"start": "2018/01/01", "end": "2026/11/02", "limit": None, "date_type": "pdat"}
    ]
    assert report["date_mode"] == "retrospective"
    provenance = report["articles"][0]["provenance"][0]
    assert provenance["date_type"] == "pdat"
    assert provenance["window_start"] == "2018/01/01"


def test_large_ranges_split_without_overlap_or_lost_pmids():
    calls = []

    class Reader:
        def search(self, query, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise SearchLimitError(4)
            return (
                (["1", "2"], 2) if kwargs["start"] == "2018/01/01" else (["3", "4"], 2)
            )

    ids, count = search_range(
        Reader(), "q", date(2018, 1, 1), date(2018, 1, 4), None, "pdat"
    )
    assert ids == ["1", "2", "3", "4"] and count == 4
    assert calls[1]["end"] == "2018/01/02"
    assert calls[2]["start"] == "2018/01/03"


def test_changed_count_after_split_fails_instead_of_silent_partial_result():
    class Reader:
        calls = 0

        def search(self, query, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise SearchLimitError(4)
            return ["1"], 1

    with pytest.raises(PubMedError, match="ändrades"):
        search_range(Reader(), "q", date(2018, 1, 1), date(2018, 1, 4), None, "pdat")


def test_cli_selects_nph_only_and_preserves_readonly_default(capsys):
    assert (
        main(
            [
                "--config",
                str(ROOT / "config/searches.yaml"),
                "--fixture",
                str(ROOT / "tests/fixtures/pubmed.xml"),
                "--from-date",
                "2018-01-01",
                "--until-date",
                "2026-11-02",
                "--search-id",
                "nph",
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert len(report["searches"]) == 1
    assert report["searches"][0]["search_id"] == "nph"
    assert report["searches"][0]["date_type"] == "pdat"
    assert report["summary"]["imported"] == 0


@pytest.mark.parametrize(
    "args",
    [
        ["--from-date", "invalid"],
        ["--until-date", "2020-01-01"],
        ["--from-date", "2020-01-02", "--until-date", "2020-01-01"],
    ],
)
def test_invalid_retrospective_dates_are_rejected(args):
    with pytest.raises(SystemExit):
        main(["--fixture", str(ROOT / "tests/fixtures/pubmed.xml"), *args])
