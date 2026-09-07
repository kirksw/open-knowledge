---
type: Concept
title: "Scaffold RL length generalization"
statement: "Reinforcement-learning training of scaffold behavior at a modest context length generalized to far longer contexts, without retraining at the target length."
description: "Scope: the RLM paper's RLVR experiment on MRCRv2."
tags: [reinforcement-learning, length-generalization, inference-scaffold, long-context]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-07T13:40:20Z"
sources:
  - id: record
    resource: "/sources/recursive-language-models.md"
    title: "Recursive Language Models (arXiv:2512.24601)"
  - id: primary
    resource: "https://arxiv.org/abs/2512.24601"
    title: "Recursive Language Models"
related:
  - /concepts/distilling-scaffold-trajectories.md
  - /concepts/prompt-as-external-environment.md
---

# Statement

Training the scaffold policy with RL on short-ish inputs transferred to much longer ones: RLVR training of RLM(Qwen3-4B-Instruct-0527) on MRCRv2's 64k-token, 2-needle split generalized to the 1M-token, 8-needle split. This suggests scaffold behavior learned at reachable lengths can extend beyond what was trained, because the policy operates over an externalized prompt rather than a fixed window.

# Evidence

- RLVR training of RLM(Qwen3-4B-Instruct-0527) on MRCRv2's 64k-token/2-needle split generalized to the 1M-token/8-needle split (Figure 3b). [^primary]
- A 1M-context Gemini 3.1 Pro is shown in that figure only as a reference point; the paper runs no head-to-head against native long-context models. [^primary]

# Caveats

- Figure-derived claim supported by in-text description only; single task family (MRCRv2), single small model, author-reported from one preprint. [^primary]
- Generalization measured up to 1M tokens, far below the 6-11M-token inputs used elsewhere in the paper; no third-party replication exists. [^primary]

# Related

- [Distilling scaffold trajectories into small models](/concepts/distilling-scaffold-trajectories.md)
- [Prompt as external environment](/concepts/prompt-as-external-environment.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
