# Phase 5.1 — Expert retrieval evaluation

Phase 5.1 converts the technically verified Phase 5 index into a defensible,
expert-labeled retrieval evaluation. The same notebook is rerun at each human
checkpoint; it automatically advances to the next valid state.

## Checkpoint sequence

1. **Query intake** — 50 approved real or realistic opportunities are entered.
2. **Independent labels** — two Devoteam experts label the blinded candidate
   packets independently with relevance 0, 1, or 2.
3. **Adjudication and citation audit** — disagreements are resolved and a
   deterministic citation sample is checked.
4. **Frozen evaluation** — BM25, dense, and hybrid are compared with paired
   bootstrap confidence intervals and subgroup diagnostics.

The notebook never invents evaluation queries or labels. It never changes the
Phase 4 corpus, Phase 5 index, or original Drive source.

## Query-set rules

- Exactly 50 approved queries.
- At least 30 French, 5 English, and 5 Arabic queries.
- At least 5 acronym-heavy, 5 sparse, and 5 ambiguous queries.
- Queries must come from real opportunities or approved realistic scenarios.
- Queries must not be constructed from the reference corpus or bootstrap
  metadata. This prevents leakage and inflated retrieval scores.

## Relevance scale

- `0`: irrelevant.
- `1`: partially relevant.
- `2`: highly relevant.

Labeler packets hide retrieval system, rank, and score. Only candidate IDs,
evidence excerpts, metadata, and citations are visible.

## Decision boundary

Phase 5.1 may declare a baseline eligible for supervisor review, but it cannot
promote a production model automatically. Recall@10 is the primary pilot gate.
Secondary metrics, inter-labeler agreement, multilingual slices, failure
categories, citation correctness, security checks, and confidence intervals
remain visible in the final decision packet.

This frozen set is for one preregistered baseline comparison. Do not tune RRF
weights, prompts, embeddings, or rerankers on it. A later reranker experiment
requires a separate development set or a preregistered cross-validation plan.
