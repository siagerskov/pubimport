"""Discovery and Zotero planning CLI. External writes require explicit opt-in."""

import argparse
import json
import os
import sys
from pathlib import Path

from .config import ConfigurationError, load_searches
from .pipeline import discover
from .pubmed import PubMedClient, PubMedError, parse_articles
from .sync import ApplyError, apply_plan, bounded_plan, plan_sync
from .zotero import Snapshot, ZoteroClient, ZoteroError


class FixtureReader:
    """Offline demonstration: every search returns the same synthetic articles."""

    def __init__(self, path: Path):
        self.articles = parse_articles(path.read_bytes())

    def search(self, query, *, start, end, limit=None):
        ids = [a.pmid for a in self.articles]
        return ids[:limit], len(ids)

    def fetch(self, ids):
        by_id = {a.pmid: a for a in self.articles}
        return [by_id[pmid] for pmid in ids]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="PubMed-bevakning med säker Zotero-dry-run som standard."
    )
    parser.add_argument("--config", type=Path, default=Path("config/searches.yaml"))
    parser.add_argument(
        "--limit", type=int, help="Max träffar per sökning; trunkering redovisas."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--fixture", type=Path, help="Offline-XML; samma poster för varje sökning."
    )
    source.add_argument(
        "--live", action="store_true", help="Läs från NCBI; kräver nätåtkomst."
    )
    library = parser.add_mutually_exclusive_group()
    library.add_argument(
        "--zotero", action="store_true", help="Läs biblioteket för dry-run."
    )
    library.add_argument(
        "--zotero-snapshot", type=Path, help="Offline-bibliotek i JSON."
    )
    parser.add_argument(
        "--apply", action="store_true", help="Utför import efter separat godkännande."
    )
    parser.add_argument("--confirm-library", help="Bekräfta mål-ID vid apply.")
    parser.add_argument(
        "--max-imports", type=int, default=10, help="Importtak, standard 10."
    )
    parser.add_argument(
        "--batch-imports",
        action="store_true",
        help="Importera högst max-imports nya; redovisa övriga som uppskjutna.",
    )
    args = parser.parse_args(argv)
    if args.apply and (not args.live or not args.zotero):
        parser.error("--apply kräver --live och --zotero; ingen fixture-import tillåts")
    if args.max_imports < 1:
        parser.error("--max-imports måste vara större än noll")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit måste vara större än noll")
    try:
        searches = load_searches(args.config)
        client = (
            FixtureReader(args.fixture)
            if args.fixture
            else PubMedClient(
                email=os.environ.get("NCBI_EMAIL"),
                api_key=os.environ.get("NCBI_API_KEY"),
            )
        )
        report = discover(searches, client, limit=args.limit)
        report["source"] = "synthetic-fixture" if args.fixture else "ncbi"
        if args.zotero or args.zotero_snapshot:
            if args.zotero_snapshot:
                try:
                    data = json.loads(args.zotero_snapshot.read_text(encoding="utf-8"))
                    snapshot = Snapshot(
                        data["collections"], data["items"], data["version"]
                    )
                    if (
                        not isinstance(snapshot.collections, list)
                        or not isinstance(snapshot.items, list)
                        or type(snapshot.version) is not int
                        or snapshot.version < 0
                    ):
                        raise ValueError
                except (ValueError, TypeError, KeyError):
                    raise ZoteroError("Ogiltig Zotero-snapshot.") from None
            else:
                library_id = os.environ.get("ZOTERO_LIBRARY_ID", "")
                if args.apply and args.confirm_library != library_id:
                    raise ZoteroError(
                        "Apply kräver --confirm-library med rätt biblioteks-ID."
                    )
                zotero = ZoteroClient(
                    library_id,
                    os.environ.get("ZOTERO_API_KEY", ""),
                    os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
                    allow_writes=args.apply,
                )
                snapshot = zotero.snapshot()
            if args.batch_imports:
                report, plan, deferred = bounded_plan(
                    report, searches, snapshot, args.max_imports
                )
                plan["summary"]["deferred"] = deferred
            else:
                plan = plan_sync(report, searches, snapshot)
            if args.apply:
                if plan["summary"]["new"] > args.max_imports:
                    raise ZoteroError(
                        "Importtaket överskreds; begränsa urvalet eller välj nytt tak."
                    )
                report["sync"] = apply_plan(plan, zotero)
                report["mode"] = "apply"
                report["summary"]["imported"] = report["sync"]["summary"]["imported"]
            else:
                report["sync"] = plan
                report["mode"] = "dry-run"
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except ApplyError as exc:
        print(json.dumps({"mode": "apply", "summary": exc.summary}, ensure_ascii=False))
        print(str(exc), file=sys.stderr)
        return 1
    except (ConfigurationError, PubMedError, ZoteroError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, UnicodeError):
        print("In- eller utdata kunde inte läsas eller skrivas.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
