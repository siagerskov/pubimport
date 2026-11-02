"""Publish safe counters to automation-status, never to the application's branch."""

import base64
import json
import os
import re
import sys
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BRANCH = "automation-status"
FILE = "automation-status.json"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def publish(repository, token, commit, status, opener=None, kind="import"):
    if kind not in {"import", "review"}:
        raise ValueError("Invalid status kind")
    branch = BRANCH if kind == "import" else "review-status"
    filename = FILE if kind == "import" else "review-status.json"
    opener = opener or build_opener(NoRedirect()).open
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid repository")
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not token:
        raise ValueError("Missing publication identity")
    base = f"https://api.github.com/repos/{repository}/"

    def request(method, path, data=None, missing_ok=False):
        body = json.dumps(data).encode() if data is not None else None
        req = Request(
            base + path,
            data=body,
            method=method,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with opener(req, timeout=30) as response:
                return json.load(response)
        except HTTPError as exc:
            code = exc.code
            exc.close()
            if missing_ok and code == 404:
                return None
            raise RuntimeError(
                f"Statusfilen kunde inte sparas (HTTP {code})."
            ) from None
        except (OSError, URLError, ValueError):
            raise RuntimeError("Statusfilens nätverksanrop misslyckades.") from None

    if request("GET", "git/ref/heads/" + branch, missing_ok=True) is None:
        request("POST", "git/refs", {"ref": "refs/heads/" + branch, "sha": commit})
    old = request("GET", "contents/" + filename + "?ref=" + branch, missing_ok=True)
    body = {
        "message": "Update automation run status",
        "branch": branch,
        "content": base64.b64encode(
            json.dumps(status, ensure_ascii=False, indent=2).encode()
        ).decode(),
    }
    if old:
        body["sha"] = old["sha"]
    request("PUT", "contents/" + filename, body)


def run():
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    raw = json.loads(os.environ.get("IMPORT_SUMMARY") or "{}")
    # Whitelist integer counters; never publish payloads, notes, titles or credentials.
    counters = {
        k: v
        for k, v in raw.items()
        if k
        in {
            "new",
            "known",
            "metadata_missing",
            "actions",
            "imported",
            "errors",
            "deferred",
            "completed_actions",
            "review_updates",
            "review_conflicts",
            "reviews_completed",
        }
        and type(v) is int
    }
    status = {
        "observed_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "result": os.environ.get("SYNC_RESULT", "unknown"),
        "event": os.environ.get("GITHUB_EVENT_NAME", ""),
        "mode": os.environ.get("RUN_MODE", ""),
        "import_summary": counters,
        "tag_fix": os.environ.get("TAG_FIX_RESULT", ""),
        "commit": os.environ.get("GITHUB_SHA", ""),
    }
    publish(
        repository,
        os.environ.get("GITHUB_TOKEN", ""),
        status["commit"],
        status,
        kind=os.environ.get("STATUS_KIND", "import"),
    )
    print("Körstatus sparad på separat statusgren.")


if __name__ == "__main__":
    try:
        run()
    except (RuntimeError, ValueError, KeyError) as exc:
        # Log fixed public errors only; never raw response data.
        print(
            str(exc)
            if isinstance(exc, RuntimeError)
            else "Statusfilen kunde inte sparas.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
