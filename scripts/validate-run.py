#!/usr/bin/env python3
"""Deterministic validation of staged knowledge artifacts.

Checks the staged directory produced by the synthesis and output agents
against repository policy and writes ``validation.json`` plus, on success,
``manifest.json`` with the approved paths and content hashes.

Validation is read-only, offline, and fails closed. It rejects changes that:

- target paths outside ``sources/``, ``docs/``, ``concepts/``, and ``outputs/``;
- use disallowed file types, hidden files, or reserved OKF filenames;
- do not match the deliverables declared in ``request.json`` (plus 1-8 concept pages);
- overwrite files that already exist on the default branch, except concept
  updates that keep every previously recorded source (accumulation);
- fail OKF v0.2 frontmatter rules or the per-type template contract;
- cite a footnote source ID missing from the ``sources`` frontmatter;
- contain credentials, private addresses, oversized or binary content;
- omit the originating-issue link (source record) or source-record link
  (knowledge summary).

Exit codes: 0 = approved (manifest written), 1 = rejected (errors recorded).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mini_yaml import MiniYAMLError, split_frontmatter  # noqa: E402

ALLOWED_ROOTS = {"sources": ".md", "docs": ".md", "concepts": ".md", "outputs": None}  # None = per-file rule
OUTPUT_EXTS = {"md", ".txt"}
RESERVED_NAMES = {"index.md", "log.md"}
MAX_FILE_BYTES = 300 * 1024
MAX_TOTAL_BYTES = 1024 * 1024
SUMMARY_SECTIONS = ("Answer", "Key concepts", "Evidence", "Caveats", "References")
CONCEPT_SECTIONS = ("Statement", "Evidence", "Caveats", "Related")
MAX_CONCEPTS = 8

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY( BLOCK)?-----"), "private key material"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b"), "GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{16,}\b"), "GitHub fine-grained token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"), "API key (sk-)"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b"), "Google API key"),
    (re.compile(r"\bCF-Access-Client", re.I), "Cloudflare Access service-token header"),
    (re.compile(r"\bLITELLM_[A-Z_]+\b"), "LiteLLM credential reference"),
    (re.compile(r"\b169\.254\.169\.254\b"), "cloud metadata endpoint address"),
    (re.compile(r"\bmetadata\.google\.internal\b"), "cloud metadata hostname"),
    (re.compile(r"\b(10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "private/loopback IPv4 address"),
    (re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"), "private IPv4 address"),
    (re.compile(r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b"), "private IPv4 address"),
    (re.compile(r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"), "carrier-grade NAT address"),
]
FOOTNOTE_REF_RE = re.compile(r"\[\^([A-Za-z0-9_-]+)\]")
FOOTNOTE_DEF_RE = re.compile(r"^\s*\[\^([A-Za-z0-9_-]+)\]:", re.MULTILINE)


def eprint(*args):
    print(*args, file=sys.stderr)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_path(rel: str, errors: list[str]) -> PurePosixPath | None:
    pure = PurePosixPath(rel)
    if pure.is_absolute() or rel.startswith("/") or ".." in pure.parts:
        errors.append(f"{rel}: absolute or parent-traversing paths are not allowed")
        return None
    parts = pure.parts
    if not parts or parts[0] not in ALLOWED_ROOTS:
        errors.append(f"{rel}: path outside allowed directories (sources/, docs/, outputs/)")
        return None
    if any(part.startswith(".") for part in parts):
        errors.append(f"{rel}: hidden path segments are not allowed")
        return None
    if pure.name in RESERVED_NAMES:
        errors.append(f"{rel}: reserved OKF filename")
        return None
    ext = pure.suffix.lower()
    root = parts[0]
    if root == "outputs":
        if ext not in OUTPUT_EXTS:
            errors.append(f"{rel}: outputs/ allows only .md and .txt files")
            return None
    elif ext != ".md":
        errors.append(f"{rel}: {root}/ allows only .md files")
        return None
    return pure


def scan_content(rel: str, data: bytes, errors: list[str]) -> str | None:
    if b"\x00" in data:
        errors.append(f"{rel}: binary content (NUL byte) is not allowed")
        return None
    if len(data) > MAX_FILE_BYTES:
        errors.append(f"{rel}: file exceeds {MAX_FILE_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{rel}: file is not valid UTF-8 text")
        return None
    for pattern, label in SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            snippet = match.group(0)[:12]
            errors.append(f"{rel}: content matches {label} (near {snippet!r})")
    # Bare hexadecimal blobs look like credentials, except when the same line
    # labels them as a content hash (sha1/sha256/sha512/checksum/digest),
    # which is legitimate provenance for fetched sources.
    hash_label = re.compile(r"sha-?(?:1|256|512)|checksum|digest", re.I)
    for match in re.finditer(r"\b[a-fA-F0-9]{40,}\b", text):
        line_start = text.rfind("\n", 0, match.start()) + 1
        prefix = text[line_start : match.start()]
        if hash_label.search(prefix[-40:]):
            continue
        errors.append(
            f"{rel}: content matches hexadecimal secret-sized string (near {match.group(0)[:12]!r})"
        )
        break
    return text


def sources_ids(fm: dict, rel: str, errors: list[str]) -> list[dict]:
    entries = fm.get("sources")
    if not isinstance(entries, list) or not entries:
        errors.append(f"{rel}: sources frontmatter must be a non-empty list")
        return []
    ids = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(f"{rel}: sources entries must be mappings with id, resource, title")
            continue
        for fieldname in ("id", "resource", "title"):
            value = entry.get(fieldname)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{rel}: sources entry missing non-empty {fieldname}")
        entry_id = entry.get("id")
        if isinstance(entry_id, str) and entry_id:
            if entry_id in ids:
                errors.append(f"{rel}: duplicate sources id {entry_id!r}")
            ids.append(entry_id)
    return entries


def check_citations(text: str, fm: dict, rel: str, errors: list[str]) -> None:
    entries = fm.get("sources") if isinstance(fm.get("sources"), list) else []
    known = {e.get("id") for e in entries if isinstance(e, dict)}
    cited = set(FOOTNOTE_REF_RE.findall(text))
    for foot_id in sorted(cited):
        if foot_id not in known:
            errors.append(
                f"{rel}: footnote source id {foot_id!r} is not present in sources frontmatter"
            )


def check_generated(fm: dict, rel: str, errors: list[str]) -> None:
    generated = fm.get("generated")
    if not isinstance(generated, dict):
        errors.append(f"{rel}: generated frontmatter must map by/at for agent-written content")
        return
    for fieldname in ("by", "at"):
        value = generated.get(fieldname)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{rel}: generated.{fieldname} must be non-empty")
    at = generated.get("at")
    if isinstance(at, str) and at:
        try:
            datetime.fromisoformat(at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{rel}: generated.at is not an ISO-8601 timestamp")


def check_common_frontmatter(fm: dict, rel: str, expected_type: str, errors: list[str],
                             description_optional=False) -> None:
    if fm is None:
        errors.append(f"{rel}: missing OKF frontmatter")
        return
    if fm.get("type") != expected_type:
        errors.append(f"{rel}: type must be {expected_type!r}, got {fm.get('type')!r}")
    for fieldname in ("title", "description"):
        value = fm.get(fieldname)
        if fieldname == "description" and description_optional:
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{rel}: {fieldname} must be a non-empty string")
    if fm.get("status") != "draft":
        errors.append(f"{rel}: agent-written content must keep status: draft")
    if fm.get("verified") is not None:
        errors.append(f"{rel}: verified may only be added by a human or deterministic check")
    check_generated(fm, rel, errors)
    sources_ids(fm, rel, errors)


def concept_update_allowed(target: Path, staged_path: Path, rel: str, errors: list[str]) -> bool:
    """A concept page may be updated, but only over an existing Concept whose
    recorded sources never shrink (deterministic accumulation guarantee)."""
    try:
        existing_fm, _ = split_frontmatter(target.read_text(encoding="utf-8"))
        staged_fm, _ = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    except (MiniYAMLError, OSError, UnicodeDecodeError) as exc:
        errors.append(f"{rel}: existing or staged concept could not be parsed: {exc}")
        return False
    if not isinstance(existing_fm, dict) or not isinstance(staged_fm, dict):
        return False
    if existing_fm.get("type") != "Concept":
        errors.append(f"{rel}: refusing to overwrite a non-Concept file at this path")
        return False
    if staged_fm.get("type") != "Concept":
        return False
    existing_resources = {
        e.get("resource")
        for e in (existing_fm.get("sources") or [])
        if isinstance(e, dict)
    }
    staged_resources = {
        e.get("resource")
        for e in (staged_fm.get("sources") or [])
        if isinstance(e, dict)
    }
    dropped = existing_resources - staged_resources
    if dropped:
        errors.append(
            f"{rel}: concept update must not drop previously recorded sources ({', '.join(sorted(map(str, dropped)))})"
        )
        return False
    return True


def validate_file(path: Path, rel: str, request: dict, repo_root: Path, errors: list[str]) -> None:
    pure = PurePosixPath(rel)
    data = path.read_bytes()
    text = scan_content(rel, data, errors)
    if text is None:
        return
    slug = request["slug"]
    deliverables = request["deliverables"]
    issue = request["issue"]

    if pure.suffix == ".txt":
        return  # plain-text outputs: content and path rules only

    try:
        fm, body = split_frontmatter(text)
    except MiniYAMLError as exc:
        errors.append(f"{rel}: frontmatter error: {exc}")
        return

    if pure.parts[0] == "sources":
        check_common_frontmatter(fm, rel, "Source Record", errors)
        if fm:
            resource = fm.get("resource")
            if not isinstance(resource, str) or not re.match(r"^https?://", resource):
                errors.append(f"{rel}: resource must be the canonical http(s) URL")
            if fm.get("issue") != issue["number"]:
                errors.append(f"{rel}: issue must be {issue['number']}")
            if issue.get("url") and issue["url"] not in body:
                errors.append(f"{rel}: body must link the originating issue")
            check_citations(body, fm, rel, errors)
    elif pure.parts[0] == "docs":
        check_common_frontmatter(fm, rel, "Knowledge Summary", errors)
        if fm:
            entries = sources_ids(fm, rel, errors)
            record_resource = f"/sources/{slug}.md"
            if not any(isinstance(e, dict) and e.get("resource") == record_resource for e in entries):
                errors.append(f"{rel}: sources frontmatter must include the record entry {record_resource!r}")
            if record_resource not in body:
                errors.append(f"{rel}: body must link the source record {record_resource}")
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)
            normalized = {h.strip().lower() for h in headings}
            for section in SUMMARY_SECTIONS:
                if section.lower() not in normalized:
                    errors.append(f"{rel}: missing required section '# {section}'")
            check_citations(body, fm, rel, errors)
    elif pure.parts[0] == "concepts":
        check_common_frontmatter(fm, rel, "Concept", errors, description_optional=True)
        if fm:
            statement = fm.get("statement")
            if not isinstance(statement, str) or not statement.strip():
                errors.append(f"{rel}: statement must be a non-empty one-sentence claim")
            entries = sources_ids(fm, rel, errors)
            record_resources = {
                e.get("resource") for e in entries if isinstance(e, dict) and e.get("resource", "").startswith("/sources/")
            }
            if not record_resources:
                errors.append(f"{rel}: sources frontmatter must reference at least one /sources/ record")
            related = fm.get("related", [])
            if related is None:
                related = []
            if not isinstance(related, list):
                errors.append(f"{rel}: related must be a list of /concepts/ paths")
            else:
                for link in related:
                    if not isinstance(link, str) or not re.match(r"^/concepts/[a-z0-9-]+\.md$", link):
                        errors.append(f"{rel}: related entries must be /concepts/<slug>.md paths")
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)
            normalized = {h.strip().lower() for h in headings}
            for section in CONCEPT_SECTIONS:
                if section.lower() not in normalized:
                    errors.append(f"{rel}: missing required section '# {section}'")
            check_citations(body, fm, rel, errors)
    else:  # outputs/*.md
        check_common_frontmatter(fm, rel, "Output", errors)
        if fm:
            if fm.get("issue") != issue["number"]:
                errors.append(f"{rel}: issue must be {issue['number']}")
            entries = sources_ids(fm, rel, errors)
            record_resource = f"/sources/{slug}.md"
            if not any(isinstance(e, dict) and e.get("resource") == record_resource for e in entries):
                errors.append(f"{rel}: sources frontmatter must reference the record entry {record_resource!r}")
            check_citations(body, fm, rel, errors)


def validate() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    work = Path(args.work_dir)
    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []

    request_path = work / "request.json"
    if not request_path.is_file():
        eprint("validate-run: request.json missing")
        return 1
    request = json.loads(request_path.read_text(encoding="utf-8"))
    issue_number = request["issue"]["number"]
    slug = request["slug"]
    deliverables = request["deliverables"]

    staged = work / "staged"
    if not staged.is_dir():
        eprint("validate-run: staged/ directory missing")
        return 1
    staged_files = sorted(
        str(p.relative_to(staged)) for p in staged.rglob("*") if p.is_file()
    )

    expected: dict[str, bool] = {}
    if deliverables["source_record"]:
        expected[f"sources/{slug}.md"] = True
    if deliverables["wiki_page"]:
        expected[f"docs/{slug}.md"] = True
    if deliverables["output"]["requested"]:
        expected[f"outputs/{deliverables['output']['filename']}"] = True

    concept_files = [rel for rel in staged_files if PurePosixPath(rel).parts[0] == "concepts"]
    if not (1 <= len(concept_files) <= MAX_CONCEPTS):
        errors.append(
            f"concepts: staged runs must extract between 1 and {MAX_CONCEPTS} concept pages (found {len(concept_files)})"
        )

    for rel in staged_files:
        if rel not in expected and PurePosixPath(rel).parts[0] != "concepts":
            errors.append(f"{rel}: staged file is not part of the requested deliverables")
    for rel in expected:
        if rel not in staged_files:
            errors.append(f"{rel}: required deliverable is missing from staged files")

    manifest_files = []
    total = 0
    for rel in staged_files:
        path = staged / rel
        pure = check_path(rel, errors)
        target = repo_root / rel if pure else None
        if pure is not None and target is not None and target.exists():
            if pure.parts[0] == "concepts" and concept_update_allowed(target, path, rel, errors):
                pass  # concept update: allowed, accumulation already checked
            else:
                errors.append(f"{rel}: a file already exists at this path on the default branch")
        if pure is None:
            continue
        size = path.stat().st_size
        total += size
        validate_file(path, rel, request, repo_root, errors)
        manifest_files.append({
            "path": rel,
            "sha256": sha256_file(path),
            "bytes": size,
        })
    if total > MAX_TOTAL_BYTES:
        errors.append(f"staged content exceeds total budget of {MAX_TOTAL_BYTES} bytes")

    caveats = []
    draft_path = work / "draft.json"
    if draft_path.is_file():
        try:
            draft = json.loads(draft_path.read_text(encoding="utf-8"))
            caveats = [str(c) for c in draft.get("caveats", []) if str(c).strip()]
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"draft.json could not be read: {exc}")

    status = "approved" if not errors else "rejected"
    validation = {
        "version": 1,
        "status": status,
        "issue": issue_number,
        "checked_files": staged_files,
        "errors": errors,
        "caveats": caveats,
    }
    (work / "validation.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if errors:
        print(f"validate-run: rejected with {len(errors)} error(s)")
        for error in errors:
            print(f"  - {error}")
        return 1

    manifest = {
        "version": 1,
        "validation": "approved",
        "issue": request["issue"],
        "branch": f"knowledge/{issue_number}-{slug}",
        "slug": slug,
        "files": manifest_files,
        "caveats": caveats,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (work / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"validate-run: approved {len(manifest_files)} file(s) for issue #{issue_number}")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
