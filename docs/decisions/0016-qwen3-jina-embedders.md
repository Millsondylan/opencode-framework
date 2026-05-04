# ADR-0016: Qwen3 General and Jina Code Embedders with Jina Tiny Reranker

## Status
accepted

## Context
Different content types benefit from different embedders, and rerank cost must stay bounded.

## Decision
Embed general text with Qwen3, code with Jina code embedder, and rerank with Jina tiny reranker.

## Consequences

### Positive
- Domain-specific embedders improve retrieval on code spans.
- Tiny reranker fits the local latency budget.
- Model choices are independently upgradable.

### Negative
- Two embedder pipelines double model-hosting surface.
- Mixed embeddings require careful index partitioning.

### Neutral
- Indexes are versioned so a migration can run offline.

## Alternatives Considered
- OpenAI embeddings (rejected: network dependency and cost).
- Single general embedder (rejected: weaker on code spans).

## Related
- ADR-0015
- ADR-0018
