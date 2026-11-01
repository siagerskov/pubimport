import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

import pytest

from pubmed_zotero.zotero import NoRedirect, ZoteroClient, ZoteroError


class Response(io.BytesIO):
    def __init__(self, data=None, *, version=1, total=0, headers=None):
        super().__init__(json.dumps(data).encode() if data is not None else b"")
        self.headers = {
            "Last-Modified-Version": str(version),
            "Total-Results": str(total),
            **(headers or {}),
        }


class Transport:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    def __call__(self, request, timeout):
        assert timeout == 30
        self.requests.append(request)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def client(*responses, **kwargs):
    transport = Transport(*responses)
    waits = []
    return (
        ZoteroClient("123", "SECRET", opener=transport, sleep=waits.append, **kwargs),
        transport,
        waits,
    )


def collection(key="AAAAAAAA"):
    return {"key": key, "data": {"name": "Test", "parentCollection": False}}


def test_snapshot_pagination_headers_and_readonly():
    c, transport, _ = client(
        Response([collection()], total=2),
        Response([collection("BBBBBBBB")], total=2),
        Response([], total=0),
    )
    snapshot = c.snapshot()
    assert snapshot.version == 1 and len(snapshot.collections) == 2
    assert parse_qs(urlparse(transport.requests[1].full_url).query)["start"] == ["1"]
    assert all(r.method == "GET" for r in transport.requests)
    headers = {k.lower(): v for k, v in transport.requests[0].header_items()}
    assert headers["zotero-api-version"] == "3"
    assert headers["zotero-api-key"] == "SECRET"
    assert all("SECRET" not in r.full_url for r in transport.requests)
    with pytest.raises(ZoteroError, match="Skrivning"):
        c.create("collections", {"name": "blocked"})
    assert len(transport.requests) == 3


def test_snapshot_rejects_concurrent_change():
    c, _, _ = client(Response([], version=1), Response([], version=2))
    with pytest.raises(ZoteroError, match="ändrades"):
        c.snapshot()


@pytest.mark.parametrize(
    "response",
    [
        Response([], total=1),
        Response({}, total=0),
        Response([collection(), collection()], total=2),
        Response([{"key": "BAD", "data": {"name": "x"}}], total=1),
    ],
)
def test_broken_pagination_or_records_fail_closed(response):
    c, _, _ = client(response)
    with pytest.raises(ZoteroError):
        c.snapshot()


def test_read_retries_429_and_respects_backoff():
    c, transport, waits = client(
        HTTPError("secret", 429, "SECRET", {"Retry-After": "5"}, None),
        Response([], headers={"Backoff": "3"}),
        Response([]),
    )
    c.snapshot()
    assert len(transport.requests) == 3
    assert 5 in waits and 3 in waits


@pytest.mark.parametrize("status", [401, 403, 412, 302])
def test_http_errors_are_safe(status):
    c, transport, _ = client(HTTPError("https://secret", status, "SECRET", {}, None))
    with pytest.raises(ZoteroError) as exc:
        c.snapshot()
    assert "SECRET" not in str(exc.value) and "https://secret" not in str(exc.value)
    assert len(transport.requests) == 1


def test_reads_exhaust_network_retries():
    c, transport, _ = client(*[URLError("SECRET") for _ in range(4)])
    with pytest.raises(ZoteroError) as exc:
        c.snapshot()
    assert len(transport.requests) == 4 and "SECRET" not in str(exc.value)


def test_create_has_version_guard_token_and_updates_version():
    c, transport, _ = client(
        Response([], version=2),
        Response([], version=2),
        Response(
            {"successful": {"0": collection()}, "failed": {}, "unchanged": {}},
            version=3,
        ),
        allow_writes=True,
    )
    c.snapshot()
    assert (
        c.create("collections", {"name": "Test", "parentCollection": False})["key"]
        == "AAAAAAAA"
    )
    request = transport.requests[-1]
    headers = {k.lower(): v for k, v in request.header_items()}
    assert headers["if-unmodified-since-version"] == "2"
    assert len(headers["zotero-write-token"]) == 32
    assert c.version == 3 and request.method == "POST"


@pytest.mark.parametrize(
    "failure", [URLError("SECRET"), HTTPError("secret", 503, "SECRET", {}, None)]
)
def test_ambiguous_write_is_not_retried(failure):
    c, transport, _ = client(Response([]), Response([]), failure, allow_writes=True)
    c.snapshot()
    with pytest.raises(ZoteroError) as exc:
        c.create("collections", {"name": "Test"})
    assert len(transport.requests) == 3
    assert "SECRET" not in str(exc.value)


def test_failed_batch_is_not_reported_as_success():
    c, _, _ = client(
        Response([]),
        Response([]),
        Response({"successful": {}, "failed": {"0": {"message": "SECRET"}}}),
        allow_writes=True,
    )
    c.snapshot()
    with pytest.raises(ZoteroError) as exc:
        c.create("items", {"itemType": "journalArticle"})
    assert "SECRET" not in str(exc.value)


def test_patch_contains_only_collection_union():
    c, transport, _ = client(
        Response([]), Response([]), Response(version=2), allow_writes=True
    )
    c.snapshot()
    c.add_collections({"key": "AAAAAAAA"}, ["BBBBBBBB"])
    assert transport.requests[-1].method == "PATCH"
    assert json.loads(transport.requests[-1].data) == {"collections": ["BBBBBBBB"]}
    assert c.version == 2


def test_redirect_is_never_followed():
    assert (
        NoRedirect().redirect_request(None, None, 302, "x", {}, "https://evil.example")
        is None
    )


@pytest.mark.parametrize(
    "library_id,key,kind", [("x", "k", "user"), ("1", "", "user"), ("1", "k", "bad")]
)
def test_invalid_configuration(library_id, key, kind):
    with pytest.raises(ZoteroError):
        ZoteroClient(library_id, key, kind)
