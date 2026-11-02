from pubmed_zotero.reporting import action_summary


def test_actions_summary_reports_counts_and_escapes_untrusted_titles():
    report = {
        "mode": "dry-run",
        "summary": {"total_hits": 20, "unique_pmids": 1, "truncated": True},
        "sync": {
            "summary": {"new": 1, "known": 0, "metadata_missing": 0, "imported": 0}
        },
        "articles": [
            {
                "article": {"pmid": "123", "title": "<script>untrusted</script>"},
                "provenance": [{"search_id": "msk-radiology", "search_version": "3"}],
            }
        ],
    }
    summary = action_summary(report)
    assert "<script>" not in summary
    assert "&lt;script&gt;" in summary
    assert "Nya: 1" in summary and "Importerade: 0" in summary
    assert "Trunkerat urval: ja" in summary
    assert "msk-radiology v3" in summary
    assert "inte ändrat Zotero" in summary
