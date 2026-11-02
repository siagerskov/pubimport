"""Compact, escaped Actions summaries; never include credentials or library data."""

import html


def action_summary(report):
    summary = report.get("sync", {}).get("summary", {})
    discovery = report["summary"]
    reviewed = summary.get("reviews_completed", summary.get("review_updates", 0))
    rows = [
        "## PubMed → Zotero",
        "",
        f"Läge: **{html.escape(report['mode'])}**",
        "",
        f"Sökträffar totalt (kan överlappa): {discovery['total_hits']}",
        f"Unika hämtade PMID: {discovery['unique_pmids']}",
        f"Trunkerat urval: {'ja' if discovery['truncated'] else 'nej'}",
        "",
        f"Nya: {summary.get('new', 0)} · Kända: {summary.get('known', 0)} · "
        f"Saknad titel: {summary.get('metadata_missing', 0)} · "
        f"Importerade: {summary.get('imported', 0)}",
        "",
        f"Uppskjutna av importtak: {summary.get('deferred', 0)}",
        f"Automatiska godkännanden: {reviewed} · "
        f"Statuskonflikter: {summary.get('review_conflicts', 0)}",
        "",
        "### Artiklar i körplanen",
        "",
        "<table><tr><th>PMID</th><th>Titel</th><th>Sökning</th></tr>",
    ]
    for entry in report["articles"]:
        article = entry["article"]
        topics = ", ".join(
            f"{p['search_id']} v{p['search_version']}" for p in entry["provenance"]
        )
        rows.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(v))}</td>"
                for v in (article["pmid"], article["title"] or "Titel saknas", topics)
            )
            + "</tr>"
        )
    rows += [
        "</table>",
        "",
        (
            "Kontrollera de importerade posterna manuellt i Zotero."
            if report["mode"] == "apply"
            else "Bedöm relevans och metadata före pilotimport."
        ),
    ]
    if report["mode"] == "dry-run":
        rows.append("Dry-run har inte ändrat Zotero.")
    return "\n".join(rows) + "\n"
