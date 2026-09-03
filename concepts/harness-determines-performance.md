---
type: Concept
title: "The harness determines agent performance"
statement: "An LLM's measured task performance depends strongly on the agent harness it runs in, independently of model weights."
description: "Scope: agent-style evaluations where the harness manages tools, context, and verification."
tags: [agent-harness, evaluation]
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
  - /concepts/harness-defects-dominate-failures.md
  - /concepts/harness-creation-gap.md
---

# Statement

The same model with identical weights can perform very differently depending on the harness that surrounds it. The harness — the infrastructure managing "the execution loop, tool use, context, failure recovery, and result verification" — is a first-order determinant of measured agent capability, not a neutral shell. [^primary]

# Evidence

- With identical weights, GPT-5 solved 35.2% of Terminal-Bench 2.1 inside Terminus 2 but 49.6% inside Codex CLI — a 14.4-point swing attributable to the harness alone. [^primary]
- Harness defects, not executor capability, accounted for 77.8% of failed MLE-bench Data tasks in the HarnessDev study. [^primary]
- HarnessDev was motivated by this observation: it shifts evaluation from task outputs to the runnable infrastructure itself, separating the creator model that builds the harness from the executor model that runs inside it. [^primary]

# Caveats

- The headline 35.2-vs-49.6 comparison is a single benchmark (Terminal-Bench 2.1) reported in one preprint. [^primary]
- The 77.8% defect attribution is measured on MLE-bench Data tasks only, using the paper's own attribution method. [^primary]

# Related

- [Harness defects dominate failures](/concepts/harness-defects-dominate-failures.md)
- [Harness creation gap](/concepts/harness-creation-gap.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
