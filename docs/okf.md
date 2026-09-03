---
type: Reference
title: "OKF v0.2 Conventions"
description: "Bundle rules and local concept types for this repository."
---

# OKF v0.2 Conventions

This repository follows the [Open Knowledge Format v0.2 specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md).

## Bundle rules

- The repository root is the bundle root.
- Every non-reserved `.md` file in the bundle starts with parseable YAML frontmatter and a non-empty `type`.
- `index.md` and `log.md` are reserved filenames at every level and contain no frontmatter.
- Bundle-relative Markdown links beginning with `/` are preferred for durable cross-links (for example `/sources/<slug>.md`).
- Unknown frontmatter fields are allowed and must be preserved by agents.

## Local concept types

- `Source Record`: a provenance concept for one knowledge request; records canonical URLs, access dates, the originating issue, and caveats.
- `Knowledge Summary`: a question-first synthesis derived from one or more source records; it leads with the answer to the originating issue's angle.
- `Concept`: an atomic, reusable claim under `concepts/`; one concept asserts one claim, accumulates evidence across sources over time, and links related concepts.
- `Output`: a requested standalone artifact derived from a summary; Markdown or plain text in `outputs/`.
- `Reference`: repository documentation or a supporting local concept.

## Knowledge model

The bundle decomposes knowledge along concepts, not sources:

- `sources/` is append-only provenance: one record per captured source.
- `docs/` is append-only summaries: one question-first page per knowledge request, linking its concepts.
- `concepts/` is the growing wiki layer: concept pages are created once and updated as later sources add, support, or contest the claim.
- A concept update may add sources and evidence but must not drop a source already recorded on it; superseded claims are marked, not silently removed.

This makes a second paper on the same idea strengthen existing concept pages instead of spawning a parallel digest.

## Provenance, trust, and lifecycle

Use the optional v0.2 fields deliberately:

- `sources` records source URLs or bundle paths. Give cited sources stable `id` values.
- `generated` records who wrote the current meaningful content and when.
- `verified` records a human or deterministic confirmation; it is not a confidence score.
- `status` is `draft`, `stable`, or `deprecated`. Absent means `stable` in OKF, but this repository sets it explicitly for public concepts.
- `stale_after` is an optional absolute timestamp for time-sensitive material.

A missing `verified` field means unverified, not unusable.
