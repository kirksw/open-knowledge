---
name: open-knowledge
description: Maintain this repository's public paper and project reference library. Use when capturing a source, writing a synthesis, updating navigation, or validating OKF frontmatter in this root-level bundle.
---

# Open Knowledge Operator

OKF Markdown/frontmatter is canonical.
Read `AGENTS.md`, `docs/okf.md`, and `docs/capture-workflow.md` before writing.

## Capture

Use `templates/source-record.md` to create a draft `Source Record` in `sources/`.
Record canonical URLs, minimal notes, and source metadata.
Do not reproduce copyrighted or private source material.

## Synthesize

Write public-ready `Knowledge Summary` concepts in `docs/` from `templates/wiki-page.md`.
Link the source record using bundle-relative paths such as `/sources/<slug>.md`.
Add `generated` for agent-written content, keep `status: draft`, and do not add `verified` unless an actual human or deterministic verification occurred.
Requested standalone artifacts go in `outputs/` as Markdown or plain text.

## Validate

Run:

```sh
./scripts/okf-scan.py .
./scripts/okf-list.py .
```

Reserved `index.md` and `log.md` files have no frontmatter.
Every other Markdown concept in the repository needs a non-empty `type`.
When operating inside the automated pipeline, follow the stage contract in `.agents/prompts/` exactly.
