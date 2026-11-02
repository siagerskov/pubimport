"""Official NCBI E-utilities client with bounded retries and injectable I/O."""

import json
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from .models import Article, Author

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
MAX_RESPONSE_BYTES = 20 * 1024 * 1024


class PubMedError(RuntimeError):
    """Safe public error: never includes URLs, credentials or response bodies."""


class SearchLimitError(PubMedError):
    def __init__(self, count):
        super().__init__(
            "Fler än 9999 träffar: dela datumintervallet eller avgränsa sökningen."
        )
        self.count = count


def _text(element) -> str | None:
    if element is None:
        return None
    return " ".join("".join(element.itertext()).split()) or None


def parse_articles(payload: bytes) -> list[Article]:
    try:
        root = ElementTree.fromstring(payload)
    except (ElementTree.ParseError, DefusedXmlException):
        raise PubMedError("PubMed returnerade ogiltig eller osäker XML.") from None
    if root.tag != "PubmedArticleSet" or root.find(".//ERROR") is not None:
        raise PubMedError("PubMed returnerade ett oväntat metadatasvar.")
    result = []
    for record in root:
        if record.tag != "PubmedArticle":
            raise PubMedError("PubMed-posttypen stöds inte; inga resultat levereras.")
        citation = record.find("MedlineCitation")
        pmid = _text(record.find("MedlineCitation/PMID"))
        article = record.find("MedlineCitation/Article")
        if citation is None or not pmid or not pmid.isdigit() or article is None:
            raise PubMedError("PubMed-posten saknar giltigt PMID eller artikeldata.")
        authors = []
        for person in article.findall("AuthorList/Author"):
            authors.append(
                Author(
                    family=_text(person.find("LastName")),
                    given=_text(person.find("ForeName"))
                    or _text(person.find("Initials")),
                    collective=_text(person.find("CollectiveName")),
                )
            )
        date = article.find("Journal/JournalIssue/PubDate")
        publication_date = None
        if date is not None:
            publication_date = (
                _text(date.find("MedlineDate"))
                or "-".join(
                    part
                    for tag in ("Year", "Month", "Day")
                    if (part := _text(date.find(tag)))
                )
                or None
            )
        abstract_parts = []
        for section in article.findall("Abstract/AbstractText"):
            if content := _text(section):
                label = section.get("Label")
                abstract_parts.append(f"{label}: {content}" if label else content)
        doi = None
        identifiers = record.findall("PubmedData/ArticleIdList/ArticleId")
        identifiers += article.findall("ELocationID")
        for identifier in identifiers:
            kind = identifier.get("IdType") or identifier.get("EIdType")
            if kind == "doi" and identifier.get("ValidYN") != "N":
                value = _text(identifier)
                if value:
                    doi = (
                        re.sub(
                            r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)",
                            "",
                            value,
                            flags=re.IGNORECASE,
                        )
                        .strip()
                        .lower()
                        or None
                    )
                    if doi:
                        break
        result.append(
            Article(
                pmid=pmid,
                title=_text(article.find("ArticleTitle")),
                authors=tuple(authors),
                journal=_text(article.find("Journal/Title")),
                publication_date=publication_date,
                abstract="\n".join(abstract_parts) or None,
                doi=doi,
            )
        )
    if len({a.pmid for a in result}) != len(result):
        raise PubMedError("PubMed returnerade dubbla metadata-ID:n.")
    return result


