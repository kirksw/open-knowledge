---
type: Concept
title: "Multi-indexed memory exposed as tools"
statement: "A memory database can maintain multiple indexes and expose distinct access methods — explicitly key-based lookup and similarity-based retrieval — as selectable tools, so the retrieval strategy can vary per query."
description: "Scope: memory database design for tool-augmented retrieval in conversational QA."
tags: [memory, retrieval, database, tool-use]
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
  - /concepts/agentic-memory-retrieval-loop.md
  - /concepts/memory-retrieval-lags-storage.md
---

# Statement

Instead of a single embedding store with one similarity-search entry point, a memory database can be multi-indexed so that different query methods map to different access paths. TA-Mem explicitly names key-based lookup and similarity-based retrieval as supported query methods and exposes database-provided tools so the retrieval agent — not a fixed workflow — chooses the access path per query.

# Evidence

- TA-Mem's memory database is multi-indexed and designed for different types of query methods, explicitly including key-based lookup and similarity-based retrieval. [^primary]
- The retrieval tools are "provided by the database," and the retrieval agent selects appropriate tools based on the user input. [^primary]

# Caveats

- The abstract names only these two access methods; whether the full system provides additional tools (e.g., temporal or structural queries) is not determinable from the fetched page. [^primary]
- No per-index performance breakdown appears in the corpus, so the value of each access path is unmeasured here.

# Related

- [Agentic memory retrieval loop](/concepts/agentic-memory-retrieval-loop.md)
- [Memory retrieval lags memory storage](/concepts/memory-retrieval-lags-storage.md)

[^primary]: TA-Mem: Tool-Augmented Autonomous Memory Retrieval for LLM in Long-Term Conversational QA - https://arxiv.org/abs/2603.09297
