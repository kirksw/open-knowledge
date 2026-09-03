#!/usr/bin/env python3
"""Deterministic issue commenter for the knowledge-agent pipeline.

Modes:

- ``clarify``: post the single clarification question recorded in
  ``clarification.json``, add ``agent:needs-info``, and remove
  ``agent:working``.
- ``failed``: post a fixed failure notice linking the workflow run, include
  validation errors when ``validation.json`` records a rejection, add
  ``agent:failed``, and remove ``agent:working``.

Comment bodies are generated from fixed templates; the only variable data
is the agent's clarification question or validator error list.

Environment: GH_TOKEN, GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_SERVER_URL.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_ops import issue_comment, repo_from_env, set_labels  # noqa: E402

MAX_ERROR_LINES = 40


CLARIFY_TEMPLATE = """The knowledge agent needs one clarification before it can continue:

> {question}

Please answer by editing or commenting on this issue, remove the `agent:needs-info` label, then reapply `knowledge:ready` to restart the run.
"""

FAILED_TEMPLATE = """The knowledge-agent run for this issue failed and needs attention.

- Workflow run: {run_url}
- The `agent:working` label was removed; this issue now carries `agent:failed`.

Fix the underlying problem (for example repository secrets, model access, or a validation failure below), then remove `agent:failed` and reapply `knowledge:ready` to retry.
{validation_section}"""

VALIDATION_SECTION_TEMPLATE = """
Validation reported these problems:

```
{errors}
```
"""


def build_body(mode: str, work: Path) -> tuple[str, list[str], list[str]]:
    run_id = os.environ.get("GITHUB_RUN_ID", "unknown").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    repo = repo_from_env()
    run_url = f"{server}/{repo}/actions/runs/{run_id}"
    if mode == "clarify":
        path = work / "clarification.json"
        if not path.is_file():
            raise SystemExit("comment: clarification.json missing")
        question = json.loads(path.read_text(encoding="utf-8"))["question"].strip()
        return CLARIFY_TEMPLATE.format(question=question), ["agent:needs-info"], ["agent:working"]
    validation_section = ""
    path = work / "validation.json"
    if path.is_file():
        validation = json.loads(path.read_text(encoding="utf-8"))
        if validation.get("status") == "rejected" and validation.get("errors"):
            errors = "\n".join(validation["errors"][:MAX_ERROR_LINES])
            validation_section = VALIDATION_SECTION_TEMPLATE.format(errors=errors)
    body = FAILED_TEMPLATE.format(run_url=run_url, validation_section=validation_section)
    return body, ["agent:failed"], ["agent:working"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["clarify", "failed"], required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--issue", type=int, required=True)
    args = parser.parse_args(argv)

    if not os.environ.get("GH_TOKEN"):
        print("comment: GH_TOKEN must be set", file=sys.stderr)
        return 1
    repo = repo_from_env()
    if not repo:
        print("comment: GITHUB_REPOSITORY must be set", file=sys.stderr)
        return 1

    body, add, remove = build_body(args.mode, Path(args.work_dir))
    issue_comment(repo, args.issue, body)
    set_labels(repo, args.issue, add=add, remove=remove)
    print(f"comment: posted {args.mode} comment on issue #{args.issue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
