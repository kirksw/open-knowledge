---
type: Knowledge Summary
title: "How Recursive Language Models process arbitrarily long prompts"
description: "RLMs keep the prompt outside the context window in a REPL environment that recursively invokes LM sub-calls, beating window-bound baselines on long-prompt benchmarks at comparable median cost but with heavy-tailed costs and recursion-amplified failure modes."
tags: [long-context, inference-scaffold, recursion, agents, benchmarks]
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
  - id: s2
    resource: "https://arxiv.org/html/2512.24601v3"
    title: "Recursive Language Models (v3 full-text HTML)"
---

# Answer

Recursive Language Models (RLMs) never feed a long prompt into the network directly: the prompt is stored as a string variable in a persistent REPL environment, and the root LM iteratively writes Python code against it while seeing only constant-size metadata (length, a short prefix, how to access parts), with intermediate results kept in REPL variables rather than the context window [^primary]. Because code inside the environment can itself invoke LM sub-calls programmatically — including sub-RLM calls up to a configurable recursion depth — neither inputs nor outputs are bounded by the base model's context size, which the authors describe as an abstracted "language model" without context limitations [^primary]. On author-reported benchmarks, RLM(GPT-5) scored 91.3 on a 6-11M-token BrowseComp-Plus suite where base GPT-5 and CodeAct variants scored 0.0 after hitting input-context limits, with abstract-reported medians beating a compaction agent by 26%, CodeAct with sub-calls by 130%, and Claude Code by 13% at comparable cost [^primary]. The trade-offs are heavy-tailed costs (a Qwen3-Coder run averages roughly 500 sub-calls per correct rollout versus roughly ten for GPT-5, and the authors warn of "exploding sub-call costs"), long sequential runtimes, and failure modes such as syntax errors that propagate through recursion depth [^primary]. Compared with alternatives: retrieval-augmented and coding agents "can only fill up the underlying LLM's context window with snippets" (CodeAct+BM25 scored 51.0 versus 91.3), compaction is "rarely expressive enough for tasks that require dense access throughout the prompt", verbalized sub-agent delegation stays window-bound, and native long-context models are treated as an orthogonal direction with no head-to-head against a ~10M-token model in the paper [^primary]. All evidence is author-reported from a single preprint fetched twice as byte-identical copies [^s2]; claims that trained "native" RLMs could form a new axis of scale are explicitly hypotheses.

# Key concepts

- [Prompt as external environment](/concepts/prompt-as-external-environment.md)
- [Symbolic recursion via programmatic sub-calls](/concepts/symbolic-recursion-subcalls.md)
- [Scaffolds beat window-bound baselines on long prompts](/concepts/scaffold-beats-window-bound-baselines.md)
- [REPL offloading versus sub-calling](/concepts/repl-offloading-vs-subcalling.md)
- [Recursive scaffold failure modes](/concepts/recursive-scaffold-failure-modes.md)
- [Recursive scaffold cost heavy tail](/concepts/recursive-scaffold-cost-heavy-tail.md)
- [Distilling scaffold trajectories into small models](/concepts/distilling-scaffold-trajectories.md)
- [Scaffold RL length generalization](/concepts/scaffold-rl-length-generalization.md)

# Evidence

## Architecture and inference loop

- An RLM is an inference-time scaffold around a base LM ℳ with context size K: the arbitrarily long prompt P lives in a persistent REPL; each iteration executes code, keeps intermediate variables in REPL state, and appends only code plus stdout metadata to the LM's history — the paper says this "forces ℳ to rely on variables and sub-calls to manage long strings instead of polluting its window"; iteration stops when the variable `Final` is set and is returned as the response. [^primary]
- Three design choices distinguish RLMs from a "deceptively similar" ablation (Algorithm 2): (1) the prompt sits outside the window behind a symbolic handle; (2) the final answer is read from a REPL variable, so outputs are not bounded by ℳ's window; (3) symbolic recursion — code can invoke LM sub-calls programmatically, e.g., in loops over slices. [^primary]
- Recursion depth parameterizes the loop: depth 0 = REPL without sub-calls; depth 1 = sub-LLM calls (`llm_query`); depth >1 adds sub-RLM calls (`rlm_query`, falling back to `llm_query` at max depth). Reference implementation: GPT-5 (medium reasoning) root with GPT-5-mini sub-calls; Qwen3-Coder-480B-A35B as open-weight alternative; motivated by "context rot" in frontier models. [^primary]

## Performance and scaling (paper-demonstrated, author-reported)

