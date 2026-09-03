---
type: Knowledge Summary
title: "Can LLMs create and evolve their own agent harness?"
description: "Frontier LLMs can build runnable agent harnesses from a weak seed and make genuine local improvements to their own harness, but evolution gains are small, noisy, executor-dependent, and bottlenecked by failure diagnosis — so structured evaluation, not raw self-modification, is what makes it pay off."
tags: [agent-harness, self-improvement, benchmark, llm-engineering]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-03T15:10:20Z"
sources:
  - id: record
    resource: "/sources/harnessdev-can-llms-create-and-evolve-their-own.md"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? (arXiv:2609.01437v1)"
  - id: primary
    resource: "https://arxiv.org/html/2609.01437v1"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
---

# Answer

Yes, but unevenly, and only locally. Frontier creator models can build a complete, runnable harness from a weak seed — the unmodified seed scores 0.00 on all five downstream benchmarks, so every point comes from creator-added execution logic — yet the best creator (Opus 4.8) averages 67.8 versus 86.2 for mature human-engineered references, matching them on writing (EQ-Bench3 84.6 vs 83.7), beating them on ML experimentation (MLE-bench medal 32.9 vs 24.0), and lagging badly on search (BrowseComp 52.4 vs 92.2). [^primary] Given execution feedback on their own harness, all five self-runtime creators improved on held-out tasks, but only by +1.43 to +4.44 points (mean +3.11); under a fixed executor only one of four lineages improved; and identical commits vary by about ±4.75 points, so the paper's verdict is that models make "useful local improvements, while robust evolution across unseen tasks and runtime models remains an open challenge." [^primary] The bottlenecks are specific: harness defects rather than executor capability accounted for 77.8% of failed ML-experimentation tasks, failure diagnosis is the weakest self-improvement step, and created harnesses almost never checkpoint state. [^primary] Interpretation for the issue's angle on unstructured self-modifying code (e.g. pi coding agent): HarnessDev suggests the payoff comes less from the act of self-modification than from the scaffolding around it — frozen candidate versions, held-out evaluation disjoint from the feedback signal, executor-portability checks, cost tracking, and audits against reward hacking. [^primary]

# Key concepts

- [The harness determines agent performance](/concepts/harness-determines-performance.md)
- [Harness creation gap](/concepts/harness-creation-gap.md)
- [Harness defects dominate failures](/concepts/harness-defects-dominate-failures.md)
- [Harness–executor overfitting](/concepts/harness-executor-overfitting.md)
- [Visible-feedback overfitting](/concepts/visible-feedback-overfitting.md)
- [Agents neglect failure diagnosis](/concepts/agents-neglect-failure-diagnosis.md)
- [Agents neglect state checkpointing](/concepts/agents-neglect-state-checkpointing.md)
- [Harness cost does not predict score](/concepts/harness-cost-does-not-predict-score.md)

# Evidence

**The harness matters as much as the model.** With identical weights, GPT-5 solved 35.2% of Terminal-Bench 2.1 inside Terminus 2 but 49.6% inside Codex CLI. [^primary] Harness quality, not just executor capability, drives outcomes: 77.8% of failed MLE-bench Data tasks were attributed to harness defects. [^primary]

**Creation: capable but uneven.** Six creators, four domains, five downstream benchmarks (SWE-bench Pro public split, Terminal-Bench 2.1, MLE-bench, EQ-Bench3, BrowseComp; 2,207 instances) with evaluation tasks hidden from development. [^primary] Best Self-Eval results versus reference: writing 84.6 vs 83.7, ML experimentation 32.9 vs 24.0 (creator wins), search 52.4 vs 92.2, SWE-Pro 69.3 vs 80.0, Terminal-Bench 64.8 vs 88.8 (creator lags). [^primary] Creator strategies differ: Opus rewrites the execution stack, GPT-5.5 adds a large monolithic agent, DeepSeek/Qwen/Seed extend the seed with modules, Gemini edits the runner in place. [^primary]

**What creators get wrong.** State/memory is the weakest component: 11/18 Code artifacts define a State class but only one exposes a state-saving interface and only one implements periodic checkpointing; no checkpoint event appears in 26,679 recorded trajectories. [^primary] Much generated code is dead: 18 of 108 Code component instances (all state/memory) and 124 of 587 Writing features were never observed in real runs. [^primary]

**Executor coupling.** Fixing the executor to Gemini 3.1 Pro reshuffles rankings: Opus's SWE-Pro score falls from 69.3 to 33.0 (its harness hard-codes a 120-step limit around the original executor), while several Qwen and DeepSeek harnesses improve (Qwen +17.6 BrowseComp, +12.9 MLE-bench). [^primary]

**Cost and size don't predict quality.** MLE-bench token use varies about nineteen-fold across created harnesses; GPT-5.5 reached medal 19.1 with 29.3M tokens while DeepSeek V4 reached 19.6 with 208.4M. [^primary] Gemini added the fewest net lines (1,006 of 17,111) yet obtained the best Terminal-Bench score (68.8). [^primary]

**Evolution: real but fragile.** All five self-runtime creators improved on the visible feedback pair and on held-out tasks (+1.43 to +4.44, mean +3.11); under fixed Gemini only Opus improved held-out while the other three regressed (GPT-5.5 worst at −10.32). [^primary] Evolution is noisy and non-monotonic: identical commits vary by ±4.75 pair-score points, only 2 of 64 official version switches show clear positive evidence beyond noise, feedback and held-out scores agree in direction only 53.1% of the time (34/64), and only 2/9 declared versions are held-out optimal. [^primary] Diagnosis is the weakest step: the trajectory-analysis interface was called only twice, and explicitly inspected cases cover 0.5%–40.2% of the 189 feedback tasks. [^primary] Volume of self-testing correlates weakly with downstream score (Spearman 0.13–0.26, not significant) while revision calls correlate at 0.57 (p≤.0005) — testing helps when the creator reads the failure, makes a targeted change, and re-verifies, as when Opus traced a 99-reported/48-passed gap to premature completion and added a verified completion check. [^primary] The paper reports a null reward-hacking audit (no hard-coded answers, hidden-test access, or runtime bypass). [^primary]

# Caveats

- Single preprint source (arXiv v1, 2026-09-01); figures may change in later versions, and model names are as given in the paper without external verification.
- Human references are not paired controls: they pair external system-level results, and three starred values come from OpenAI's GPT-5.6 release report without being rerun by the authors; distance-to-reference should not be read as an absolute ceiling.
- Evolution evidence is single-trajectory: one lineage per creator–runtime cell (one cell unfinished), held-out evaluation on SWE-Pro only; the authors caution against population-level conclusions.
- Average-of-3 reporting masks variance; independent creations from the same model can differ sharply.
- License CC BY-NC-ND 4.0: quotations kept short; summaries here are original.

# References

- [Source record](/sources/harnessdev-can-llms-create-and-evolve-their-own.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/html/2609.01437v1
