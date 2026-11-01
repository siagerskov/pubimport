"""Identifier-based matching; ambiguous matches fail closed."""

import re

from .zotero import ZoteroError


def normalize_doi(value):
    return (
        re.sub(
            r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)",
            "",
            value.strip(),
            flags=re.IGNORECASE,
        )
        .strip()
        .lower()
    )


def pmids(data):
    result = set(re.findall(r"^PMID:\s*(\d+)\s*$", data.get("extra", ""), re.MULTILINE))
    url = re.fullmatch(
        r"https?://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/?", data.get("url", "")
    )
    if url:
        result.add(url.group(1))
    return result


def match(article, items):
    candidates = [
        item
        for item in items
        if item["data"]["itemType"] not in {"note", "attachment", "annotation"}
    ]
    primary = [item for item in candidates if article["pmid"] in pmids(item["data"])]
    doi = normalize_doi(article.get("doi") or "")
    secondary = [
        item
        for item in candidates
        if doi and normalize_doi(item["data"].get("DOI", "")) == doi
    ]
    if len(primary) > 1 or len(secondary) > 1:
        raise ZoteroError(
            "Flera biblioteksposter matchar samma identifierare; granska dubbletter."
        )
    if primary:
        if pmids(primary[0]["data"]) != {article["pmid"]}:
            raise ZoteroError("Posten har motstridiga PMID; manuell granskning krävs.")
        if secondary and primary[0]["key"] != secondary[0]["key"]:
            raise ZoteroError(
                "PMID och DOI pekar på olika poster; manuell granskning krävs."
            )
        return primary[0]
    if secondary:
        known = pmids(secondary[0]["data"])
        if known and known != {article["pmid"]}:
            raise ZoteroError("Samma DOI har olika PMID; manuell granskning krävs.")
        return secondary[0]
    return None
