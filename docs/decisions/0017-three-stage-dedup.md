# ADR-0017: Three-Stage Dedup (SimHash, MinHash LSH, Semantic Cosine with NLI)

## Status
accepted

## Context
Agent logs and diffs contain many near-duplicates that inflate cost and dilute retrieval.

## Decision
Deduplicate in three stages: SimHash for near-exact, MinHash LSH for approximate, then semantic cosine with NLI for paraphrase.

## Consequences

### Positive
- Each stage removes a different class of duplicate at minimal cost.
- NLI catches semantic paraphrase that hashes miss.
- Pipeline order keeps expensive steps on a small residual.

### Negative
- NLI model hosting adds a runtime dependency.
- False positives on borderline semantic matches need tuning.

### Neutral
- Thresholds are per-corpus tunable.

## Alternatives Considered
- SimHash only (rejected: misses paraphrase).
- NLI on all pairs (rejected: quadratic cost).

## Related
- ADR-0015
- ADR-0018
