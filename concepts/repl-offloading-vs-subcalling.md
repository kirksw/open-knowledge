---
type: Concept
title: "REPL offloading versus sub-calling"
statement: "The two mechanisms of a recursive scaffold contribute differently: REPL offloading alone (no sub-calls) suffices when answers are localized in the prompt, while programmatic sub-calling mainly helps on information-dense inputs requiring access throughout the prompt."
description: "Scope: RLM recursion-depth ablations across benchmark task types."
tags: [ablation, inference-scaffold, long-context, task-complexity]
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
  - /concepts/symbolic-recursion-subcalls.md
  - /concepts/scaffold-beats-window-bound-baselines.md
---

# Statement

Externalizing the prompt into a REPL (depth 0) and invoking LM sub-calls (depth ≥1) are separable capabilities with different payoff profiles: in the RLM paper's ablations, depth-0 offloading beat all sub-calling variants on code-repository QA, while sub-calling drove the largest gains on information-dense tasks where the whole prompt must be accessed, and its benefit elsewhere was mixed.

# Evidence

- On LongBench-v2 CodeQA with Qwen3-Coder, RLM depth 0 scored 66.0, beating all sub-calling variants — REPL offloading alone sufficed. [^primary]
- On information-dense inputs, sub-calling helped: OOLONG improved 28.4% (GPT-5) and 33.3% (Qwen3-Coder) at depth 1, and OOLONG-Pairs jumped from ≤0.1 F1 (both base models) to 58.0 (GPT-5 depth 1) and 23.1 (Qwen3-Coder depth 1), with GPT-5 depth 3 reaching 76.0. [^primary]
- Beyond long-context tasks the picture is mixed: on LongCoT-mini, RLM(GPT-5.2, depth=1) scored 50.6 versus 38.7 base (65.6 with explicit decomposition hints), but without hints it scored below base on MATH (5.6 vs 26.0) and CS (11.0 vs 40.4). [^primary]

# Caveats

- Single-preprint evidence with small per-benchmark sets; the depth-0 result is demonstrated for CodeQA/Qwen3-Coder specifically and may not transfer to other task types. [^primary]
- The LongCoT-mini hint dependency suggests sub-calling can hurt when the model cannot decompose the task itself; interpretation: recursion is a task-shape-dependent tool, not a universal upgrade. [^primary]

# Related

- [Symbolic recursion via programmatic sub-calls](/concepts/symbolic-recursion-subcalls.md)
- [Scaffolds beat window-bound baselines on long prompts](/concepts/scaffold-beats-window-bound-baselines.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
