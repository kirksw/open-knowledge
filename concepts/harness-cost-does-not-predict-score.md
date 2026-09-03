---
type: Concept
title: "Harness cost does not predict score"
statement: "Execution cost and edit size do not predict harness quality: token use varies enormously across comparable harnesses, and larger or more numerous changes do not reliably score higher."
description: "Scope: efficiency of created agent harnesses on downstream benchmarks."
tags: [agent-harness, efficiency, code-generation]
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
  - /concepts/harness-creation-gap.md
  - /concepts/agents-neglect-state-checkpointing.md
---

# Statement

Spending more tokens or writing more code does not buy a better harness. Harness quality and cost are close to independent across creators, so efficiency must be measured alongside capability rather than assumed to follow from effort.

# Evidence

- MLE-bench execution-token use varies about nineteen-fold across created harnesses, and higher cost does not reliably produce a higher score: GPT-5.5 reached medal 19.1 with 29.3M tokens while DeepSeek V4 reached 19.6 with 208.4M. [^primary]
- Edit size does not predict performance: across 18 Code artifacts (17,111 net added lines), Gemini added the fewest lines (1,006 net) yet obtained the best Terminal-Bench score (68.8). [^primary]
- HarnessDev accordingly scores harnesses on both capability (held-out task success) and efficiency (executor tokens) as first-class dimensions. [^primary]

# Caveats

- Comparisons are cross-model (different creators), so cost differences partly reflect different executors and strategies rather than a controlled variable. [^primary]
- Token accounting follows the paper's measurement setup; absolute numbers may not be comparable across studies. [^primary]

# Related

- [Harness creation gap](/concepts/harness-creation-gap.md)
- [Agents neglect state checkpointing](/concepts/agents-neglect-state-checkpointing.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
