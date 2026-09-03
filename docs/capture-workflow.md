---
type: Reference
title: "Capture Workflow"
description: "Manual path for adding knowledge entries without the automated pipeline."
---

# Capture Workflow

The automated path is described in [Agent pipeline](agent-pipeline.md); this page is the manual equivalent.

## Capture

Create a `Source Record` in `sources/` from `templates/source-record.md`.
Use the canonical URL for the primary source and write only short personal notes or clearly marked quotations.
Do not copy full copyrighted papers, paywalled articles, or confidential material into this public repository.

## Synthesize

Create a `Knowledge Summary` in `docs/` from `templates/wiki-page.md` when the capture is useful beyond its original encounter.
The summary is question-first: it opens with the answer to the originating question, links its key concepts, then carries evidence.
It must link to its source record, name its primary sources in frontmatter, distinguish source claims from interpretation, and use a `draft` status until reviewed.

Extract or update `Concept` pages in `concepts/` from `templates/concept.md` for claims that other entries can reuse.
A concept update adds sources and evidence; it must not drop a source already recorded on the page.
Requested artifacts belong in `outputs/` as Markdown or plain text.

## Curate

Add or update navigation indexes when a change materially improves them.
A human review can add a `verified` event and promote a summary to `stable`.
When a better summary replaces an older one, retain the older file with `status: deprecated` and link to the successor.
Record material changes in `log.md`.
