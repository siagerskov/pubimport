import io
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs

import pytest

from pubmed_zotero.pubmed import PubMedClient, PubMedError, parse_articles

FIXTURE = Path(__file__).parent / "fixtures/pubmed.xml"


class Transport:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def __call__(self, request, *, timeout):
        self.calls.append((request, timeout))
        item = next(self.responses)
        if isinstance(item, Exception):
            raise item
        return io.BytesIO(item)


def client(*responses, **kwargs):
    transport = Transport(*responses)
    waits = []
    return (
        PubMedClient(
            opener=transport, sleep=waits.append, monotonic=lambda: 0, **kwargs
        ),
        transport,
        waits,
    )


def search_response(ids, count=None):
    return json.dumps(
        {
            "esearchresult": {
                "count": str(len(ids) if count is None else count),
                "idlist": ids,
            }
        }
    ).encode()


def test_parse_rich_and_missing_metadata():
    rich, minimal = parse_articles(FIXTURE.read_bytes())
    assert rich.pmid == "10000001"
    assert rich.title == "Synthetic MSK imaging study"
    assert rich.doi == "10.0000/test"
    assert rich.authors[0].given == "Anna"
    assert rich.authors[1].collective == "Fixture Group"
    assert rich.publication_date == "2026-Nov"
    assert (
        rich.abstract
        == "OBJECTIVE: Evaluate imaging.\nRESULTS: Synthetic results only."
    )
    assert rich.url == "https://pubmed.ncbi.nlm.nih.gov/10000001/"
    assert minimal.publication_date == "2026 Winter"
    assert minimal.doi is minimal.abstract is minimal.journal is None
    assert minimal.authors == ()


@pytest.mark.parametrize(
    "payload",
    [
        b"broken",
        b"<ERROR>secret</ERROR>",
        b"<PubmedArticleSet><PubmedArticle/></PubmedArticleSet>",
        b"<PubmedArticleSet><PubmedBookArticle/></PubmedArticleSet>",
        b'<!DOCTYPE x [<!ENTITY x "unsafe">]><PubmedArticleSet>&x;</PubmedArticleSet>',
    ],
)
def test_bad_xml_is_safe(payload):
    with pytest.raises(PubMedError) as exc:
        parse_articles(payload)
    assert "secret" not in str(exc.value)


def test_pagination_and_post_parameters():
    c, transport, waits = client(
        search_response([str(n) for n in range(1, 201)], 201),
        search_response(["201"], 201),
        api_key="SECRET",
    )
    ids, total = c.search("radiology", start="2026/10/19", end="2026/11/01")
    assert len(ids) == total == 201
    request, timeout = transport.calls[1]
    params = parse_qs(request.data.decode())
    assert params["retstart"] == ["200"]
    assert params["datetype"] == ["edat"]
    assert params["api_key"] == ["SECRET"]
    assert "SECRET" not in request.full_url
    assert request.method == "POST" and timeout == 30
    assert waits[-1] >= 0.35


def test_empty_and_capped_searches():
    c, _, _ = client(search_response([]))
    assert c.search("q", start="s", end="e") == ([], 0)
    c, _, _ = client(search_response(["1"], 12000))
    assert c.search("q", start="s", end="e", limit=1) == (["1"], 12000)
    c, _, _ = client(search_response([], 12000))
    with pytest.raises(PubMedError, match="9999"):
        c.search("q", start="s", end="e")


@pytest.mark.parametrize(
    "payload",
    [
        b"bad",
        b"{}",
        b'{"esearchresult":null}',
        search_response(["bad"]),
        search_response([], 1),
        search_response(["1", "1"]),
        b'{"esearchresult":{"count":"0","idlist":[],"errorlist":{"x":"SECRET"}}}',
    ],
)
def test_invalid_search_response(payload):
    c, _, _ = client(payload)
    with pytest.raises(PubMedError) as exc:
        c.search("q", start="s", end="e")
    assert "SECRET" not in str(exc.value)


def test_fetch_reorders_and_detects_missing_records():
    c, _, _ = client(FIXTURE.read_bytes())
    assert [a.pmid for a in c.fetch(["10000002", "10000001"])] == [
        "10000002",
        "10000001",
    ]
    c, _, _ = client(FIXTURE.read_bytes())
    with pytest.raises(PubMedError, match="metadata"):
        c.fetch(["10000001"])


