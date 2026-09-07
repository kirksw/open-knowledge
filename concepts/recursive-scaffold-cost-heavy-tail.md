---
type: Concept
title: "Recursive scaffold cost heavy tail"
statement: "Recursive LM scaffolds have a heavy-tailed cost distribution: median runs are comparable to or cheaper than baselines, but outlier trajectories raise the average, and uncontrolled sub-calling can explode costs."
description: "Scope: cost and runtime characteristics reported for Recursive Language Models."
tags: [cost, inference-scaffold, latency, heavy-tail]
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
  - /concepts/recursive-scaffold-failure-modes.md
  - /concepts/symbolic-recursion-subcalls.md
---

# Statement

Medians flatter recursive scaffolds: the median RLM run was cheaper than the median base-model run and costs were comparable to or cheaper than most baselines, but the average is higher because outlier trajectories issue enormous numbers of sub-calls, and the authors explicitly warn the complexity "may lead to unintentional side-effects like exploding sub-call costs". Runtimes suffer from a sequential implementation with very long 95th-percentile latencies.

# Evidence

- The paper reports the median RLM run is cheaper than the median base-model run while the average is higher due to outlier trajectories, with RLM cost scaling with task complexity. [^primary]
- Concrete point: average RLM(GPT-5, depth=1) cost of $0.99 on BrowseComp-Plus (1K) versus linearly extrapolated $1.50-$2.75 for GPT-5-mini ingesting the same 6-11M input tokens. [^primary]
- Outlier source: Qwen3-Coder issued hundreds to thousands of sub-calls for single simple tasks (roughly 500 on average per correct OOLONG rollout versus roughly ten for GPT-5). [^primary]
- Runtime: the implementation used blocking, sequential LM calls with very long 95th-percentile runtimes, acknowledged as implementation-dependent; asynchronous sub-calls and sandboxed REPLs are named as future work that "can potentially significantly reduce" runtime and cost — a hypothesis, not a demonstrated result. [^primary]

# Caveats

- Costs reflect then-current provider pricing (OpenAI, Fireworks, Anthropic) and some baseline costs are reported as N/A in Table 1, making comparisons incomplete. [^primary]
- Author-reported from one preprint; runtime figures are specific to the paper's sequential implementation. [^primary]

# Related

- [Recursive scaffold failure modes](/concepts/recursive-scaffold-failure-modes.md)
- [Symbolic recursion via programmatic sub-calls](/concepts/symbolic-recursion-subcalls.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
