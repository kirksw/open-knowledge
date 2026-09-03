#!/usr/bin/env python3
"""Unit and integration tests for the knowledge-agent pipeline scripts.

Run: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mini_yaml = load("mini_yaml")
coordinator = load("coordinator")


class MiniYAMLTests(unittest.TestCase):
    def test_scalars(self):
        data = mini_yaml.parse('a: hello\nb: "quoted"\nc: 12\nd: true\ne:\n')
        self.assertEqual(data["a"], "hello")
        self.assertEqual(data["b"], "quoted")
        self.assertEqual(data["c"], 12)
        self.assertIs(data["d"], True)
        self.assertIsNone(data["e"])

    def test_nested_mapping(self):
        data = mini_yaml.parse("generated:\n  by: knowledge-agent\n  at: 2026-09-03T10:00:00Z\n")
        self.assertEqual(data["generated"], {"by": "knowledge-agent", "at": "2026-09-03T10:00:00Z"})

    def test_sequence_of_mappings(self):
        text = (
            "sources:\n"
            "  - id: primary\n"
            "    resource: https://example.com\n"
            "    title: Example\n"
            "  - id: s2\n"
            "    resource: https://example.org\n"
            "    title: Other\n"
        )
        data = mini_yaml.parse(text)
        self.assertEqual(data["sources"][0]["id"], "primary")
        self.assertEqual(data["sources"][1]["title"], "Other")

    def test_sequence_of_scalars(self):
        data = mini_yaml.parse("tags:\n  - papers\n  - ml\n")
        self.assertEqual(data["tags"], ["papers", "ml"])

    def test_rejects_tabs_and_odd_shapes(self):
        with self.assertRaises(mini_yaml.MiniYAMLError):
            mini_yaml.parse("a:\tb")
        with self.assertRaises(mini_yaml.MiniYAMLError):
            mini_yaml.parse("- item\n")

    def test_split_frontmatter(self):
        fm, body = mini_yaml.split_frontmatter("---\ntype: X\n---\n\n# Body\n")
        self.assertEqual(fm["type"], "X")
        self.assertIn("# Body", body)
        fm_none, _ = mini_yaml.split_frontmatter("# No frontmatter\n")
        self.assertIsNone(fm_none)
        with self.assertRaises(mini_yaml.MiniYAMLError):
            mini_yaml.split_frontmatter("---\ntype: X\n")


class CoordinatorParsingTests(unittest.TestCase):
    def test_parse_sections_issue_form(self):
        body = (
            "### Source URLs\n\n"
            "https://a.example/1\n"
            "- https://a.example/2\n\n"
            "### What is interesting / desired angle\n\n"
            "Why transformers replaced RNNs.\n\n"
            "### Requested deliverables\n\n"
            "- [x] Source record (sources/x.md)\n"
            "- [x] Wiki page (docs/x.md)\n"
            "- [ ] Output document (outputs/x.md)\n\n"
            "### Output document specification\n\n"
            "none\n\n"
            "### Publication constraints or caveats\n\n"
            "Quote sparingly.\n"
        )
        sections = coordinator.parse_sections(body)
        self.assertIn("https://a.example/1", sections["urls"])
        self.assertEqual(len(coordinator.extract_urls(sections["urls"])), 2)
        self.assertEqual(sections["angle"], "Why transformers replaced RNNs.")
        deliverables, missing = coordinator.parse_deliverables(sections["deliverables"])
        self.assertTrue(deliverables["source_record"])
        self.assertTrue(deliverables["wiki_page"])
        self.assertFalse(deliverables["output"])
        self.assertEqual(missing, [])
        self.assertEqual(sections["constraints"], "Quote sparingly.")

    def test_check_url_syntax(self):
        self.assertIsNone(coordinator.check_url_syntax("https://example.com/paper"))
        self.assertIsNone(coordinator.check_url_syntax("http://example.com:8080/paper"))
        self.assertIsNotNone(coordinator.check_url_syntax("ftp://example.com/x"))
        self.assertIsNotNone(coordinator.check_url_syntax("https://user:pass@example.com"))
        self.assertIsNotNone(coordinator.check_url_syntax("https://localhost/x"))

    def test_slugify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(coordinator.slugify("[Knowledge]: Attention Is All You Need", 7, root), "attention-is-all-you-need")
            (root / "sources" / "attention-is-all-you-need.md").parent.mkdir(parents=True)
            (root / "sources" / "attention-is-all-you-need.md").write_text("x")
            self.assertEqual(coordinator.slugify("Attention Is All You Need", 7, root), "attention-is-all-you-need-7")

    def test_trust_check(self):
        base = {
            "label": {"name": "knowledge:ready"},
            "issue": {
                "user": {"login": "kirksw"},
                "author_association": "OWNER",
                "state": "open",
                "labels": [],
            },
            "sender": {"login": "kirksw"},
        }
        self.assertIsNone(coordinator.trust_check(base, "kirksw"))
        other = json.loads(json.dumps(base))
        other["sender"]["login"] = "someone-else"
        self.assertIsNotNone(coordinator.trust_check(other, "kirksw"))
        working = json.loads(json.dumps(base))
        working["issue"]["labels"] = [{"name": "agent:working"}]
        self.assertIsNotNone(coordinator.trust_check(working, "kirksw"))


def make_event(number=7, body="", title="Attention Is All You Need"):
    return {
        "label": {"name": "knowledge:ready"},
        "sender": {"login": "kirksw"},
        "repository": {"full_name": "kirksw/open-knowledge", "default_branch": "main"},
        "issue": {
            "number": number,
            "title": title,
            "body": body,
            "state": "open",
            "html_url": f"https://github.com/kirksw/open-knowledge/issues/{number}",
            "user": {"login": "kirksw"},
            "author_association": "OWNER",
            "labels": [],
        },
    }


GOOD_BODY = (
    "### Source URLs\n\n"
    "https://arxiv.example/abs/1706.03762\n\n"
    "### What is interesting / desired angle\n\n"
    "Why self-attention replaced recurrence.\n\n"
    "### Requested deliverables\n\n"
    "- [x] Source record (sources/x.md)\n"
    "- [x] Wiki page (docs/x.md)\n"
    "- [ ] Output document (outputs/x.md)\n\n"
    "### Output document specification\n\n"
    "\n"
    "### Publication constraints or caveats\n\n"
    "Quote sparingly.\n"
)


class CoordinatorEndToEnd(unittest.TestCase):
    def run_coordinator(self, body, title="Attention Is All You Need"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        work = root / ".work"
        event = make_event(body=body, title=title)
        event_path = root / "event.json"
        event_path.write_text(json.dumps(event))
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "coordinator.py"),
             "--event-file", str(event_path), "--repo-root", str(REPO),
             "--work-dir", str(work)],
            capture_output=True, text=True,
        )
        return proc, work

    def test_accepted_request(self):
        proc, work = self.run_coordinator(GOOD_BODY)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        request = json.loads((work / "request.json").read_text())
        self.assertEqual(request["slug"], "attention-is-all-you-need")
        self.assertTrue(request["deliverables"]["source_record"])
        self.assertTrue(request["deliverables"]["wiki_page"])
        self.assertFalse(request["deliverables"]["output"]["requested"])
        self.assertEqual(request["urls"][0]["id"], "primary")
        self.assertFalse((work / "clarification.json").exists())

    def test_output_requested_needs_spec(self):
        body = GOOD_BODY.replace("- [ ] Output document", "- [x] Output document")
        proc, work = self.run_coordinator(body)
        self.assertEqual(proc.returncode, 0)
        clarification = json.loads((work / "clarification.json").read_text())
        self.assertIn("output document", clarification["question"].lower())
        self.assertFalse((work / "request.json").exists())

    def test_missing_urls_clarifies(self):
        body = GOOD_BODY.replace("https://arxiv.example/abs/1706.03762", "")
        proc, work = self.run_coordinator(body)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue((work / "clarification.json").exists())

    def test_untrusted_event_ignored(self):
        event = make_event(body=GOOD_BODY)
        event["sender"]["login"] = "attacker"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event_path = root / "event.json"
            event_path.write_text(json.dumps(event))
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "coordinator.py"),
                 "--event-file", str(event_path), "--repo-root", str(REPO),
                 "--work-dir", str(root / ".work")],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 3)


GOOD_RECORD = """---
type: Source Record
title: "Attention Is All You Need"
description: "Record of the transformer paper."
resource: "https://arxiv.example/abs/1706.03762"
issue: 7
tags: []
status: draft
generated:
  by: knowledge-agent
  at: 2026-09-03T10:00:00Z
