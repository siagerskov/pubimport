"""Zotero API v3: paginated snapshots and explicit, concurrency-guarded writes."""

import hashlib
import json
import re
import time
from dataclasses import dataclass
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_BYTES = 20 * 1024 * 1024
KEY = re.compile(r"[A-Z0-9]{8}")


class ZoteroError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward a library key to a redirect destination.
        return None


@dataclass
class Snapshot:
    collections: list[dict]
    items: list[dict]
    version: int


def validate_records(records: list, kind: str) -> None:
    seen = set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("data"), dict):
            raise ZoteroError("Ogiltig Zotero-post.")
        key = record.get("key")
        data = record["data"]
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in seen:
            raise ZoteroError("Ogiltig eller dubbel Zotero-nyckel.")
        if data.get("key", key) != key:
            raise ZoteroError("Inkonsekvent Zotero-post.")
        seen.add(key)
        if kind == "collections":
            if not isinstance(data.get("name"), str):
                raise ZoteroError("Samlingen saknar namn.")
            parent = data.get("parentCollection", False)
            if parent is not False and (
                not isinstance(parent, str) or not KEY.fullmatch(parent)
            ):
                raise ZoteroError("Ogiltig överordnad samling.")
        else:
            if not isinstance(data.get("itemType"), str):
                raise ZoteroError("Posten saknar itemType.")
            for field in ("extra", "DOI", "note", "url"):
                if field in data and not isinstance(data[field], str):
                    raise ZoteroError("Ogiltigt textfält i Zotero.")
            for field in ("collections", "tags"):
                if field in data and not isinstance(data[field], list):
                    raise ZoteroError("Ogiltigt listfält i Zotero.")
            if any(
                not isinstance(k, str) or not KEY.fullmatch(k)
                for k in data.get("collections", [])
            ):
                raise ZoteroError("Ogiltigt samlingsmedlemskap.")
            if any(
                not isinstance(t, dict) or not isinstance(t.get("tag"), str)
                for t in data.get("tags", [])
            ):
                raise ZoteroError("Ogiltig tagg.")


