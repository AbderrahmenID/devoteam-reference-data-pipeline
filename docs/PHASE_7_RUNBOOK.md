# Phase 7 — Secure retrieval and evidence-backed recommendations

Phase 7 consumes the signed Phase 5 index and an approved Phase 6 opportunity.
It retrieves evidence requirement-by-requirement, aggregates evidence to stable
reference IDs, applies deterministic business scoring, reports coverage gaps,
and produces a human-reviewable shortlist.

## Fast baseline by design

This release uses the signed multilingual BM25 index. It does not download a
new model, call an external embedding API, invoke an LLM, or use a cross-encoder.
That keeps the notebook fast and secure while Phase 5.1 expert labeling is
pending. Hybrid and cross-encoder experiments may be added later, but they may
not be promoted without controlled expert evaluation.

## Control order

1. Verify the Phase 5 manifest and index hashes.
2. Verify the complete Phase 6 output hash chain.
3. Require human review for a real opportunity. The packaged synthetic sample
   may use its explicit development-fixture approval only.
4. Apply security classifications and approved hard filters before BM25 scoring.
5. Retrieve evidence independently for every approved requirement.
6. Aggregate evidence from documents to canonical reference IDs.
7. Score relevance, weighted coverage, evidence quality, recency, and approved
   soft-preference fit.
8. Apply deterministic client-diversity control.
9. Preserve chunk, document, page, file hash, and Drive citation provenance.
10. Require human shortlist approval before template generation.

## Outputs

`data/recommendations/<opportunity_id>/phase7_evidence_recommendations_v1/`
contains:

- `recommendations.parquet` and `recommendations.json`
- `evidence_matrix.parquet` and `evidence_matrix.jsonl`
- `requirement_coverage.csv`
- `requirement_gaps.json`
- `RECOMMENDATION_REVIEW.xlsx`
- `PHASE_7_REPORT.md`
- `PHASE_7_MANIFEST.json`
- `SHA256SUMS.txt`
- `_SUCCESS.json`

Sample output is technical validation only. Real recommendations remain internal
until business review, expert evaluation, security approval, and template review.
