---
type: Concept
title: "Symbolic recursion via programmatic sub-calls"
statement: "When scaffold code can invoke LM sub-calls programmatically — in loops over prompt slices, with sub-RLM calls up to a depth limit — the number of LM invocations can scale from linear to quadratic in prompt length, exceeding what autoregressively verbalized sub-agent delegation can express."
description: "Scope: the recursion mechanism inside Recursive Language Models and comparable multi-agent scaffolds."
tags: [recursion, inference-scaffold, sub-agents, long-context]
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
  - /concepts/recursive-scaffold-cost-heavy-tail.md
---

# Statement

Symbolic recursion — code inside the execution environment calling LM sub-calls as ordinary functions, e.g., looping over slices of the stored prompt — is the design choice that lets an inference-time scaffold issue Ω(|P|) to Ω(|P|²) LM calls for a prompt P. Verbalized sub-agent delegation (Anthropic subagents, THREAD) expresses sub-calls autoregressively, which caps outputs at the base model's window and cannot realize this call-count scaling.

# Evidence

- The RLM paper's three design choices versus its ablation (Algorithm 2): the prompt lives outside the window behind a symbolic handle; the final answer is read from a REPL variable so outputs are not window-bounded; and symbolic recursion enables programmatic sub-calls, which the authors credit for Ω(|P|) to Ω(|P|²) sub-call scaling. [^primary]
- Depth parameterization: depth 0 = REPL without sub-calls; depth 1 = sub-LLM calls (`llm_query`); depth >1 = sub-RLM calls (`rlm_query`, falling back to `llm_query` at max depth). [^primary]
- Prior self-delegation systems that verbalize sub-calls autoregressively cap outputs at ℳ's window, and related decomposition methods (ViperGPT, THREAD, ReDel, Context Folding, AgentFold, DisCIPL) "are unable to handle long context inputs beyond the length of the base LM"; DisCIPL generates programs in one step with no recovery from mistakes, whereas RLMs refine via persistent-REPL execution feedback. [^primary]

# Caveats

- Realized sub-call counts vary enormously by base model: Qwen3-Coder issued hundreds to thousands of sub-calls for simple tasks (roughly 500 on average per correct OOLONG rollout) versus roughly ten for GPT-5. [^primary]
- The Ω(|P|)-Ω(|P|²) scaling is the authors' characterization of the mechanism's capability, not a measured cost curve; deeper recursion amplified syntax-error failures for Qwen3-Coder. [^primary]

# Related

- [Prompt as external environment](/concepts/prompt-as-external-environment.md)
- [Recursive scaffold cost heavy tail](/concepts/recursive-scaffold-cost-heavy-tail.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
