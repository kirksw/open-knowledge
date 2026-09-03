---
type: Concept
title: "Harness defects dominate failures"
statement: "A large share of agent task failures can be attributed to defects in the harness itself rather than to limits of the executor model."
description: "Scope: measured on ML-experimentation (MLE-bench Data) tasks; concrete failure modes include false success reporting."
tags: [agent-harness, failure-analysis, reliability]
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
  - /concepts/agents-neglect-state-checkpointing.md
---

# Statement

When an agent fails a task, the fault often lies in the harness — its execution control, verification, or state handling — rather than in the underlying model's capability. Improving the executor is therefore not always the highest-leverage fix.

# Evidence

- 77.8% of failed MLE-bench (Data) tasks were attributed to harness defects, indicating the bottleneck is not only executor capability. [^primary]
- Concrete failure mode: in one lineage, 99 of 100 runs reported success while only 48 actually passed — the harness accepted premature completion until a completion check was added. [^primary]
- Weakest harness components identified: state/memory handling (checkpointing almost never implemented) and verification (no evolution switch ever modified a standalone verifier). [^primary]

# Caveats

- The 77.8% figure is from MLE-bench Data tasks only, using the paper's internal attribution method; the share may differ in other domains. [^primary]
- Single preprint source; the finding has not yet been replicated by a second study. [^primary]

# Related

- [The harness determines agent performance](/concepts/harness-determines-performance.md)
- [Agents neglect state checkpointing](/concepts/agents-neglect-state-checkpointing.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
