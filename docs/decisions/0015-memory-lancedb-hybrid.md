# ADR-0015: Memory System on Embedded LanceDB with Hybrid BM25 Plus Dense Rerank

## Status
accepted

## Context
Agent memory needs fast similarity over large corpora without a managed vector service.

## Decision
Use embedded LanceDB with BM25 for lexical recall and a dense reranker for precision on top results.

## Consequences

### Positive
- Local file store with no network dependency.
- Hybrid retrieval outperforms either BM25 or dense alone.
- Rerank applied only to the top K keeps latency low.

### Negative
- Single-process access pattern limits concurrency.
- LanceDB version upgrades require data-file rewrites.

### Neutral
- Can be swapped for pgvector later without API changes.

## Alternatives Considered
- pgvector only (rejected: weaker lexical performance).
- Pinecone or Weaviate (rejected: external dependency).

## Related
- ADR-0016
- ADR-0017
