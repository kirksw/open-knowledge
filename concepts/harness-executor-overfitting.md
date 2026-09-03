---
type: Concept
title: "Harness–executor overfitting"
statement: "LLM-built harnesses overfit to the executor model they were developed against; porting them to a different executor reshuffles rankings and can erase apparent gains."
description: "Scope: harnesses created or evolved with one executor model, then evaluated with another."
tags: [agent-harness, overfitting, portability, evaluation]
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
  - /concepts/visible-feedback-overfitting.md
---

# Statement

A harness tuned alongside one executor model can encode assumptions (step limits, tool-message formats, context conventions) that break under a different executor. Measured harness quality is therefore conditional on the executor, and rankings do not transfer.

# Evidence

- Fixing the executor to Gemini 3.1 Pro changes Creation rankings substantially: Opus's Self-Eval SWE-Pro score falls from 69.3 to 33.0 because its harness hard-codes a 120-step limit around the original executor, while several Qwen and DeepSeek harnesses improve (Qwen +17.6 on BrowseComp, +12.9 on MLE-bench). [^primary]
- Evolution gains transfer weakly: all five self-runtime creators improved held-out tasks, but under a fixed Gemini executor only Opus improved while the other three lineages regressed (GPT-5.5 worst at −10.32). [^primary]
- The paper explicitly separates creator and executor models as a design feature, and reports that evolution gains depend strongly on the model executing the harness. [^primary]

# Caveats

- Single-trajectory evidence: one lineage per creator–runtime cell (one cell unfinished), so per-model transfer estimates carry uncertainty. [^primary]

# Related

- [Harness creation gap](/concepts/harness-creation-gap.md)
- [Visible-feedback overfitting](/concepts/visible-feedback-overfitting.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
