---
type: Reference
title: "Open Knowledge"
description: "Landing page for this public OKF reference library."
---

# Open Knowledge

A public, personal reference library for papers, projects, and durable syntheses.

The repository is an [Open Knowledge Format (OKF) v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md) bundle: plain Markdown with YAML frontmatter that people can read and agents can cite, extend, and verify.
The bundle root is the repository root.

## Start here

- [Library index](index.md)
- [Agent pipeline](docs/agent-pipeline.md) - request an entry with a GitHub issue.
- [Capture workflow](docs/capture-workflow.md) - add an entry manually.
- [Publication policy](docs/publication-policy.md)
- [OKF conventions](docs/okf.md)
- [Agent guidance](AGENTS.md)

## Add something

- Automated: open a *Knowledge entry* issue, apply `knowledge:ready`, and review the pull request the agent opens; see [Agent pipeline](docs/agent-pipeline.md).
- Manual: copy `templates/source-record.md` to `sources/` and `templates/wiki-page.md` to `docs/`, then open a pull request.

Run `./scripts/okf-scan.py .` to verify the bundle and `./scripts/okf-list.py .` to list its concepts.