sources:
  - id: primary
    resource: "https://arxiv.example/abs/1706.03762"
    title: "Attention Is All You Need"
---

# Provenance

- Requested in https://github.com/kirksw/open-knowledge/issues/7 by the repository owner.

# Source overview

The paper introduces the Transformer.

# Notes

Self-attention replaces recurrence [^primary].

# Caveats

None recorded.

[^primary]: Attention Is All You Need - https://arxiv.example/abs/1706.03762
"""

GOOD_SUMMARY = """---
type: Knowledge Summary
title: "Attention Is All You Need"
description: "The transformer architecture explained."
tags: []
status: draft
generated:
  by: knowledge-agent
  at: 2026-09-03T10:00:00Z
sources:
  - id: record
    resource: "/sources/attention-is-all-you-need.md"
    title: "Attention Is All You Need"
  - id: primary
    resource: "https://arxiv.example/abs/1706.03762"
    title: "Attention Is All You Need"
---

# Answer

Self-attention works better than recurrence for sequence transduction [^primary].

# Key concepts

- [Self-attention replaces recurrence](/concepts/self-attention-replaces-recurrence.md)

# Evidence

An architecture based on attention [^primary].

# Caveats

Interpretation is the author's.

# References

- [Source record](/sources/attention-is-all-you-need.md)

