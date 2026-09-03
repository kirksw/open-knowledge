---
type: Knowledge Summary
title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
description: "A benchmark paper reporting that LLMs can build runnable agent harnesses that approach human-engineered references in some domains, while feedback-driven self-evolution yields only small, unstable, executor-dependent gains."
tags: ["llm-agents", "agent-harness", "benchmarks", "self-improvement"]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-03T14:29:52Z"
sources:
  - id: record
    resource: "/sources/harnessdev-can-llms-create-and-evolve-their-own.md"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
  - id: primary
    resource: "https://arxiv.org/abs/2609.01437"
    title: "HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness?"
---

# Takeaway

HarnessDev finds that current LLMs can author complete, runnable agent harnesses that rival human-engineered references in some domains (writing, ML experimentation) but remain substantially behind on code and search/research, and that letting a model iteratively evolve its own harness from execution feedback yields only small, noisy, executor-dependent gains [^primary]. Self-harness-improvement works partially today, and the paper's failure modes read as a concrete checklist of what any self-modifying agent approach must guard against.

# What it is

**Benchmark design.** HarnessDev is an arXiv preprint benchmark (arXiv:2609.01437v1, dated September 1, 2026, from authors at ByteDance Seed, SUTD, Georgia Tech, M-A-P, and TokenWave.AI) that "shifts the unit of evaluation from task outputs to runnable infrastructure" [^primary]. It has two stages:

- **Creation:** a creator LLM builds a complete harness from a shared weak-but-runnable seed (a compatibility layer with no agent loop, tool policy, context management, state, verifier, retry/recovery, or stopping rule — unmodified it scores zero on every downstream benchmark) plus a spec and 1–3 development cases [^primary].
- **Evolution:** the creator iteratively revises its own harness using downstream execution feedback [^primary].

Coverage spans six creator LLMs, four domains, and five downstream benchmarks totaling 2,207 unique instances, with hidden evaluation tasks withheld from development: SWE-bench Pro public split (731 tasks, code), Terminal-Bench 2.1 (89, code), MLE-bench (75, data analysis), EQ-Bench3 (46, writing), and BrowseComp (1,266, research) [^primary]. The design separates the creator model, the development environment (Claude Code 2.1.177; Codex 0.144.3 for GPT-5.5), a frozen-harness executor model, and a fixed evaluator, so score changes reflect harness changes rather than model or evaluator drift [^primary]. As motivating evidence that harnesses matter, the paper cites GPT-5 solving 35.2% of Terminal-Bench 2.1 inside Terminus 2 versus 49.6% inside Codex CLI with identical weights [^primary].

**Creation findings.** Under Self-Eval (avg@3), the best creator (Opus 4.8, overall 67.8) remains below the human-engineered reference (86.2) [^primary]. Writing harnesses approach the reference, and on MLE-bench the medal rates of Opus 4.8 (32.9) and Gemini 3.1 Pro (32.4) exceed the human reference of 24.0, while the gap is largest for search/research and remains substantial for code [^primary]. The human-reference numbers are external system-level results pairing different harness–model combinations, not paired controls under one executor; three starred values come from OpenAI's GPT-5.6 release report [^primary]. Under Unified-Eval (all harnesses run by a fixed Gemini 3.1 Pro executor), rankings shift substantially, with Gemini 3.1 Pro leading (55.6 avg) ahead of Opus 4.8 (53.3) [^primary]. Cost does not predict quality: MLE-bench token use varies about nineteen-fold (e.g., GPT-5.5 medal 19.1 at 29.3M tokens vs DeepSeek V4 Pro 19.6 at 208.4M) [^primary].

**Quality of generated harnesses.** 77.8% of failed data-analysis tasks were attributed to harness defects rather than executor capability [^primary]. State/memory is the weakest capability: 11/18 code harnesses define a State class, but only one exposes a state-saving interface and one implements periodic checkpointing, and no checkpoint event appears in 26,679 recorded task trajectories [^primary]. Some generated mechanisms are dead code: of 108 code component instances, 72 trigger in real runs and 18 are never observed (all concerning state and memory); 124 of 587 writing features are confirmed dead code [^primary]. Edit size does not predict performance — Gemini added the fewest lines (1,006) among 18 code artifacts yet achieved the best Terminal-Bench score (68.8) [^primary]. Portability is limited and harness-specific: Qwen gains +17.6 on BrowseComp and +12.9 on MLE-bench under the Gemini executor, while Opus's SWE-bench Pro score falls from 69.3 to 33.0 and its search harness's duplicate-query rate rises from 10.1% to 88.2% [^primary].

