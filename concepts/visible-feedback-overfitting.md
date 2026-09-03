---
type: Concept
title: "Visible-feedback overfitting"
statement: "Optimizing an agent against the same visible feedback signal used for version selection invites overfitting to noise; visible scores are useful for local search but unreliable for final selection."
description: "Scope: iterative self-improvement loops that pick versions by re-scoring on a visible evaluation set."
tags: [self-improvement, evaluation, overfitting]
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
  - /concepts/harness-executor-overfitting.md
  - /concepts/agents-neglect-failure-diagnosis.md
---

# Statement

When a self-improving agent repeatedly evaluates candidate versions on a visible benchmark and keeps the best-scoring one, run-to-run noise dominates small gains: identical code can score very differently, so the "winner" is often lucky rather than better. Selection should use held-out evaluation disjoint from the feedback signal.

# Evidence

- Identical commits varied by about ±4.75 pair-score points across repeated evaluation. [^primary]
- Only 2 of 64 official version switches showed clear positive evidence beyond the noise band. [^primary]
- Feedback and held-out scores moved in the same direction only 53.1% of the time (34/64), and only 2 of 9 declared versions were held-out optimal. [^primary]
- The paper's own framing: visible feedback is "useful for local search but unreliable for final selection: repeatedly optimizing a noisy score can favor a lucky run and amplify overfitting." [^primary]
- HarnessDev operationalizes the fix by withholding a 630-instance SWE-Pro held-out split that is never shown to the creator. [^primary]

# Caveats

- Evolution evidence is single-trajectory (one lineage per creator–runtime cell) with held-out evaluation on SWE-Pro only; the authors caution against population-level conclusions. [^primary]

# Related

- [Harness–executor overfitting](/concepts/harness-executor-overfitting.md)
- [Agents neglect failure diagnosis](/concepts/agents-neglect-failure-diagnosis.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
