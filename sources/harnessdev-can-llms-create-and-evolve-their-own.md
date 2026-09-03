---
type: Source Record
title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
description: "Provenance record for the HarnessDev benchmark paper (arXiv:2609.01437), requested in issue #1."
resource: "https://arxiv.org/abs/2609.01437"
issue: 1
tags: ["llm-agents", "agent-harness", "benchmarks", "self-improvement"]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-03T14:29:52Z"
sources:
  - id: primary
    resource: "https://arxiv.org/abs/2609.01437"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
---

# Provenance

- Requested in https://github.com/kirksw/open-knowledge/issues/1 by the repository owner.
- Captured URL: https://arxiv.org/html/2609.01437v1 (HTML v1, fetched 2026-09-03T14:26:43Z, HTTP 200, text/html, 587,593 bytes, sha256 `0bbc8ed36a571a31bea861747c91722946b67c5fa352eb4bd39bb9aa94c73f93`).

# Source overview

- **What it is:** an academic benchmark paper defining HarnessDev, which "shifts the unit of evaluation from task outputs to runnable infrastructure" [^primary]. It was published on arXiv as a preprint (arXiv:2609.01437v1 [cs.SE]) dated September 1, 2026.
- **Who produced it:** authors affiliated with ByteDance Seed, Singapore University of Technology and Design, Georgia Institute of Technology, M-A-P, and TokenWave.AI; core contributors named on the paper include Yuhao Wu, Jingyuan Zhang, and Jiajun Shi [^primary]. A project page exists at https://self-developing-agents.github.io/ [^primary]. Author and affiliation metadata are agent-captured from the paper and not independently verified.
- **Access:** open access via arXiv; this record is based on the HTML v1 extraction, with license CC BY-NC-ND 4.0 [^primary].

# Notes

- The benchmark covers a Creation stage (build a complete harness from a weak-but-runnable seed, a spec, and 1–3 development cases) and an Evolution stage (iteratively revise the creator's own harness from downstream execution feedback) [^primary].
- Reported Creation coverage: six creator LLMs, four domains, and five downstream benchmarks totaling 2,207 unique downstream instances, with hidden evaluation tasks withheld from development [^primary].
- The design separates creator model, development environment (Claude Code 2.1.177; Codex 0.144.3 for GPT-5.5), a frozen-harness executor model, and a fixed evaluator, so score changes reflect harness changes [^primary].
- Reported Evolution findings: all five self-runtime creators improve on visible feedback, but held-out gains shrink to +1.43 to +4.44 points (mean +3.11), and under a fixed Gemini runtime only one lineage improves while others regress (GPT-5.5 −10.32) [^primary].
- Constraint compliance was audited for every reported run; the paper reports a null result, with no harness obtaining score through a prohibited route [^primary].
- Short attributable quotation from the conclusion: "If model weights are one place intelligence accumulates, the harness is another: explicit, inspectable, testable, reusable" [^primary].

# Caveats

- **License:** CC BY-NC-ND 4.0 (non-commercial, no derivatives). Quotations here are kept short and attributed; summaries are original writing. This matches the repository publication policy (canonical links, short quotations, original summaries).
- **Single preprint, not visibly peer-reviewed:** all findings derive from one arXiv preprint; model and benchmark names (e.g., "Opus 4.8", "GPT-5.5", "GPT-5.6 Sol") are as reported by the source and are not independently verified.
- **Uneven human baselines:** human-reference numbers are external system-level results pairing different harness–model combinations, "not paired controls under one executor"; three starred values come from OpenAI's GPT-5.6 release report [^primary].
- **Statistical fragility, acknowledged in-paper:** one trajectory per creator–runtime cell, held-out evaluation limited to SWE-bench Pro, and repeated-run noise (±4.75 pair-score points) that swamps most observed evolution gains [^primary].
- **Fetch quality:** the corpus is an arXiv HTML extraction with some mangled LaTeX/table markup; values were cross-checked against surrounding prose by the research stage.

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/abs/2609.01437
