#!/usr/bin/env python3
"""Deterministic coordinator for knowledge issues.

Reads the trusted GitHub `issues.labeled` event payload, re-verifies the
trust gate, parses the issue form, and writes either:

- ``request.json``  when the request is actionable, or
- ``clarification.json`` when one focused owner question is required.

The coordinator never mutates Git and never touches the network beyond the
filesystem. Exit codes: 0 = handoff written, 3 = event ignored (not a
trusted run), 1 = infrastructure error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MAX_URLS = 8
READY_LABEL = "knowledge:ready"

POLICY_FILES = [
    "AGENTS.md",
    "docs/okf.md",
    "docs/publication-policy.md",
    "templates/source-record.md",
    "templates/wiki-page.md",
    "templates/output.md",
]

SECTION_ALIASES = {
    "source urls": "urls",
    "what is interesting / desired angle": "angle",
    "requested deliverables": "deliverables",
    "output document specification": "output_spec",
    "publication constraints or caveats": "constraints",
}

TOKEN_RE = re.compile(r"https?://\S+")


def eprint(*args):
    print(*args, file=sys.stderr)


def trust_check(event: dict, owner: str) -> str | None:
    """Return a refusal reason, or None when the event is a trusted run start."""
    issue = event.get("issue") or {}
    label = event.get("label") or {}
    sender = (event.get("sender") or {}).get("login", "")
    if (label.get("name") or "") != READY_LABEL:
        return f"label is not {READY_LABEL}"
    if (issue.get("user") or {}).get("login") != owner:
        return "issue author is not the owner"
    if issue.get("author_association") != "OWNER":
        return "issue author association is not OWNER"
    if sender != owner:
        return "actor is not the owner"
    if issue.get("state") != "open":
        return "issue is not open"
    if any(l.get("name") == "agent:working" for l in issue.get("labels", [])):
        return "an agent run is already active"
    return None


def parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    chunks: dict[str, list[str]] = {}
    for line in (body or "").splitlines():
        m = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
        if m:
            heading = m.group(1).strip().lower().rstrip(":")
            current = SECTION_ALIASES.get(heading)
            if current and current not in chunks:
                chunks[current] = []
            continue
        if current:
            chunks[current].append(line)
    for key, lines in chunks.items():
        sections[key] = "\n".join(lines).strip()
    return sections


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    for token in TOKEN_RE.findall(text or ""):
        url = token.strip("`<>()[]\"',.")
        if url not in urls:
            urls.append(url)
    return urls


def check_url_syntax(url: str) -> str | None:
    from urllib.parse import urlsplit

    try:
        parts = urlsplit(url)
    except ValueError as exc:
        return f"unparseable URL {url!r}: {exc}"
    if parts.scheme not in ("http", "https"):
        return f"{url!r}: only http(s) URLs are accepted"
    if not parts.hostname:
        return f"{url!r}: missing hostname"
    if "@" in (parts.netloc or ""):
        return f"{url!r}: userinfo in URLs is not accepted"
    host = parts.hostname
    if not re.fullmatch(r"[a-z0-9.-]+", host, re.IGNORECASE):
        return f"{url!r}: invalid hostname {host!r}"
    lowered = host.lower()
    if lowered in ("localhost", "localhost.localdomain") or lowered.endswith(".localhost") or lowered.endswith(".local"):
        return f"{url!r}: local hostname rejected"
    if parts.port is not None and not (1 <= parts.port <= 65535):
        return f"{url!r}: invalid port"
    return None


def parse_deliverables(text: str) -> tuple[dict[str, bool], list[str]]:
    """Return ({source_record, wiki_page, output}, missing-checkbox labels)."""
    found = {"source_record": False, "wiki_page": False, "output": False}
    patterns = [
        ("source_record", re.compile(r"source record", re.I)),
        ("wiki_page", re.compile(r"wiki page", re.I)),
        ("output", re.compile(r"output document", re.I)),
    ]
    any_checkbox = False
    for line in (text or "").splitlines():
        m = re.match(r"^\s*[-*]\s*\[( |x|X)\]\s*(.*)$", line)
        if not m:
            continue
        any_checkbox = True
        checked, label = m.group(1).lower() == "x", m.group(2)
        for key, pattern in patterns:
            if pattern.search(label):
                found[key] = checked
    missing = [] if any_checkbox else ["Requested deliverables checkboxes"]
    return found, missing


OUTPUT_NAME_RE = re.compile(r"outputs/([A-Za-z0-9][A-Za-z0-9._-]*\.(?:md|txt))")


def derive_output_filename(spec: str, slug: str) -> str | None:
    m = OUTPUT_NAME_RE.search(spec or "")
    if m:
        return m.group(1)
    if re.search(r"\.(md|txt)\b", spec or "", re.I):
        return f"{slug}.{re.search(r'\.(md|txt)\b', spec, re.I).group(1).lower()}"
    return f"{slug}.md"


SLUG_STRIP_RE = re.compile(r"^\s*\[?knowledge\]?\s*:?\s*", re.IGNORECASE)


def slugify(title: str, issue_number: int, repo_root: Path) -> str:
    text = SLUG_STRIP_RE.sub("", title or "")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = text[:48].strip("-")
    if not text:
        text = "entry"
    attempt = 0
    while True:
        slug = text if attempt == 0 else f"{text}-{issue_number + attempt - 1}"
        clash = any(
            (repo_root / directory / f"{slug}{ext}").exists()
            for directory in ("sources", "docs", "concepts", "outputs")
            for ext in (".md", ".txt")
        )
        if not clash:
            return slug
        attempt += 1


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-file", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--owner-login", default="kirksw")
    args = parser.parse_args(argv)

    event = json.loads(Path(args.event_file).read_text(encoding="utf-8"))
    repo_root = Path(args.repo_root).resolve()

    reason = trust_check(event, args.owner_login)
    if reason:
        eprint(f"coordinator: ignoring event ({reason})")
        return 3

    issue = event["issue"]
    number = issue["number"]
    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)

    missing_policy = [p for p in POLICY_FILES if not (repo_root / p).is_file()]
    if missing_policy:
        eprint(f"coordinator: repository policy files missing: {', '.join(missing_policy)}")
        return 1

    body = issue.get("body") or ""
    sections = parse_sections(body)

    def clarify(question: str) -> int:
        write_json(work / "clarification.json", {"version": 1, "issue": number, "question": question})
        print(f"coordinator: clarification requested for issue #{number}")
        return 0

    if not sections and not body.strip():
        return clarify(
            "The issue body is empty. Please edit the issue to use the *Knowledge entry* issue form "
            "(source URLs, angle, deliverables, constraints), then toggle the `knowledge:ready` label off and on again."
        )

    urls_raw = extract_urls(sections.get("urls", ""))
    if not urls_raw:
        return clarify(
            "No canonical source URL was found. Please edit the issue to add at least one public "
            "http(s) source URL under *Source URLs*, then toggle the `knowledge:ready` label off and on again."
        )
    if len(urls_raw) > MAX_URLS:
        return clarify(
            f"The issue lists {len(urls_raw)} source URLs; the maximum is {MAX_URLS}. Please edit the "
            "issue down to the most canonical sources, then toggle the `knowledge:ready` label off and on again."
        )
    bad = [err for url in urls_raw if (err := check_url_syntax(url))]
    if bad:
        return clarify(
            "A source URL could not be accepted: " + "; ".join(bad)
            + ". Please edit the issue, then toggle the `knowledge:ready` label off and on again."
        )

    angle = sections.get("angle", "").strip()
    if not angle:
        return clarify(
            "The research angle is empty. Please edit the issue to describe briefly what is interesting "
            "or what the summary should answer, then toggle the `knowledge:ready` label off and on again."
        )

    deliverables, missing = parse_deliverables(sections.get("deliverables", ""))
    if missing:
        return clarify(
            "The deliverables checkboxes are missing. Please edit the issue using the *Knowledge entry* "
            "form and select the requested deliverables, then toggle the `knowledge:ready` label off and on again."
        )
    if not any(deliverables.values()):
        return clarify(
            "No deliverables are selected. Please select at least one of source record, wiki page, or "
            "output document, then toggle the `knowledge:ready` label off and on again."
        )

    output_requested = deliverables["output"]
    output_spec = sections.get("output_spec", "").strip()
    slug = slugify(issue.get("title") or "", number, repo_root)
    if output_requested and not output_spec:
        return clarify(
            "The output document deliverable is selected but its specification is empty. Please edit the "
            "issue to describe the single Markdown or plain-text artifact wanted, then toggle the `knowledge:ready` label off and on again."
        )

    request = {
        "version": 1,
        "issue": {
            "number": number,
            "title": issue.get("title") or "",
            "url": issue.get("html_url") or "",
            "author": (issue.get("user") or {}).get("login", ""),
        },
        "repo": {
            "full_name": (event.get("repository") or {}).get("full_name", ""),
            "default_branch": (event.get("repository") or {}).get("default_branch", "main"),
        },
        "urls": [{"id": "primary" if i == 0 else f"s{i + 1}", "url": url} for i, url in enumerate(urls_raw)],
        "angle": angle,
        "deliverables": {
            "source_record": deliverables["source_record"],
            "wiki_page": deliverables["wiki_page"],
            "output": {
                "requested": output_requested,
                "spec": output_spec,
                "filename": derive_output_filename(output_spec, slug) if output_requested else None,
            },
        },
        "constraints": sections.get("constraints", "").strip(),
        "slug": slug,
        "policy_files": POLICY_FILES,
    }
    write_json(work / "request.json", request)
    print(f"coordinator: request accepted for issue #{number} (slug {slug!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