- Beyond-window operation: on BrowseComp-Plus with 1,000 documents (150 instances, 6-11M tokens), base GPT-5 and both CodeAct variants scored 0.0 (input-context limits; GPT-5's window stated as 272K tokens) while RLM(GPT-5, depth=1) scored 91.3 and depth 2-3 reached 92.0. [^primary]
- Information-dense tasks: OOLONG gains of 28.4% (GPT-5) and 33.3% (Qwen3-Coder) at depth 1; on OOLONG-Pairs both base models scored ≤0.1 F1 versus 58.0 (GPT-5 depth 1) and 76.0 (GPT-5 depth 3). Scaling curves (Figure 1, 2^13-2^20 tokens): "For context lengths beyond 2^14, the RLM consistently outperforms GPT-5". [^primary]
- Abstract-reported medians on GPT-5: +26% over a compaction agent, +130% over CodeAct with sub-calls, +13% over Claude Code, "while having comparable cost". Cost versus direct ingestion of 6-11M tokens: $0.99 average for RLM(GPT-5, depth=1) versus a linearly extrapolated $1.50-$2.75 for GPT-5-mini ingestion, while outperforming compaction and retrieval baselines by over 29%. [^primary]
- Ablation nuance: on CodeQA with Qwen3-Coder, depth 0 (66.0) beat all sub-calling variants — REPL offloading alone suffices for some tasks; programmatic sub-calling mainly helps information-dense inputs. Beyond long context, on LongCoT-mini, RLM(GPT-5.2, depth=1) scored 50.6 versus 38.7 base (65.6 with explicit decomposition hints), but without hints scored below base on MATH (5.6 vs 26.0) and CS (11.0 vs 40.4). [^primary]
- Trainability: RLM-Qwen3-8B (rejection fine-tuning on ~1,000 filtered turns distilled from 2,250 trajectories, 48 H100-hours) beats base Qwen3-8B as an RLM by a median of 28.3%, is over 3× faster with lower cost, and "even approaches the quality of vanilla GPT-5 on three long-context tasks"; RLVR training on MRCRv2's 64k/2-needle split generalized to the 1M/8-needle split. [^primary]

## Compute/cost and failure-mode trade-offs

- Cost shape: median RLM runs are cheaper than median base-model runs, but averages are higher due to outlier trajectories; costs scale with task complexity. Runtimes use blocking, sequential LM calls with very long 95th-percentile runtimes; asynchronous sub-calls and sandboxed REPLs are named future work, not demonstrated. [^primary]
- Documented failure modes: Qwen3-Coder launched hundreds to thousands of sub-calls for simple tasks (roughly 500 on average per correct OOLONG rollout versus roughly ten for GPT-5); one OOLONG-Pairs trajectory built the correct answer then "never returned the answer it built up in its code environment through sub-LM calls"; syntax errors are frequent in Qwen3-Coder trajectories and propagate through recursion depth; the `FINAL()`/`FINAL_VAR()` answer protocol is brittle (16% and 13% of distilled turns misused them). [^primary]
- Authors' negative results (Appendix B): one system prompt does not transfer across models; models with weak coding ability struggle as RLMs; thinking models with insufficient output-token budgets fail (Qwen3-235B-A22B improved 30%→38% on OOLONG but some trajectories exhausted output on thinking tokens). Authors flag guardrails as under-explored and warn RLM complexity "may lead to unintentional side-effects like exploding sub-call costs". [^primary]

## Comparison with alternatives

- Long-context models: the paper treats architectural/retraining approaches as orthogonal and evaluates task-agnostic scaffolds; the only native long-context reference is a 1M-context Gemini 3.1 Pro shown in the MRCRv2 figure as a reference point — no head-to-head against a native ~10M-token model exists. [^primary]
- Retrieval-augmented generation: prior retrieval/coding agents treat external data as an environment but "can only fill up the underlying LLM's context window with snippets", remaining bounded with respect to user input; empirically CodeAct(+BM25) scored 51.0 on BrowseComp-Plus (1K) versus 91.3 for RLM depth 1. [^primary]
- Conventional agent tool use / sub-agents: CodeAct-style agents load the prompt directly into the model; prior self-delegation systems (Anthropic subagents, THREAD) verbalize sub-calls autoregressively, capping outputs at ℳ's window; related decomposition methods (ViperGPT, ReDel, Context Folding, AgentFold, DisCIPL) "are unable to handle long context inputs beyond the length of the base LM", and DisCIPL generates programs in one step without recovery from mistakes, whereas RLMs refine via persistent-REPL execution feedback. [^primary]
- Compaction: summarize-on-full-context is "rarely expressive enough for tasks that require dense access throughout the prompt"; empirically the compaction agent collapsed on OOLONG-Pairs (0.1 F1 with GPT-5) while scoring well on BrowseComp-Plus (70.5). [^primary]

# Caveats

- Single-preprint evidence: both fetched URLs are byte-identical copies of arXiv:2512.24601v3 (11 May 2026) [^s2]; all scores, costs, and medians are author-reported, with no independent replication or third-party evaluation in the corpus.
- Small evaluation sets (20-150 instances per benchmark; the 1,000-document scaling result uses a 20-query subset) limit statistical strength; several findings are qualitative trajectory readings. [^primary]
- Cost comparisons use then-current provider pricing and contain N/A entries for some closed agents; runtime numbers are acknowledged as implementation-dependent. [^primary]
- Minor internal tension in the source: Table 1 lists OOLONG-Pairs at 32K tokens while Appendix D.1 describes contexts spanning 1,024-1,048,576 tokens. [^primary]
- Interpretation (not source-grounded): the architecture's dependence on a coding-capable base model and an executable REPL suggests applicability limits for non-code domains, but the paper does not test this.

# References

- [Source record](/sources/recursive-language-models.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
[^s2]: Recursive Language Models (v3 full-text HTML) - https://arxiv.org/html/2512.24601v3
