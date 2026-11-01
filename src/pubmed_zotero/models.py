"""Normalized bibliographic data and search provenance."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Search:
    id: str
    title: str
    query: str
    version: str
    description: str
    lookback_days: int = 14
    enabled: bool = True


@dataclass(frozen=True)
class Author:
    family: str | None = None
    given: str | None = None
    collective: str | None = None


@dataclass(frozen=True)
class Article:
    pmid: str
    title: str | None
    authors: tuple[Author, ...]
    journal: str | None
    publication_date: str | None
    abstract: str | None
    doi: str | None

    @property
    def url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"


@dataclass(frozen=True)
class Provenance:
    search_id: str
    search_version: str
    query: str
    searched_at: str
    discovered_at: str


@dataclass
class DiscoveredArticle:
    article: Article
    provenance: list[Provenance] = field(default_factory=list)
    status: str = "discovered"  # Not imported or compared against a Zotero library.
