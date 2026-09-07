---
type: Concept
title: "Prompt as external environment"
statement: "Storing an arbitrarily long prompt outside the model's context window — as a string variable in a persistent execution environment the model manipulates through code — lets a fixed-context LM process inputs of unbounded length."
description: "Scope: inference-time scaffolds (REPL/agent harnesses) for long-prompt processing."
tags: [long-context, inference-scaffold, context-window, repl]
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
  - /concepts/repl-offloading-vs-subcalling.md
---

# Statement

An arbitrarily long prompt need not be fed into the neural network: it can be held as a string variable in a persistent REPL environment while the root LM sees only constant-size metadata (prompt length, a short prefix, how to access parts) and iteratively writes code against it. Because intermediate results stay in REPL variables and only code plus stdout metadata enters the LM's history, the usable input length is decoupled from the base model's context size.

# Evidence

- The RLM paper argues that "arbitrarily long user prompts should not be fed into the neural network directly but should instead be treated as part of the environment." [^primary]
- Each loop iteration executes code in the REPL and appends only code plus metadata (short prefix/length) of stdout to the LM's history, which "forces ℳ to rely on variables and sub-calls to manage long strings instead of polluting its window"; iteration stops when the variable `Final` is set. [^primary]
- The scaffold handled 6-11M-token BrowseComp-Plus inputs with a base model (GPT-5) whose window is stated as 272K tokens, where direct ingestion hit input-context limits and scored 0.0. [^primary]

# Caveats

- Evidence is author-reported from a single preprint (arXiv:2512.24601v3); no independent replication exists in the corpus. [^primary]
- The mechanism presumes a coding-capable base model and an executable code environment; the paper's negative results show weak-coding models struggle in this scaffold. [^primary]

# Related

- [Symbolic recursion via programmatic sub-calls](/concepts/symbolic-recursion-subcalls.md)
- [REPL offloading versus sub-calling](/concepts/repl-offloading-vs-subcalling.md)

[^primary]: Recursive Language Models - https://arxiv.org/abs/2512.24601
