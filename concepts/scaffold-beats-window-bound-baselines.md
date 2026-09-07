---
type: Concept
title: "Scaffolds beat window-bound baselines on long prompts"
statement: "An inference-time REPL scaffold with recursive sub-calls outperformed window-bound baselines — direct ingestion, compaction, retrieval-augmented CodeAct, and Claude Code — on long-prompt benchmarks and kept operating past the base model's context limit."
description: "Scope: author-reported RLM benchmark results (arXiv:2512.24601) on S-NIAH, BrowseComp-Plus, OOLONG, OOLONG-Pairs, CodeQA, LongCoT-mini."
tags: [long-context, benchmarks, inference-scaffold, evaluation]
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
  - /concepts/symbolic-recursion-subcalls.md
---

# Statement

On the RLM paper's benchmarks, a scaffolded model dominated every window-bound alternative tested: it was the only approach to score above zero at 6-11M-token inputs, and it beat compaction, retrieval-augmented, and conventional agent baselines by double-digit medians at comparable reported cost. The result held for both a frontier closed model (GPT-5) and an open-weight alternative (Qwen3-Coder-480B-A35B).

# Evidence

- BrowseComp-Plus with 1,000 documents (6-11M tokens): base GPT-5 and both CodeAct variants scored 0.0 (input-context limits; GPT-5 window stated as 272K tokens); RLM(GPT-5, depth=1) scored 91.3, depth 2-3 reached 92.0; CodeAct(+BM25) scored 51.0; the compaction agent 70.5. [^primary]
- Information-dense tasks: OOLONG gains of 28.4% (GPT-5) and 33.3% (Qwen3-Coder) at depth 1 over base; OOLONG-Pairs F1 of 58.0-76.0 for GPT-5 RLMs versus ≤0.1 for both base models and 0.1 for the GPT-5 compaction agent. [^primary]
- Abstract-reported medians across evaluated benchmarks on GPT-5: +26% over a compaction agent, +130% over CodeAct with sub-calls, +13% over Claude Code, "while having comparable cost"; average RLM(GPT-5, depth=1) cost of $0.99 versus linearly extrapolated $1.50-$2.75 for direct GPT-5-mini ingestion of the same inputs, while outperforming compaction and retrieval baselines by over 29%. [^primary]
- Scaling curves (Figure 1, 2^13-2^20 input tokens): "For context lengths beyond 2^14, the RLM consistently outperforms GPT-5". [^primary]

# Caveats

- All numbers are author-reported from one preprint with small evaluation sets (20-150 instances; the 1,000-document scaling claim uses a 20-query subset); no independent replication or third-party evaluation exists in the corpus. [^primary]
- No head-to-head against a native ~10M-token long-context model: the only native long-context reference is a 1M-context Gemini 3.1 Pro appearing in one MRCRv2 figure as a reference point. [^primary]
- Baseline costs are partly incomplete (some closed-agent entries reported as N/A in Table 1), and pricing reflects 2026 provider rates. [^primary]

# Related

- [Prompt as external environment](/concepts/prompt-as-external-environment.md)
- [Symbolic recursion via programmatic sub-calls](/concepts/symbolic-recursion-subcalls.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
