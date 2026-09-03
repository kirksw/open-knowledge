#!/usr/bin/env python3
"""Shared GitHub CLI helpers for the knowledge-agent pipeline scripts."""

from __future__ import annotations

import json
import os
import subprocess


def run(cmd: list[str], *, check=True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({' '.join(cmd[:4])}...): {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc


def gh(*args: str, check=True) -> subprocess.CompletedProcess:
    return run(["gh", *args], check=check)


def repo_from_env(default: str = "") -> str:
    return os.environ.get("GITHUB_REPOSITORY", default).strip()


def issue_labels(repo: str, issue_number: int) -> list[str]:
    proc = gh("api", f"repos/{repo}/issues/{issue_number}/labels")
    return [entry["name"] for entry in json.loads(proc.stdout)]


def set_labels(repo: str, issue_number: int, *, add: list[str] = (), remove: list[str] = ()) -> None:
    """Add and remove issue labels, tolerating labels that are absent."""
    current = set(issue_labels(repo, issue_number))
    for name in remove:
        if name in current:
            gh("issue", "edit", str(issue_number), "--repo", repo, "--remove-label", name)
            current.discard(name)
    to_add = [name for name in add if name not in current]
    if to_add:
        gh("issue", "edit", str(issue_number), "--repo", repo,
           *(arg for name in to_add for arg in ("--add-label", name)))


def issue_comment(repo: str, issue_number: int, body: str) -> None:
    gh("issue", "comment", str(issue_number), "--repo", repo, "--body", body)