@pytest.mark.parametrize(
    "failure",
    [
        URLError("SECRET"),
        TimeoutError("SECRET"),
        HTTPError("https://secret/", 503, "SECRET", {}, None),
    ],
)
def test_transient_errors_retry(failure):
    c, transport, waits = client(failure, search_response([]))
    assert c.search("q", start="s", end="e") == ([], 0)
    assert len(transport.calls) == 2
    assert 1 in waits


def test_retry_after_and_exhaustion_do_not_leak():
    c, transport, waits = client(
        *[
            HTTPError("secret", 429, "SECRET", {"Retry-After": "5"}, None)
            for _ in range(4)
        ]
    )
    with pytest.raises(PubMedError) as exc:
        c.search("q", start="s", end="e")
    assert len(transport.calls) == 4 and waits.count(5) == 3
    assert "SECRET" not in str(exc.value)


def test_retry_after_date():
    c, _, waits = client(
        HTTPError(
            "secret",
            429,
            "SECRET",
            {"Retry-After": "Sun, 01 Nov 2026 00:00:10 GMT"},
            None,
        ),
        search_response([]),
        now=lambda: datetime(2026, 11, 1, tzinfo=UTC),
    )
    c.search("q", start="s", end="e")
    assert 10 in waits


def test_nonretryable_http_error():
    c, transport, _ = client(HTTPError("secret", 403, "SECRET", {}, None))
    with pytest.raises(PubMedError, match="403") as exc:
        c.search("q", start="s", end="e")
    assert len(transport.calls) == 1
    assert "SECRET" not in str(exc.value)


def test_doi_fallback_is_normalized():
    payload = b"""<PubmedArticleSet><PubmedArticle><MedlineCitation>
    <PMID>1</PMID><Article><ELocationID EIdType="doi">DOI: 10.1234/ABC</ELocationID>
    </Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""
    assert parse_articles(payload)[0].doi == "10.1234/abc"


def test_fetch_batches_at_100():
    def xml(ids):
        return (
            "<PubmedArticleSet>"
            + "".join(
                f"<PubmedArticle><MedlineCitation><PMID>{pmid}</PMID><Article/>"
                "</MedlineCitation></PubmedArticle>"
                for pmid in ids
            )
            + "</PubmedArticleSet>"
        ).encode()

    ids = [str(n) for n in range(1, 102)]
    c, transport, _ = client(xml(ids[:100]), xml(ids[100:]))
    assert [a.pmid for a in c.fetch(ids)] == ids
    assert len(transport.calls) == 2
    assert parse_qs(transport.calls[1][0].data.decode())["id"] == ["101"]


def test_duplicate_fetch_ids_rejected_before_network():
    c, transport, _ = client()
    with pytest.raises(ValueError):
        c.fetch([str(n) for n in range(1, 101)] + ["1"])
    assert not transport.calls


def test_changing_search_count_aborts():
    c, _, _ = client(
        search_response([str(n) for n in range(1, 201)], 201),
        search_response(["201"], 202),
    )
    with pytest.raises(PubMedError, match="ändrades"):
        c.search("q", start="s", end="e")


def test_long_retry_after_aborts_without_long_wait():
    c, transport, waits = client(
        HTTPError("secret", 429, "SECRET", {"Retry-After": "3600"}, None)
    )
    with pytest.raises(PubMedError, match="paus"):
        c.search("q", start="s", end="e")
    assert len(transport.calls) == 1 and max(waits) == 0


def test_oversized_response_aborts(monkeypatch):
    monkeypatch.setattr("pubmed_zotero.pubmed.MAX_RESPONSE_BYTES", 5)
    c, _, _ = client(b"123456")
    with pytest.raises(PubMedError, match="storleksgränsen"):
        c.search("q", start="s", end="e")


def test_interrupted_body_is_retried():
    from http.client import IncompleteRead

    class Interrupted(io.BytesIO):
        def read(self, *args):
            raise IncompleteRead(b"SECRET")

    responses = iter([Interrupted(), io.BytesIO(search_response([]))])
    waits = []
    c = PubMedClient(
        opener=lambda *a, **kw: next(responses), sleep=waits.append, monotonic=lambda: 0
    )
    assert c.search("q", start="s", end="e") == ([], 0)
    assert 1 in waits


def test_search_passes_pdat_explicitly_to_ncbi():
    c, transport, _ = client(search_response([]))
    c.search("q", start="2018/01/01", end="2026/11/02", date_type="pdat")
    assert parse_qs(transport.calls[0][0].data.decode())["datetype"] == ["pdat"]
