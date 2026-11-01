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