**Evolution findings.** Across nine code-harness lineages (73 official versions, 64 adjacent switches), all five self-runtime creators improve on the visible feedback set, but held-out gains shrink to +1.43 to +4.44 points (mean +3.11), largest for Opus 4.8 [^primary]. Under a fixed Gemini runtime, only Opus improves on held-out tasks while the other three lineages regress (GPT-5.5 −10.32 points), showing gains depend strongly on the executing model [^primary]. Visible feedback is unreliable for version selection: feedback and held-out scores move in the same direction in only 34/64 switches (53.1%), and only 2/9 declared versions are held-out optimal [^primary]. Evolution is noisy: the same commit varies by about ±4.75 pair-score points between repeated runs, 27 of 64 official switches show gains inside the noise band, 8 regress on both benchmarks, and one switch contains no executable code change [^primary]. Failure diagnosis is the weakest step: the dedicated trajectory-inspection interface was called only twice, and creators explicitly inspected 0.5%–40.2% of the 189 feedback tasks depending on lineage [^primary]. One positive example: Opus noticed 99 of 100 runs reporting success while only 48 passed, traced the gap to premature completion, and added a completion check — feedback helped most when it "exposes a concrete failure mode and the resulting change is verified end to end" [^primary]. A constraint-compliance audit of every reported run found no harness obtained score through a prohibited route (e.g., hard-coded answers or scorer tampering) [^primary]. The paper positions itself against concurrent benchmarks (HarnessOpt-Bench, Evo-Bench, Meta-Agent Challenge), claiming novelty in connecting creation with evolution, separating creator from executor, and measuring execution cost and held-out generalization [^primary].

# Why it matters

This is direct, structured evidence on the issue author's question — how capable are LLMs at improving their own harness. The creation-stage answer is "surprisingly capable but uneven": runnable, benchmark-competitive harnesses are within reach of frontier models, yet the deepest gaps are exactly where harness engineering is hardest (search/research, code). The evolution-stage answer is more sobering for self-modifying agent approaches like the author's pi experiments: naive feedback-driven self-improvement overfits to visible scores and to the executing model, and observed gains often sit inside run-to-run noise. The paper's failure modes translate into a practical checklist for any self-modifying harness: verify changes end-to-end against a concrete failure mode; evaluate on held-out tasks rather than the feedback you optimized; enforce state/checkpointing explicitly (models neglect it); watch for dead code that inflates apparent sophistication; and distrust small score deltas that fall within repeated-run variance. The Unified-Eval and portability results add a caution: a harness "improved" by one model may actively hurt another, so self-modified harnesses should be validated per-runtime. Finally, the benchmark's core reframing — treating the harness as a developed, inspectable, testable artifact rather than fixed experimental configuration — is a useful lens for repositories like this one that accumulate agent-harness knowledge.

# Caveats

- Everything here derives from a single arXiv preprint (v1, September 2026) that does not appear to be peer-reviewed; all model, benchmark, and tool names (e.g., "Opus 4.8", "GPT-5.5", "Gemini 3.1 Pro") are as reported by the source and are attributed, not independently asserted [^primary].
- Human-baseline comparisons are uneven by the authors' own admission: external verified numbers pairing different harness–model combinations, three of them taken from OpenAI's GPT-5.6 release report, so "exceeding the reference" does not mean exceeding a paired human control [^primary].
- Statistical fragility is acknowledged in-paper: one trajectory per creator–runtime cell, held-out evaluation limited to SWE-bench Pro, and ±4.75-point repeated-run noise that swamps most observed evolution gains; some Unified-Eval table cells carry post-hoc sensitivity corrections (e.g., Opus SWE-bench Pro clean mean 49.1 vs 33.0 with a collapsed replica) [^primary].
- The paper measures model-external learning in the harness only; it explicitly does not claim this replaces parameter training [^primary].
- License: the paper is CC BY-NC-ND 4.0, so quotations above are short and attributed, and this summary is original writing; see the [source record](/sources/harnessdev-can-llms-create-and-evolve-their-own.md) for details.

# References

- [Source record](/sources/harnessdev-can-llms-create-and-evolve-their-own.md)

[^primary]: HarnessDev: Can LLMs Create and Evolve Their Own Agent Harness? - https://arxiv.org/abs/2609.01437
