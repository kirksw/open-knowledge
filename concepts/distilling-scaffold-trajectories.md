---
type: Concept
title: "Distilling scaffold trajectories into small models"
statement: "Distilling a strong model's scaffold trajectories into a small model by rejection fine-tuning yields a cheap, fast recursive operator that far outperforms the same small model used directly."
description: "Scope: the RLM paper's RLM-Qwen3-8B training experiment."
tags: [distillation, fine-tuning, inference-scaffold, small-models]
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
  - /concepts/prompt-as-external-environment.md
  - /concepts/scaffold-rl-length-generalization.md
---

# Statement

Scaffold behavior is a trainable skill that can be transferred by supervised distillation: rejection fine-tuning a small model on roughly a thousand filtered turns from a larger model's recursive trajectories produced an operator that beats the same small model in the same scaffold by a large median margin, at a fraction of the compute, trained on an unrelated domain yet transferring to the target tasks.

# Evidence

- RLM-Qwen3-8B was produced by rejection fine-tuning Qwen3-8B on ~1,000 filtered turns distilled from 2,250 RLM(Qwen3-Coder) trajectories collected on LongBenchPro (unrelated domain); 2,250 candidate trajectories were filtered to 1,072, then root turns were split into ~1,000 SFT samples, with programmatic fixes for template mistakes (16% of turns misused `FINAL`, 13% misused `FINAL_VAR`). [^primary]
- Training was cheap: 300 steps, batch 64, 48 H100-hours. [^primary]
- Results: the distilled model beats base Qwen3-8B as an RLM by a median of 28.3% across four tasks, is over 3× faster with lower cost, and "even approaches the quality of vanilla GPT-5 on three long-context tasks". [^primary]

# Caveats

- Single experiment from one preprint on four tasks; the filtering and template-fixing pipeline suggests raw trajectories are noisy and distillation required cleanup. [^primary]
- The broader claim that trajectories are "a form of reasoning trainable by bootstrapping" and could yield native RLMs as "another axis of scale" is an author hypothesis, not a demonstrated result. [^primary]

# Related

- [Prompt as external environment](/concepts/prompt-as-external-environment.md)
- [Scaffold RL length generalization](/concepts/scaffold-rl-length-generalization.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
