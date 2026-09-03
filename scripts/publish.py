#!/usr/bin/env python3
"""Deterministic publisher for validated knowledge artifacts.

Receives only the validator-approved ``manifest.json`` and the staged
files. Creates the branch ``knowledge/<issue>-<slug>``, copies exactly the
manifest-listed files after re-verifying their hashes, commits with a fixed
template, pushes, opens a pull request, comments on the originating issue,
and manages workflow labels.

The publisher never merges a pull request, never touches workflow files or
repository settings, and refuses any path outside the approved manifest.

Environment: GH_TOKEN, GITHUB_REPOSITORY, GITHUB_RUN_ID (GITHUB_SERVER_URL
optional, defaults to https://github.com).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_ops import set_labels  # noqa: E402

BOT_NAME = "open-knowledge-agent"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
FORBIDDEN_PREFIXES = (".github/",)


def eprint(*args):
    print(*args, file=sys.stderr)


def run(cmd: list[str], *, check=True, input_text: str | None = None,
        cwd: Path | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True, input=input_text, cwd=cwd)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({' '.join(cmd[:4])}...): {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc


def gh(*args: str, check=True, input_text: str | None = None) -> subprocess.CompletedProcess:
    cmd = ["gh", *args]
    return run(cmd, check=check, input_text=input_text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def publish() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    work = Path(args.work_dir)
    repo_root = Path(args.repo_root).resolve()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID", "unknown").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    token = os.environ.get("GH_TOKEN", "").strip()
    if not repo or not token:
        eprint("publish: GITHUB_REPOSITORY and GH_TOKEN must be set")
        return 1

    manifest_path = work / "manifest.json"
    if not manifest_path.is_file():
        eprint("publish: manifest.json missing; nothing approved to publish")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("validation") != "approved":
        eprint("publish: manifest is not approved")
        return 1
    issue_number = manifest["issue"]["number"]
    issue_url = manifest["issue"].get("url") or f"{server}/{repo}/issues/{issue_number}"
    slug = manifest["slug"]

    default_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                         cwd=repo_root).stdout.strip() or "main"
    branch = manifest.get("branch") or f"knowledge/{issue_number}-{slug}"
    branch = re.sub(r"[^A-Za-z0-9._/-]+", "-", branch).strip("-/")[:200]
    if branch == default_branch:
        eprint("publish: refusing to push to the default branch")
        return 1

    staged = work / "staged"
    copies: list[tuple[Path, Path, str]] = []
    for entry in manifest["files"]:
        rel = entry["path"]
        pure = PurePosixPath(rel)
        if pure.is_absolute() or ".." in pure.parts:
            eprint(f"publish: refusing manifest path {rel!r}")
            return 1
        if any(rel.startswith(prefix) for prefix in FORBIDDEN_PREFIXES) or any(
            part.startswith(".") for part in pure.parts
        ):
            eprint(f"publish: refusing manifest path {rel!r}")
            return 1
        src = staged / rel
        if not src.is_file():
            eprint(f"publish: staged file missing for {rel}")
            return 1
        if sha256_file(src) != entry["sha256"]:
            eprint(f"publish: hash mismatch for {rel}; refusing to publish")
            return 1
        dst = repo_root / rel
        if dst.exists():
            if pure.parts[0] == "concepts":
                head = run(["git", "show", f"HEAD:{rel}"], cwd=repo_root, check=False)
                if head.returncode == 0 and "type: Concept" in head.stdout[:600]:
                    print(f"publish: updating existing concept {rel}")
                else:
                    eprint(f"publish: refusing to overwrite non-Concept file: {rel}")
                    return 1
            else:
                eprint(f"publish: target already exists on the default branch: {rel}")
                return 1
        copies.append((src, dst, rel))
    if not copies:
        eprint("publish: manifest contains no files")
        return 1

    existing = run(["git", "ls-remote", "--heads", "origin", branch], cwd=repo_root, check=False)
    if existing.stdout.strip():
        branch = f"{branch}-r{run_id}"[:200]
        print(f"publish: branch exists, using {branch}")

    gh("auth", "setup-git")
    run(["git", "config", "user.name", BOT_NAME], cwd=repo_root)
    run(["git", "config", "user.email", BOT_EMAIL], cwd=repo_root)
    run(["git", "checkout", "-b", branch], cwd=repo_root)
    rels = []
    for src, dst, rel in copies:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        rels.append(rel)
    run(["git", "add", "--", *rels], cwd=repo_root)
    commit_message = COMMIT_TEMPLATE.format(
        issue_number=issue_number,
        title=manifest["issue"].get("title", "").strip() or f"knowledge entry {slug}",
        files=", ".join(rels),
        run_id=run_id,
    )
    run(["git", "commit", "-m", commit_message], cwd=repo_root)
    run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=repo_root)

    source_urls = []
    request_path = work / "request.json"
    if request_path.is_file():
        request = json.loads(request_path.read_text(encoding="utf-8"))
        source_urls = [entry["url"] for entry in request.get("urls", [])]
    pr_body = PR_TEMPLATE.format(
        issue_number=issue_number,
        issue_url=issue_url,
        source_urls="\n".join(f"- {u}" for u in source_urls) or "- (none recorded)",
        files="\n".join(f"- `{rel}`" for rel in rels),
        caveats="\n".join(f"- {c}" for c in manifest.get("caveats", [])) or "- none recorded",
        run_id=run_id,
        run_url=f"{server}/{repo}/actions/runs/{run_id}",
    )
    pr_title = f"Knowledge entry: {manifest['issue'].get('title', '').strip()} (#{issue_number})"
    pr_url = gh("pr", "create", "--repo", repo, "--base", default_branch, "--head", branch,
                "--title", pr_title, "--body", pr_body).stdout.strip()
    print(f"publish: pull request opened: {pr_url}")

    comment = ISSUE_COMMENT_TEMPLATE.format(pr_url=pr_url, files=", ".join(rels))
    gh("issue", "comment", str(issue_number), "--repo", repo, "--body", comment)
    set_labels(repo, issue_number, add=["agent:pr-open"], remove=["agent:working", "agent:needs-info"])
    print(f"publish: issue #{issue_number} updated (agent:pr-open)")
    return 0


COMMIT_TEMPLATE = """Add knowledge entry for issue #{issue_number}: {title}

Deliverables: {files}

Validated by the knowledge-agent pipeline (run {run_id}); manifest hashes verified.
Human review is required before merge.
"""

PR_TEMPLATE = """## Knowledge entry for issue #{issue_number}

Requested in {issue_url}.

### Sources

{source_urls}

### Changed files

{files}

### Validation

Deterministic validation approved; content hashes recorded in the run manifest.

### Caveats requiring review

{caveats}

### Provenance

Generated by the knowledge-agent pipeline ([run {run_id}]({run_url})).
The agent never merges this pull request; a human review and merge is required.

Closes #{issue_number}
"""

ISSUE_COMMENT_TEMPLATE = """A reviewable pull request has been opened for this knowledge request: {pr_url}

Changed files: {files}

The agent does not merge pull requests; please review and merge, or close and toggle the `knowledge:ready` label off and on again after updating this issue.
"""

if __name__ == "__main__":
    raise SystemExit(publish())
