---
type: Source Record
title: "Recursive Language Models (arXiv:2512.24601)"
description: "Source record for the arXiv preprint introducing Recursive Language Models, an inference-time scaffold that treats arbitrarily long prompts as an external environment."
resource: "https://arxiv.org/abs/2512.24601"
issue: 5
tags: [long-context, inference-scaffold, recursion, agents, benchmarks]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-07T13:40:20Z"
sources:
  - id: primary
    resource: "https://arxiv.org/abs/2512.24601"
    title: "Recursive Language Models"
  - id: s2
    resource: "https://arxiv.org/html/2512.24601v3"
    title: "Recursive Language Models (v3 full-text HTML)"
---

# Provenance

- Requested in [issue #5](https://github.com/kirksw/open-knowledge/issues/5) by the repository owner.
- Both requested URLs were fetched 2026-09-07 with HTTP 200 (see `fetch-report.json`). The `primary` request for the arXiv abs page was captured as the full-text HTML at `https://arxiv.org/html/2512.24601` via redirect; the `s2` request fetched `https://arxiv.org/html/2512.24601v3` directly. The two corpus files are byte-for-byte identical (sha256 `1be5ec7d2700811a2a6f4a6ddeb63654e458f80c9bc5ed5159a96dde15152393`), so there is effectively one distinct source document. [^primary]

# Source overview

- [^primary]: *Recursive Language Models*, a full research paper on arXiv (stamp "arXiv:2512.24601v3 [cs.AI] 11 May 2026") by Alex L. Zhang, Tim Kraska, and Omar Khattab (MIT CSAIL). The page states "License: CC BY 4.0". It contains abstract, introduction, method with Algorithms 1-2, benchmark results tables, trajectory analyses, related work, limitations, and appendices with training details, negative results, prompts, benchmark details, and cost/runtime plots. The paper links reference code at `https://github.com/alexzhang13/rlm`.
- [^s2] is the same v3 full text served at the versioned HTML URL; it adds no distinct content.

# Notes

- Core idea: RLMs are "a general inference paradigm that treats long prompts as part of an external environment"; the authors argue that "arbitrarily long user prompts should not be fed into the neural network directly but should instead be treated as part of the environment." [^primary]
- Architecture: the prompt is a string variable in a persistent REPL; the root LM sees only constant-size metadata (length, short prefix, access instructions) and iteratively writes Python code. History appends code plus stdout metadata, which "forces ℳ to rely on variables and sub-calls to manage long strings instead of polluting its window"; iteration stops when the variable `Final` is set. [^primary]
- Reference implementation: GPT-5 (medium reasoning) as root with GPT-5-mini for recursive calls; Qwen3-Coder-480B-A35B as an open-weight alternative. Motivated by "context rot" in frontier models. [^primary]
- Headline results (author-reported): on BrowseComp-Plus with 1,000 documents (6-11M tokens), base GPT-5 and CodeAct variants scored 0.0 (input-context limits; GPT-5 window stated as 272K tokens) while RLM(GPT-5, depth=1) scored 91.3 and depth 2-3 reached 92.0. On OOLONG-Pairs, base models scored ≤0.1 F1 versus 58.0 (GPT-5 RLM depth=1) and up to 76.0 (depth 3). Abstract medians: RLMs beat a compaction agent by 26%, CodeAct with sub-calls by 130%, and Claude Code by 13%, "while having comparable cost". [^primary]
- Appendix D.2 (20-query subset) states "RLM(GPT-5) is the only model / agent able to achieve and maintain perfect performance at the 1000 document scale"; the depth-0 ablation reached 90% there. [^primary]
- Training results: RLM-Qwen3-8B, rejection-fine-tuned on ~1,000 filtered turns distilled from 2,250 RLM(Qwen3-Coder) trajectories, beats base Qwen3-8B as an RLM by a median of 28.3% and is over 3× faster with lower cost. RLVR training of RLM(Qwen3-4B-Instruct-0527) on MRCRv2's 64k/2-needle split generalized to the 1M/8-needle split (Figure 3b). [^primary]
- Negative results and failure modes (Appendix B and trajectory analyses): system prompts do not transfer across models; weak-coding models (Qwen3-8B) struggle; thinking models with insufficient output budgets fail; Qwen3-Coder "will try to perform a subcall on everything, leading to thousands of LM subcalls for basic tasks" (roughly 500 sub-calls on average for correct OOLONG rollouts versus roughly ten for GPT-5); one OOLONG-Pairs trajectory "never returned the answer it built up in its code environment through sub-LM calls"; syntax errors propagate through recursion depth. [^primary]
- Authors' stated limitations: guardrails are under-explored and RLM complexity "may lead to unintentional side-effects like exploding sub-call costs"; harder, more natural long-context evaluations remain future work. [^primary]
- Author hypotheses, explicitly not demonstrated results: trajectories as bootstrappable training signal, native RLM training "could result in another axis of scale", and async sub-calls / sandboxed REPLs "can potentially significantly reduce" runtime and cost. [^primary]

# Caveats

- Single-document corpus: `primary` and `s2` are byte-identical copies of one preprint; all evidence is author-reported with no independent replication or third-party evaluation available. [^primary]
- Small evaluation sets: 50 S-NIAH tasks, 150 BrowseComp-Plus instances, 50 OOLONG tasks, 20 OOLONG-Pairs queries; the Appendix D.2 scaling result uses 20 random queries. Several observations are qualitative trajectory readings. [^primary]
- Cost figures reflect then-current provider pricing (OpenAI, Fireworks, Anthropic); Table 1 reports some closed-agent costs as N/A (e.g., Claude Code without offloading), so cost comparisons are incomplete. [^primary]
- Internal tension to verify against the source: Table 1 lists OOLONG-Pairs at 32K tokens while Appendix D.1 describes contexts spanning 1,024-1,048,576 tokens. Figure-derived claims (Figures 1, 3, 10, 11) rest on in-text descriptions. [^primary]
- Licensing: the paper page states CC BY 4.0, permitting short attributed quotations; the linked GitHub repository's license was not verifiable from the corpus. [^primary]
- Terminology: "recursive" here means scaffolded self-invocation of LMs, not architectural recurrence (recursive neural networks) or context-window extension techniques. [^primary]

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
[^s2]: Recursive Language Models (v3 full-text HTML) - https://arxiv.org/html/2512.24601v3
