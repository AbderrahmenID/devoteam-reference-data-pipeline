# Phase 5.2 — Matching engine and data-contract hardening

Phase 5.2 is an additive hardening release between retrieval construction and
real-offer recommendation. It does not replace, rewrite, or delete Phase 4,
Phase 5, Phase 5.1, or the Phase 7 v1 baseline.

## Purpose

The release makes the matching contract suitable for a senior-level pilot:

- normalize country, region, sector, offering, dates, evidence type, and
  controlled capability/technology/engagement tags while retaining raw values;
- create stable user-facing reference IDs without trusting broken spreadsheet
  reference numbers;
- apply access authorization, hard filters, and exclusions before scoring;
- use one interface for BM25, dense, and hybrid retrieval;
- separate eligibility policies from semantic offer requirements;
- enforce complete `MUST` coverage before a row can enter the shortlist;
- suppress duplicate catalogue rows backed by the same evidence document;
- neutralize spreadsheet formula injection in every CSV/XLSX handoff;
- separate citation completeness, cryptographic integrity, lexical support
  proxy, and pending human citation-correctness review;
- compare the preserved Phase 7 v1 baseline with the controlled v2 sample;
- sweep fusion weights using Phase 5 bootstrap probes without presenting those
  metadata-derived probes as expert relevance judgments.

## Control order

1. Verify pinned Phase 4 and Phase 5 artifacts and SHA-256 hashes.
2. Build an additive normalized reference contract.
3. Resolve the approved/user-visible offer filters.
4. Apply authorization and shortlist eligibility.
5. Apply hard filters and explicit exclusions.
6. Produce BM25 and local E5 candidates.
7. Fuse candidates with reciprocal-rank fusion.
8. Apply deterministic evidence reranking.
9. Aggregate evidence at stable reference and requirement grain.
10. Enforce complete content-`MUST` coverage.
11. Suppress repeated evidence-document groups.
12. Produce explainable results, facets, evidence, audit workbook, manifest,
    checksums, and quality gate.

Year and location are eligibility filters. They are not hidden relevance boosts.
Facet counts are computed only from references already authorized for the user.

## Run

Open `10_PHASE_5_2_MATCHING_ENGINE_HARDENING.ipynb` in Colab and run all cells.
The notebook locates:

`MyDrive/Devoteam internship/Devoteam_AI_CLEAN_PIPELINE`

For local validation, set:

```bash
export DEVOTEAM_PROJECT_ROOT=/absolute/path/to/Devoteam_AI_CLEAN_PIPELINE
export DEVOTEAM_PHASE5_2_PACKAGE=/absolute/path/to/PHASE_5_2_MATCHING_ENGINE_HARDENING_PACKAGE.zip
```

The first normal run may download the pinned multilingual E5 model. The Phase 5
passage embeddings are reused and are not rebuilt.

## Outputs

`data/indexes/<snapshot>/phase5_2_matching_hardening_v1/` contains:

- `reference_contract.parquet` and `reference_contract.jsonl`
- `data_quality_issues.csv`
- `facet_values.json`
- `sample_recommendations.parquet` and `.json`
- `sample_ineligible_candidates.parquet`
- `sample_evidence.parquet` and `.jsonl`
- `sample_requirement_coverage.csv`
- `sample_filter_audit.json`
- `sample_facet_counts.json`
- `sample_policy_requirements.json`
- `CITATION_AUDIT_SAMPLE.xlsx`
- `fusion_sweep.csv`
- `v1_v2_comparison.json`
- `PHASE_5_2_QUALITY_GATE.json`
- `PHASE_5_2_MANIFEST.json`
- `reports/PHASE_5_2_REPORT.md`
- `SHA256SUMS.txt`
- `_SUCCESS.json`

## Decision boundary

A `TECHNICAL_PASS_SAMPLE_ONLY` result means the integration and controls passed.
It does not prove that hybrid retrieval is more relevant than BM25. Phase 5.1
adjudicated expert labels remain mandatory before selecting production fusion
weights, enabling a cross-encoder, or claiming production retrieval quality.

After a successful run, use the Phase 5.2 engine for the first real authorized
offer, but retain business shortlist review and the Phase 5.1 promotion gate.