class ZoteroClient:
    def __init__(
        self,
        library_id: str,
        api_key: str,
        library_type: str = "user",
        *,
        opener=None,
        sleep=time.sleep,
        attempts=4,
        allow_writes=False,
    ):
        if not isinstance(library_id, str) or not re.fullmatch(r"[0-9]+", library_id):
            raise ZoteroError("ZOTERO_LIBRARY_ID måste vara numeriskt.")
        if library_type not in {"user", "group"} or not api_key or not api_key.strip():
            raise ZoteroError(
                "Zotero kräver nyckel och bibliotekstyp user eller group."
            )
        self.library_id, self.library_type = library_id, library_type
        self._access_checked = False
        self._permissions = None
        self.base = f"https://api.zotero.org/{library_type}s/{library_id}/"
        self.api_key = api_key
        self.opener = opener or build_opener(NoRedirect()).open
        self.sleep, self.attempts = sleep, attempts
        self.allow_writes = allow_writes
        self.version = None

    def _request(self, method, path, payload=None):
        if method != "GET" and (not self.allow_writes or self.version is None):
            raise ZoteroError(
                "Skrivning kräver uttryckligt apply-läge och läst bibliotek."
            )
        if method != "GET" and not self._access_checked:
            self.check_access()
        body = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
            if payload is not None
            else None
        )
        headers = {
            "Zotero-API-Version": "3",
            "Zotero-API-Key": self.api_key,
            "User-Agent": "pubmed-zotero/0.2.0",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
            headers["If-Unmodified-Since-Version"] = str(self.version)
            if method == "POST":
                headers["Zotero-Write-Token"] = hashlib.sha256(body).hexdigest()[:32]
        url = (
            "https://api.zotero.org" + path
            if path.startswith("/")
            else self.base + path
        )
        request = Request(url, data=body, headers=headers, method=method)
        for attempt in range(self.attempts):
            delay = 2**attempt
            try:
                with self.opener(request, timeout=30) as response:
                    raw = response.read(MAX_BYTES + 1)
                    if len(raw) > MAX_BYTES:
                        raise ZoteroError("Zotero-svaret överskred storleksgränsen.")
                    metadata = dict(response.headers.items())
                    # HTTP headers are case insensitive; fake transports need not be.
                    metadata = {k.lower(): v for k, v in metadata.items()}
                    for field in ("backoff", "retry-after"):
                        if field in metadata:
                            self._pause(metadata[field])
                    try:
                        data = json.loads(raw) if raw else None
                    except (ValueError, UnicodeError):
                        raise ZoteroError("Zotero returnerade ogiltig JSON.") from None
                    return data, metadata
            except HTTPError as exc:
                status = exc.code
                pause = exc.headers.get("Retry-After") if exc.headers else None
                exc.close()
                if status == 412:
                    raise ZoteroError(
                        "Biblioteket ändrades samtidigt; kör igen från en ny läsning."
                    ) from None
                if status != 429 and not 500 <= status <= 599:
                    raise ZoteroError(
                        f"Zotero avvisade anropet (HTTP {status})."
                    ) from None
                # Only retry reads. A failed write can already have reached Zotero.
                if method != "GET":
                    raise ZoteroError(
                        "Skrivning misslyckades; läs om biblioteket före omkörning."
                    ) from None
                if pause:
                    self._pause(pause)
                    delay = 0
            except (URLError, OSError, HTTPException):
                if method != "GET":
                    raise ZoteroError(
                        "Skrivresultatet är okänt; läs om biblioteket före omkörning."
                    ) from None
            if attempt + 1 < self.attempts:
                self.sleep(delay)
        raise ZoteroError("Zotero kunde inte nås efter begränsade återförsök.")

    def _pause(self, value):
        try:
            seconds = int(value)
        except (ValueError, TypeError):
            raise ZoteroError("Zotero returnerade en ogiltig paus.") from None
        if not 0 <= seconds <= 120:
            raise ZoteroError("Zotero begär en längre paus; försök senare.")
        self.sleep(seconds)

    @staticmethod
    def _version(headers):
        try:
            value = int(headers["last-modified-version"])
            if value < 0:
                raise ValueError
            return value
        except (ValueError, TypeError, KeyError):
            raise ZoteroError(
                "Zotero-svaret saknar giltig biblioteksversion."
            ) from None

    def _list(self, kind, version=None):
        records = []
        total = None
        while total is None or len(records) < total:
            query = urlencode(
                {
                    "format": "json",
                    "limit": 100,
                    "start": len(records),
                    **({"includeTrashed": 1} if kind == "items" else {}),
                }
            )
            data, headers = self._request("GET", f"{kind}?{query}")
            observed = self._version(headers)
            if version is not None and observed != version:
                raise ZoteroError("Biblioteket ändrades under läsningen; kör igen.")
            version = observed
            try:
                count = int(headers["total-results"])
                if count < 0 or (total is not None and total != count):
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                raise ZoteroError(
                    "Zotero returnerade inkonsekvent sidindelning."
                ) from None
            total = count
            if (
                not isinstance(data, list)
                or len(data) > 100
                or len(records) + len(data) > total
            ):
                raise ZoteroError("Zotero returnerade en ogiltig sida.")
            if not data and len(records) < total:
                raise ZoteroError("Zotero returnerade en ofullständig sida.")
            records.extend(data)
        validate_records(records, kind)
        return records, version

    def permissions(self):
        if self._permissions is not None:
            return self._permissions
        data, _ = self._request("GET", "/keys/current")
        try:
            access = data["access"]
            if self.library_type == "user":
                if str(data["userID"]) != self.library_id:
                    raise ZoteroError("Nyckeln tillhör ett annat personligt bibliotek.")
                target = access["user"]
                notes = target.get("notes") is True
            else:
                groups = access["groups"]
                target = groups.get(self.library_id, groups.get("all", {}))
                # Group access includes notes; personal libraries have a separate scope.
                notes = target.get("library") is True
            self._permissions = {
                "library": target.get("library") is True,
                "notes": notes,
                "write": target.get("write") is True,
            }
        except (KeyError, TypeError, AttributeError):
            raise ZoteroError(
                "API-nyckelns behörigheter kunde inte verifieras."
            ) from None
        # Discard the raw metadata response; it may contain the key itself.
        return self._permissions

    def check_access(self):
        if self._access_checked:
            return
        permissions = self.permissions()
        if not permissions["library"]:
            raise ZoteroError("API-nyckeln saknar åtkomst till biblioteket.")
        if not permissions["notes"]:
            raise ZoteroError(
                "API-nyckeln saknar Allow notes access; synkningen stoppas."
            )
        if self.allow_writes and not permissions["write"]:
            raise ZoteroError("API-nyckeln saknar skrivrättighet.")
        self._access_checked = True

    def snapshot(self):
        self.check_access()
        collections, version = self._list("collections")
        items, version = self._list("items", version)
        self.version = version
        return Snapshot(collections, items, version)

    def create(self, kind, data):
        if kind not in {"collections", "items"}:
            raise ZoteroError("Ogiltig skrivdestination.")
        result, headers = self._request("POST", kind, [data])
        self.version = self._version(headers)
        if (
            not isinstance(result, dict)
            or result.get("failed")
            or result.get("unchanged")
        ):
            raise ZoteroError("Zotero avvisade en post; kör om efter kontroll.")
        successful = result.get("successful", {})
        if not isinstance(successful, dict):
            raise ZoteroError("Zotero returnerade ett ogiltigt skrivresultat.")
        record = successful.get("0")
        if not record:
            raise ZoteroError("Zotero bekräftade inte skapandet; läs om biblioteket.")
        validate_records([record], kind)
        return record

    def add_collections(self, item, collections):
        if not KEY.fullmatch(item["key"]) or any(
            not KEY.fullmatch(k) for k in collections
        ):
            raise ZoteroError("Ogiltiga nycklar för samlingsuppdatering.")
        _, headers = self._request(
            "PATCH", "items/" + item["key"], {"collections": collections}
        )
        self.version = self._version(headers)
