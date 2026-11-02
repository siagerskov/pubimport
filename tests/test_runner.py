import importlib.util
from pathlib import Path

import pytest


def runner():
    path = Path(__file__).parents[1] / "scripts/run_sync.py"
    spec = importlib.util.spec_from_file_location("run_sync", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("mode", ["offline", "dry-run", "apply"])
def test_workflow_modes_do_not_evaluate_input(monkeypatch, mode):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    module = runner()
    calls = []
    monkeypatch.setattr(module, "main", lambda args: calls.append(args) or 0)
    monkeypatch.setenv("SYNC_MODE", mode)
    monkeypatch.setenv("SYNC_LIMIT", "5; echo should-never-run")
    monkeypatch.setenv("CONFIRM_LIBRARY", "123")
    assert module.run() == 0
    args = calls[0]
    if mode == "offline":
        assert "--live" not in args and "--apply" not in args
    else:
        assert "5; echo should-never-run" in args
        assert ("--apply" in args) == (mode == "apply")


def test_workflow_rejects_unknown_mode(monkeypatch):
    monkeypatch.setenv("SYNC_MODE", "invalid")
    assert runner().run() == 2


def test_offline_runner_writes_actions_summary(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(Path(__file__).parents[1])
    monkeypatch.setenv("SYNC_MODE", "offline")
    path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(path))
    assert runner().run() == 0
    summary = path.read_text()
    assert "Nya: 2" in summary
    assert "Importerade: 0" in summary
    assert '"mode": "dry-run"' in capsys.readouterr().out


def test_runner_forwards_retrospective_dates_and_separate_search_ids(monkeypatch):
    module = runner()
    calls = []
    monkeypatch.setattr(module, "main", lambda args: calls.append(args) or 0)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setenv("SYNC_MODE", "dry-run")
    monkeypatch.setenv("SYNC_FROM_DATE", "2018-01-01")
    monkeypatch.setenv("SYNC_UNTIL_DATE", "2018-12-31")
    monkeypatch.setenv("SYNC_SEARCH_IDS", "nph, ai-radiology")
    assert module.run() == 0
    args = calls[0]
    assert args[args.index("--from-date") + 1] == "2018-01-01"
    assert args[args.index("--until-date") + 1] == "2018-12-31"
    assert args.count("--search-id") == 2
    assert "--apply" not in args