class PubMedClient:
    def __init__(
        self,
        *,
        email: str | None = None,
        api_key: str | None = None,
        opener: Callable = urlopen,
        sleep: Callable = time.sleep,
        monotonic: Callable = time.monotonic,
        now: Callable = lambda: datetime.now(UTC),
        attempts: int = 4,
        timeout: float = 30,
    ):
        if attempts < 1 or timeout <= 0:
            raise ValueError("Positive attempts and timeout required")
        self.email, self.api_key = email, api_key
        self.opener, self.sleep, self.monotonic, self.now = (
            opener,
            sleep,
            monotonic,
            now,
        )
        self.attempts, self.timeout = attempts, timeout
        # Conservative serial pacing even when an API key is supplied.
        self.interval = 0.35
        self.next_request = 0.0

    def _request(self, endpoint: str, params: dict) -> bytes:
        params = {**params, "tool": "pubmed-zotero"}
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        # POST prevents API keys and long search terms from appearing in URL logs.
        request = Request(
            BASE_URL + endpoint,
            data=urlencode(params).encode(),
            headers={"User-Agent": "pubmed-zotero/0.2.0"},
            method="POST",
        )
        for attempt in range(self.attempts):
            self.sleep(max(0.0, self.next_request - self.monotonic()))
            self.next_request = self.monotonic() + self.interval
            delay = min(2**attempt, 60)
            try:
                with self.opener(request, timeout=self.timeout) as response:
                    body = response.read(MAX_RESPONSE_BYTES + 1)
                    if len(body) > MAX_RESPONSE_BYTES:
                        raise PubMedError("PubMed-svaret överskred storleksgränsen.")
                    return body
            except HTTPError as exc:
                status = exc.code
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                exc.close()
                if status != 429 and not 500 <= status <= 599:
                    raise PubMedError(
                        f"PubMed avvisade anropet (HTTP {status})."
                    ) from None
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        try:
                            delay = max(
                                delay,
                                (
                                    parsedate_to_datetime(retry_after) - self.now()
                                ).total_seconds(),
                            )
                        except (ValueError, TypeError, OverflowError):
                            pass
                    if delay > 120:
                        raise PubMedError(
                            "PubMed begär en längre paus; försök senare."
                        ) from None
            except (URLError, TimeoutError, OSError, HTTPException):
                pass
            if attempt + 1 < self.attempts:
                self.sleep(delay)
        raise PubMedError(
            "PubMed kunde inte nås efter begränsade återförsök."
        ) from None

    def search(
        self,
        query: str,
        *,
        start: str,
        end: str,
        limit: int | None = None,
        date_type: str = "edat",
    ) -> tuple[list[str], int]:
        if date_type not in {"edat", "pdat"}:
            raise ValueError("Unsupported date type")
        if limit is not None and limit < 1:
            raise ValueError("limit must be positive")
        ids = []
        total = None
        while total is None or len(ids) < min(total, limit or total):
            size = min(200, (limit - len(ids)) if limit else 200)
            payload = self._request(
                "esearch.fcgi",
                {
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retstart": len(ids),
                    "retmax": size,
                    "datetype": date_type,
                    "mindate": start,
                    "maxdate": end,
                    "sort": "pub date",
                },
            )
            try:
                data = json.loads(payload)
                result = data["esearchresult"]
                count = int(result["count"])
                page = result["idlist"]
                if "error" in data or "errorlist" in result or "ERROR" in result:
                    raise ValueError
                if (
                    count < 0
                    or not isinstance(page, list)
                    or any(
                        not isinstance(pmid, str) or not pmid.isdigit() for pmid in page
                    )
                ):
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise PubMedError("PubMed returnerade ett ogiltigt söksvar.") from None
            if total is None:
                total = count
                if total > 9999 and (limit is None or limit > 9999):
                    raise SearchLimitError(total)
            elif count != total:
                raise PubMedError(
                    "PubMed-resultatet ändrades under paginering; kör igen."
                )
            remaining = min(total, limit or total) - len(ids)
            if len(page) > min(size, remaining) or len(set(ids + page)) != len(
                ids + page
            ):
                raise PubMedError("PubMed returnerade inkonsekvent paginering.")
            if remaining and not page:
                raise PubMedError("PubMed returnerade en ofullständig söksida.")
            ids.extend(page)
        return ids, total

    def fetch(self, ids: list[str]) -> list[Article]:
        if any(not isinstance(pmid, str) or not pmid.isdigit() for pmid in ids) or len(
            set(ids)
        ) != len(ids):
            raise ValueError("Valid unique PMIDs required")
        articles = []
        for offset in range(0, len(ids), 100):
            batch = ids[offset : offset + 100]
            parsed = parse_articles(
                self._request(
                    "efetch.fcgi",
                    {
                        "db": "pubmed",
                        "id": ",".join(batch),
                        "retmode": "xml",
                    },
                )
            )
            by_id = {article.pmid: article for article in parsed}
            if set(by_id) != set(batch):
                raise PubMedError(
                    "PubMed returnerade ofullständig eller oväntad metadata."
                )
            articles.extend(by_id[pmid] for pmid in batch)
        return articles
