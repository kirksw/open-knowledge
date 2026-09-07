---
type: Concept
title: "Adaptive semantic chunking for memory extraction"
statement: "A memory extraction agent can adaptively split input into sub-contexts based on semantic correlation and distill each into structured notes, rather than using fixed-size chunking."
description: "Scope: the ingestion/extraction stage of long-term conversational memory systems."
tags: [memory, chunking, extraction, conversational-qa]
status: draft
generated:
  by: "knowledge-agent"
  at: "2026-09-07T12:55:30Z"
sources:
  - id: record
    resource: "/sources/ta-mem-tool-augmented-autonomous-memory-retrieva.md"
    title: "TA-Mem: Tool-Augmented Autonomous Memory Retrieval for LLM in Long-Term Conversational QA (arXiv:2603.09297)"
  - id: primary
    resource: "https://arxiv.org/abs/2603.09297"
    title: "TA-Mem: Tool-Augmented Autonomous Memory Retrieval for LLM in Long-Term Conversational QA"
related:
  - /concepts/multi-indexed-memory-tools.md
  - /concepts/agentic-memory-retrieval-loop.md
---

# Statement

Memory extraction need not rely on fixed-size chunks: an extraction LLM agent can be prompted to adaptively divide input into sub-contexts based on semantic correlation and to extract the information into structured notes for storage, so chunk boundaries follow content rather than position.

# Evidence

- TA-Mem's extraction agent is "prompted to adaptively chuck [sic] an input into sub-context based on semantic correlation." [^primary]
- The extracted information is stored as structured notes in the multi-indexed memory database. [^primary]

# Caveats

- Abstract-level description only; no ablation in the corpus isolates the effect of adaptive chunking versus fixed-size chunking. [^primary]
- The abstract's "chuck" is an apparent typo for "chunk," quoted verbatim with [sic]. [^primary]

# Related

- [Multi-indexed memory exposed as tools](/concepts/multi-indexed-memory-tools.md)
- [Agentic memory retrieval loop](/concepts/agentic-memory-retrieval-loop.md)

[^primary]: TA-Mem: Tool-Augmented Autonomous Memory Retrieval for LLM in Long-Term Conversational QA - https://arxiv.org/abs/2603.09297
