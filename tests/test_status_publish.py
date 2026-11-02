import base64
import importlib.util
import io
import json
from pathlib import Path
from urllib.error import HTTPError


def publisher():
    path = Path(__file__).parents[1] / "scripts/publish_status.py"
    spec = importlib.util.spec_from_file_location("publish_status", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_status_writes_only_isolated_branch_and_never_token_into_file():
    requests = []
    responses = iter(
        [
            HTTPError("secret", 404, "SECRET", {}, None),
            {},
            HTTPError("secret", 404, "SECRET", {}, None),
            {},
        ]
    )

    def opener(request, timeout):
        requests.append(request)
        value = next(responses)
        if isinstance(value, Exception):
            raise value
        return io.BytesIO(json.dumps(value).encode())

    publisher().publish(
        "siagerskov/pubimport",
        "SECRET",
        "a" * 40,
        {"result": "success", "import_summary": {"imported": 10}},
        opener,
    )
    posts = [json.loads(r.data) for r in requests if r.data]
    assert posts[0]["ref"] == "refs/heads/automation-status"
    assert posts[1]["branch"] == "automation-status"
    content = base64.b64decode(posts[1]["content"]).decode()
    assert "SECRET" not in content
    assert json.loads(content)["import_summary"]["imported"] == 10
    assert all(
        r.full_url.startswith("https://api.github.com/repos/siagerskov/pubimport/")
        for r in requests
    )


def test_status_output_whitelists_only_integer_counters(monkeypatch):
    module = publisher()
    captured = []
    monkeypatch.setattr(module, "publish", lambda *args: captured.append(args[-1]))
    monkeypatch.setenv("GITHUB_REPOSITORY", "siagerskov/pubimport")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv(
        "IMPORT_SUMMARY",
        json.dumps(
            {
                "imported": 3,
                "known": 4,
                "extra": "PRIVATE",
                "new": "SECRET",
                "errors": False,
            }
        ),
    )
    module.run()
    assert captured[0]["import_summary"] == {"imported": 3, "known": 4}
    assert "SECRET" not in json.dumps(captured[0])
    assert "PRIVATE" not in json.dumps(captured[0])
