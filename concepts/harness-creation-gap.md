---
type: Concept
title: "Harness creation gap"
statement: "Frontier LLMs can build complete runnable agent harnesses from a weak seed, approaching but not matching mature human-engineered references, with the gap concentrated in search and code domains."
description: "Scope: single-shot harness construction from a weak-but-runnable seed with 1-3 development cases."
tags: [agent-harness, code-generation, benchmark]
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
  - /concepts/harness-determines-performance.md
  - /concepts/harness-executor-overfitting.md
---

# Statement

Given only a weak-but-runnable seed and 1–3 development cases, frontier creator LLMs can produce a complete harness that scores substantially above zero on held-out downstream tasks — but on average they remain behind mature human-engineered references. The gap is near zero (or reversed) for writing and ML experimentation, and largest for search/research and code harnesses.

# Evidence

- The unmodified weak seed scores 0.00 on all five downstream benchmarks, so any nonzero Creation score reflects creator-added execution logic. [^primary]
- Best creator (Opus 4.8) Self-Eval average: 67.8 versus 86.2 for the human-engineered reference. [^primary]
- Matches or beats the reference on writing (EQ-Bench3: 84.6 vs 83.7) and ML experimentation (MLE-bench medal: 32.9 vs 24.0). [^primary]
- Lags badly on search (BrowseComp best Self-Eval 52.4 vs 92.2 reference) and substantially on code (SWE-Pro 69.3 vs 80.0; Terminal-Bench 2.1 64.8 vs 88.8). [^primary]
- Coverage of the measurement: six creator LLMs, four domains, five downstream benchmarks, 2,207 unique downstream instances, evaluation tasks hidden from development. [^primary]

# Caveats

- Human references are not paired controls: they pair external system-level results, three of which come from OpenAI's GPT-5.6 release report and were not rerun by the authors; distance-to-reference is not an absolute ceiling. [^primary]
- Average-of-3 reporting masks variance — independent creations from the same model can differ sharply. [^primary]
- Single preprint (v1); model names as given in the paper, not externally verified. [^primary]

# Related

- [The harness determines agent performance](/concepts/harness-determines-performance.md)
- [Harness–executor overfitting](/concepts/harness-executor-overfitting.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
