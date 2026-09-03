---
type: Concept
title: "Agents neglect failure diagnosis"
statement: "When LLMs improve their own code or harness, failure diagnosis is the weakest step: they rarely inspect failing trajectories, and what predicts improvement is the diagnose-edit-reverify loop, not the volume of testing."
description: "Scope: self-improvement loops driven by execution feedback."
tags: [self-improvement, debugging, agents]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-03T15:10:20Z"
sources:
  - id: record
    resource: "/sources/harnessdev-can-llms-create-and-evolve-their-own.md"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? (arXiv:2609.01437v1)"
  - id: primary
    resource: "https://arxiv.org/html/2609.01437v1"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
related:
  - /concepts/visible-feedback-overfitting.md
  - /concepts/harness-defects-dominate-failures.md
---

# Statement

In feedback-driven self-improvement, the bottleneck is not generating changes or running tests but reading and understanding failures. Self-test volume is a weak predictor of downstream improvement; targeted revision cycles that inspect a concrete failure, make a focused edit, and re-verify end to end are what correlate with gains.

# Evidence

- A dedicated trajectory-analysis interface was called only twice across evolution lineages, and explicitly inspected cases covered just 0.5%–40.2% of the 189 feedback tasks depending on lineage. [^primary]
- Self-test volume correlates weakly with downstream score (Spearman 0.13–0.26, not significant), while revision calls correlate at 0.57 (p≤.0005). [^primary]
- Positive example: Opus found that 99 of 100 runs reported success while only 48 passed, traced the gap to premature completion, and added a completion check — feedback helps most when it exposes a concrete failure mode and the fix is verified end to end. [^primary]

# Caveats

- The correlation figures come from one benchmark study with nine lineages; treat as indicative rather than precise. [^primary]
- Interpretation: "diagnose-edit-reverify" is this page's condensation of the paper's finding that revision calls (not test volume) predict gains; the phrase itself is not the paper's. [^primary]

# Related

- [Visible-feedback overfitting](/concepts/visible-feedback-overfitting.md)
- [Harness defects dominate failures](/concepts/harness-defects-dominate-failures.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
