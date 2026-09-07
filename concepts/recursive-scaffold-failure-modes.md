---
type: Concept
title: "Recursive scaffold failure modes"
statement: "Recursive LM scaffolds inherit and amplify the base model's coding weaknesses: syntax errors propagate through recursion depth, answer protocols are brittle, prompts do not transfer across models, and weak-coding or under-budgeted thinking models fail as operators."
description: "Scope: failure modes documented in the RLM paper's trajectory analyses and Appendix B negative results."
tags: [failure-modes, inference-scaffold, recursion, code-generation]
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
  - /concepts/recursive-scaffold-cost-heavy-tail.md
  - /concepts/symbolic-recursion-subcalls.md
---

# Statement

Wrapping an LM in a code-execution recursion multiplies its coding errors rather than masking them: syntax errors recur in generated code and propagate through recursion depth, distinguishing final answers from intermediate thoughts via a variable protocol is brittle, and operational fit varies per model — one system prompt does not transfer, weak-coding models struggle, and thinking models with insufficient output-token budgets exhaust their budget before answering.

# Evidence

- Qwen3-Coder over-invoked recursion: it "will try to perform a subcall on everything, leading to thousands of LM subcalls for basic tasks" without a batching warning in the prompt (roughly 500 sub-calls on average for correct OOLONG rollouts versus roughly ten for GPT-5); its frequent syntax errors propagate through recursion depth, which the authors give as the reason deeper Qwen3-Coder RLMs do worse. [^primary]
- Answer-protocol brittleness: one OOLONG-Pairs trajectory "never returned the answer it built up in its code environment through sub-LM calls"; during distillation, 16% of turns misused `FINAL` answers and 13% misused `FINAL_VAR`. [^primary]
- Appendix B negative results: one system prompt does not transfer across models (Qwen3-Coder over-called sub-LLMs without a warning line); models with weak coding ability (Qwen3-8B) struggle as RLMs; thinking models with insufficient output-token budgets fail (Qwen3-235B-A22B improved OOLONG 30%→38% but some trajectories exhausted output on thinking tokens). [^primary]

# Caveats

- Several findings are qualitative trajectory readings from a single preprint with small evaluation sets, not controlled ablations. [^primary]
- Failure modes were observed for specific 2026-era models (GPT-5, Qwen3 family); newer models may exhibit different behavior, and no third-party replication exists. [^primary]

# Related

- [Recursive scaffold cost heavy tail](/concepts/recursive-scaffold-cost-heavy-tail.md)
- [Symbolic recursion via programmatic sub-calls](/concepts/symbolic-recursion-subcalls.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
