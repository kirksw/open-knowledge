---
type: Source Record
title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? (arXiv:2609.01437v1)"
description: "Provenance record for the HarnessDev benchmark paper on LLMs creating and evolving agent harnesses, requested in issue #1."
resource: "https://arxiv.org/html/2609.01437v1"
issue: 1
tags: [agent-harness, self-improvement, benchmark, llm-engineering]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-03T15:10:20Z"
sources:
  - id: primary
    resource: "https://arxiv.org/html/2609.01437v1"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
---

# Provenance

- Requested in [issue #1](https://github.com/kirksw/open-knowledge/issues/1) by the repository owner.
- Fetched 2026-09-03T15:06:42Z: HTTP 200, `text/html`, 587,593 bytes, sha256 `0bbc8ed36a571a31bea861747c91722946b67c5fa352eb4bd39bb9aa94c73f93`; local corpus at `corpus/00-primary.txt`.

# Source overview

- **[primary]** arXiv preprint 2609.01437v1 [cs.SE], dated 1 Sep 2026, published as HTML v1 on arXiv. A benchmark/research paper with full text, tables, and appendices A–E. Affiliations per the paper: ByteDance Seed, Singapore University of Technology and Design, Georgia Institute of Technology, M-A-P, TokenWave.AI; core contributors listed include Yuhao Wu, Jingyuan Zhang, and Jiajun Shi. Project page: https://self-developing-agents.github.io/ (not fetched this run).

# Notes

- Introduces **HarnessDev**, a benchmark that shifts evaluation from task outputs to runnable infrastructure: a **Creation** stage (build a complete harness from a weak-but-runnable seed plus 1–3 development cases) and an **Evolution** stage (iteratively improve one's own persistent harness from downstream execution feedback), scored on capability (held-out task success) and efficiency (executor tokens). [^primary]
- Defines its object of study: the agent harness "manages the execution loop, tool use, context, failure recovery, and result verification." [^primary]
- On why self-harness work is hard: "When a model modifies its own harness, it is editing the execution substrate through which it acts." [^primary]
- Scope: six creator LLMs, four domains, five downstream benchmarks (SWE-bench Pro, Terminal-Bench 2.1, MLE-bench, EQ-Bench3, BrowseComp), 2,207 unique downstream instances, with evaluation tasks hidden from development. [^primary]
- Reports a null constraint-compliance audit: no created harness obtained score through hard-coded answers, hidden-test access, or bypassing the provider-neutral runtime interface. [^primary]
- Closest concurrent work named by the authors: HarnessOpt-Bench, Evo-Bench, and the Meta-Agent Challenge; HarnessDev is positioned as distinct in connecting Creation to Evolution, separating creator/executor models, and measuring execution cost. [^primary]

# Caveats

- **License:** the paper is CC BY-NC-ND 4.0 — brief quotation and canonical linking are permissible; long excerpts and derivative reproductions are not. Quotations here are kept short and summaries are original.
- Preprint v1 dated 2026-09-01, fetched 2026-09-03; figures could change in later versions.
- Model and benchmark names ("GPT-5.5", "Opus 4.8", "Gemini 3.1 Pro", "GPT-5.6 Sol", etc.) are as given in the paper and were not verified against external sources by this agent.
- Author-stated limitations: human baselines are uneven and not guaranteed optimal; Evolution has one trajectory per creator–runtime cell (one cell unfinished); post-freeze held-out evaluation covers SWE-Pro only.
- Security note from the paper: Creation runs execute in containers provisioned for reproducibility rather than containment; generated harnesses should be treated as untrusted code.

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
