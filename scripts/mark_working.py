#!/usr/bin/env python3
"""Accept a trusted run and mark the issue as being processed.

Re-verifies the trust gate against the live issue (defense in depth beyond
the workflow-level event conditions), refuses to proceed when another run is
already active (``agent:working``), then atomically applies ``agent:working``
and clears ``agent:needs-info``.

Writes ``proceed=true|false`` and ``duplicate=true|false`` to the GitHub
Actions job output file so the workflow can stop cleanly without marking a
failure.

Environment: GH_TOKEN, GITHUB_REPOSITORY, GITHUB_OUTPUT.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_ops import gh, issue_labels, repo_from_env, set_labels  # noqa: E402


def job_output(key: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{key}={value}\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--owner", default="kirksw")
    args = parser.parse_args(argv)

    if not os.environ.get("GH_TOKEN"):
        print("mark-working: GH_TOKEN must be set", file=sys.stderr)
        return 1
    repo = repo_from_env()
    if not repo:
        print("mark-working: GITHUB_REPOSITORY must be set", file=sys.stderr)
        return 1

    issue = json.loads(gh("api", f"repos/{repo}/issues/{args.issue}").stdout)
    if issue.get("state") != "open":
        print(f"mark-working: issue #{args.issue} is not open; ignoring")
        job_output("proceed", "false")
        return 0
    author = (issue.get("user") or {}).get("login")
    association = issue.get("author_association")
    if author != args.owner or association != "OWNER":
        print(
            f"mark-working: trust re-check failed (author={author!r}, "
            f"association={association!r}); ignoring"
        )
        job_output("proceed", "false")
        return 0

    labels = issue_labels(repo, args.issue)
    if "knowledge:ready" not in labels:
        print("mark-working: knowledge:ready is not currently applied; ignoring")
        job_output("proceed", "false")
        return 0
    if "agent:working" in labels:
        print("mark-working: another run is active on this issue; skipping as duplicate")
        job_output("proceed", "false")
        job_output("duplicate", "true")
        return 0

    set_labels(repo, args.issue, add=["agent:working"], remove=["agent:needs-info"])
    print(f"mark-working: issue #{args.issue} accepted; agent:working applied")
    job_output("proceed", "true")
    job_output("duplicate", "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