[^primary]: Attention Is All You Need - https://arxiv.example/abs/1706.03762
"""

GOOD_CONCEPT = """---
type: Concept
title: "Self-attention replaces recurrence"
statement: "Sequence models built on self-attention outperform recurrent architectures."
tags: []
status: draft
generated:
  by: knowledge-agent
  at: 2026-09-03T10:00:00Z
sources:
  - id: record
    resource: "/sources/attention-is-all-you-need.md"
    title: "Attention Is All You Need"
  - id: primary
    resource: "https://arxiv.example/abs/1706.03762"
    title: "Attention Is All You Need"
related:
---

# Statement

Self-attention replaces recurrence.

# Evidence

- The paper reports better results than recurrent baselines [^primary].

# Caveats

Single-source evidence so far.

# Related

- [Held-out evaluation](/concepts/held-out-evaluation.md)

[^primary]: Attention Is All You Need - https://arxiv.example/abs/1706.03762
"""


def make_fixtures(tmp: Path, record=GOOD_RECORD, summary=GOOD_SUMMARY, output_doc=None,
                   concept=GOOD_CONCEPT):
    work = tmp / ".work"
    request = {
        "version": 1,
        "issue": {"number": 7, "title": "Attention Is All You Need",
                  "url": "https://github.com/kirksw/open-knowledge/issues/7", "author": "kirksw"},
        "repo": {"full_name": "kirksw/open-knowledge", "default_branch": "main"},
        "urls": [{"id": "primary", "url": "https://arxiv.example/abs/1706.03762"}],
        "angle": "why",
        "deliverables": {"source_record": True, "wiki_page": True,
                         "output": {"requested": output_doc is not None, "spec": "table",
                                    "filename": "attention-table.txt" if output_doc is not None else None}},
        "constraints": "",
        "slug": "attention-is-all-you-need",
    }
    (work / "request.json").parent.mkdir(parents=True, exist_ok=True)
    (work / "request.json").write_text(json.dumps(request))
    (work / "draft.json").write_text(json.dumps(
        {"version": 1, "issue": 7, "slug": "attention-is-all-you-need",
         "mode": "draft", "caveats": ["review licensing"], "clarification": None}))
    staged = work / "staged"
    (staged / "sources").mkdir(parents=True)
    (staged / "docs").mkdir(parents=True)
    (staged / "sources" / "attention-is-all-you-need.md").write_text(record)
    (staged / "docs" / "attention-is-all-you-need.md").write_text(summary)
    if concept is not None:
        (staged / "concepts").mkdir(parents=True)
        (staged / "concepts" / "self-attention-replaces-recurrence.md").write_text(concept)
    if output_doc is not None:
        (staged / "outputs").mkdir(parents=True)
        (staged / "outputs" / "attention-table.txt").write_text(output_doc)
    # Isolated repo root so "exists on default branch" checks are deterministic.
    repo = tmp / "repo"
    for part in ("sources", "docs", "templates"):
        (repo / part).mkdir(parents=True)
    return work, repo


class ValidatorTests(unittest.TestCase):
    def run_validate(self, work, repo):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate-run.py"),
             "--work-dir", str(work), "--repo-root", str(repo)],
            capture_output=True, text=True,
        )

    def test_approves_good_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            manifest = json.loads((work / "manifest.json").read_text())
            self.assertEqual(manifest["validation"], "approved")
            self.assertEqual(len(manifest["files"]), 3)  # record, summary, concept
            self.assertEqual(manifest["branch"], "knowledge/7-attention-is-all-you-need")
            self.assertEqual(manifest["caveats"], ["review licensing"])

    def test_approves_with_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp), output_doc="table content\n")
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_rejects_path_outside_allowed_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            secret = work / "staged" / ".github" / "workflows" / "evil.yml"
            secret.parent.mkdir(parents=True)
            secret.write_text("name: evil\n")
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("outside allowed directories", proc.stdout)

    def test_rejects_citation_missing_from_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp),
                                       summary=GOOD_SUMMARY.replace("[^primary]", "[^ghost]", 1))
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("ghost", proc.stdout)

    def test_rejects_secret_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(
                Path(tmp),
                summary=GOOD_SUMMARY.replace(
                    "# Caveats",
                    "# Caveats\n\ntoken ghp_abcdefghijklmnopqrst\n"),
            )
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("GitHub token", proc.stdout)

    def test_rejects_wrong_type_and_missing_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken = GOOD_SUMMARY.replace("type: Knowledge Summary", "type: Topic")
            work, repo = make_fixtures(Path(tmp), summary=broken)
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("type must be 'Knowledge Summary'", proc.stdout)

    def test_rejects_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            (repo / "sources" / "attention-is-all-you-need.md").write_text("exists")
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("already exists", proc.stdout)

    def test_rejects_missing_deliverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            (work / "staged" / "docs" / "attention-is-all-you-need.md").unlink()
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("required deliverable is missing", proc.stdout)

    def test_rejects_non_draft_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken = GOOD_SUMMARY.replace("status: draft", "status: stable")
            work, repo = make_fixtures(Path(tmp), summary=broken)
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("status: draft", proc.stdout)

    def test_rejects_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            (work / "staged" / "sources" / "attention-is-all-you-need.md").write_bytes(
                b"---\ntype: Source Record\n---\n\x00\x01binary"
            )
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("binary content", proc.stdout)

    def test_requires_at_least_one_concept(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp), concept=None)
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("between 1 and 8 concept pages", proc.stdout)

    def test_concept_update_accumulates_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            # Existing concept on the default branch with one recorded source.
            existing = repo / "concepts"
            existing.mkdir()
            (existing / "self-attention-replaces-recurrence.md").write_text(GOOD_CONCEPT)
            # Staged update adds a second source: allowed.
            added = GOOD_CONCEPT.replace(
                '  - id: primary\n    resource: "https://arxiv.example/abs/1706.03762"\n    title: "Attention Is All You Need"\nrelated:',
                '  - id: primary\n    resource: "https://arxiv.example/abs/1706.03762"\n    title: "Attention Is All You Need"\n  - id: s2\n    resource: "/sources/second-paper.md"\n    title: "Second Paper"\nrelated:',
            )
            (work / "staged" / "concepts" / "self-attention-replaces-recurrence.md").write_text(added)
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_concept_update_rejects_dropped_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            existing = repo / "concepts"
            existing.mkdir()
            fuller = GOOD_CONCEPT.replace(
                'related:',
                '  - id: s2\n    resource: "/sources/second-paper.md"\n    title: "Second Paper"\nrelated:',
            )
            (existing / "self-attention-replaces-recurrence.md").write_text(fuller)
            proc = self.run_validate(work, repo)  # staged fixture drops s2
            self.assertEqual(proc.returncode, 1)
            self.assertIn("must not drop previously recorded sources", proc.stdout)

    def test_rejects_non_concept_overwrite_in_concepts_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp))
            existing = repo / "concepts"
            existing.mkdir()
            (existing / "self-attention-replaces-recurrence.md").write_text(
                "---\ntype: Reference\ntitle: x\ndescription: x\n---\n")
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("refusing to overwrite a non-Concept file", proc.stdout)

    def test_labeled_content_hash_allowed_as_provenance(self):
        digest = "0bbc8ed36a571a31bea861747c91722946b67c5fa352eb4bd39bb9aa94c73f93"
        record = GOOD_RECORD.replace(
            "# Notes",
            f"# Notes\n\nFetched page sha256 `{digest}` recorded for provenance.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp), record=record)
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_unlabeled_hex_blob_still_rejected(self):
        blob = "0bbc8ed36a571a31bea861747c91722946b67c5fa352eb4bd39bb9aa94c73f93"
        record = GOOD_RECORD.replace("# Notes", f"# Notes\n\nMystery value: {blob}")
        with tempfile.TemporaryDirectory() as tmp:
            work, repo = make_fixtures(Path(tmp), record=record)
            proc = self.run_validate(work, repo)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("hexadecimal secret-sized string", proc.stdout)


class FetchGuardTests(unittest.TestCase):
    def setUp(self):
        self.fetch = load("fetch-sources")

    def test_private_addresses_blocked(self):
        import socket

        original = self.fetch._original_getaddrinfo

        def fake(host, port, *args, **kwargs):
            addr = host if ":" not in host else "::1"
            family = socket.AF_INET6 if ":" in host else socket.AF_INET
            return [(family, socket.SOCK_STREAM, 6, "", (addr, 0))]

        self.fetch._original_getaddrinfo = fake
        try:
            for host in ("10.0.0.5", "127.0.0.1", "169.254.169.254", "192.168.1.1",
                         "172.16.0.1", "100.64.0.1", "::1", "0.0.0.0"):
                with self.assertRaises(self.fetch.BlockedDestination, msg=host):
                    self.fetch._validate_host(host)
            answers = self.fetch._validate_host("93.184.216.34")
            self.assertTrue(answers)
        finally:
            self.fetch._original_getaddrinfo = original

    def test_pinned_resolution_blocks_rebinding(self):
        import socket

        original = self.fetch._original_getaddrinfo
        resolved = []

        def fake(host, port, *args, **kwargs):
            # Second resolution (at connect time) would return a private address.
            resolved.append(host)
            addr = "10.0.0.99" if len(resolved) > 1 else "93.184.216.34"
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (addr, port or 0))]

        self.fetch._original_getaddrinfo = fake
        try:
            answers = self.fetch._validate_host("example.com")
            self.fetch._pinned["example.com"] = answers
            result = self.fetch._guarded_getaddrinfo("example.com", 443)
            self.assertEqual(result[0][4], ("93.184.216.34", 443))
        finally:
            self.fetch._original_getaddrinfo = original
            self.fetch._pinned.clear()

    def test_html_text_extraction(self):
        parser = self.fetch._HTMLText()
        parser.feed("<html><head><title>T</title><script>bad()</script></head>"
                    "<body><h1>H</h1><p>Hello <b>world</b></p><p>Second</p></body></html>")
        text = parser.text()
        self.assertEqual(parser.title, "T")
        self.assertIn("Hello world", text)
        self.assertIn("Second", text)
        self.assertNotIn("bad()", text)


class PublishGuardTests(unittest.TestCase):
    def setUp(self):
        self.publish = load("publish")

    def test_templates_format(self):
        body = self.publish.PR_TEMPLATE.format(
            issue_number=7, issue_url="https://example/i/7",
            source_urls="- https://a", files="- `sources/x.md`",
            caveats="- none", run_id="123", run_url="https://example/runs/123")
        self.assertIn("Closes #7", body)
        msg = self.publish.COMMIT_TEMPLATE.format(
            issue_number=7, title="T", files="sources/x.md", run_id="123")
        self.assertIn("issue #7", msg)

    def test_rejects_workflow_paths(self):
        # The guard logic is inline in publish(); assert the constants used.
        for forbidden in (".github/workflows/x.yml", ".github/x"):
            self.assertTrue(any(forbidden.startswith(p) for p in self.publish.FORBIDDEN_PREFIXES))


if __name__ == "__main__":
    unittest.main()
