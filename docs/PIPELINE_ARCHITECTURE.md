# Pipeline architecture

## Execution model

Numbered notebooks orchestrate signed phase packages. Reusable behavior is
implemented in `src/devoteam_reference_ai/`, configured by UTF-8 YAML in
`config/`, and covered by `tests/`. Every material stage pins its inputs by hash,
writes deterministic identifiers and manifests, and produces `_SUCCESS.json`
only after integrity checks pass.

## Stage 1 — foundation and policy

`config/project.yaml`, `security.yaml`, `models.yaml`, and `filters.yaml` define
the project boundary, read-only source policy, confidentiality levels, disabled
external-LLM default, and visible filter catalogue. `paths.py` rejects writes
outside the project root. Run manifests include configuration hashes.

## Stage 2 — inventory and ingestion

`phase2_drive.py`, `phase2_links.py`, `phase2_policy.py`, and
`phase2_pipeline.py` inventory the configured Google Drive source through a
read-only client. The stage discovers the master workbook, follows only
permitted evidence links, excludes forbidden categories and fields, downloads
immutable source copies, and records source hashes and evidence relationships.

Output: `data/snapshots/<snapshot_id>/` with private `raw/`, inventory/download
manifests, `SNAPSHOT_MANIFEST.json`, `SHA256SUMS.txt`, and `_SUCCESS.json`.

## Stage 3 — multilingual extraction and OCR

`phase3_extraction.py` and `phase3_pipeline.py` process PDF, Office, image, and
text sources. Digital PDF text is preferred when sufficient; scanned pages use
Tesseract with French, English, and Arabic. LibreOffice converts supported
Office inputs where required. Page metrics, extraction method, language,
redaction counts, and QA state are retained.

Canonical behavior is defined in `config/phase3_extraction.yaml`: 300-DPI PDF
rendering, `fra+eng+ara`, page-quality thresholds, checkpointing, redacted-text
generation, and no external LLM calls.

## Stage 3.1 — targeted repair

`phase3_1_repair.py` reprocesses only the pinned review/failure pages. It tests
controlled OCR segmentation modes and language combinations, preserves every
attempt's lineage, and selects a curated page result without modifying the
Phase 3 output. Irrecoverable pages remain excluded/quarantined.

## Stage 4 — trusted corpus

`phase4_corpus.py` verifies the repaired-page manifest and master/evidence link
hashes, normalizes redacted text, joins document evidence to reference rows,
and creates stable reference, page, and chunk identifiers. Chunking is
page-constrained with a 900-character maximum, 120-character overlap, and
120-character minimum. Quality-ineligible pages remain in `excluded_pages.csv`
and cannot enter retrieval.

Output: canonical page, chunk, document, and reference tables; filter values;
statistics; manifest; checksums; and success marker.

## Stage 5 — retrieval artifacts

`phase5_bm25.py` and `phase5_retrieval.py` construct aligned BM25 and dense E5
representations for every canonical chunk. The dense model and revision are
pinned in `config/phase5_retrieval.yaml`. `chunk_lookup.parquet`, BM25 rows,
embeddings, and FAISS rows must align exactly. Security filtering occurs before
scoring, and citation coverage is validated.

`phase5_1_evaluation.py` prepares the protected two-labeler expert evaluation.
`phase5_2_matching.py` adds deterministic reference normalization, eligibility,
duplicate control, scoring components, and quality gates. Neither stage changes
the Phase 4 corpus semantics.

## Stages 6–8 — controlled downstream use

- Phase 6 extracts multilingual opportunity requirements and proposes visible
  business filters for human review.
- Phase 7 ranks authorized evidence, enforces per-reference and portfolio gates,
  and emits citation-complete recommendations.
- Phase 8 builds deterministic reviewed dossiers from an approved template and
  approved shortlist. It does not copy raw evidence or award tender points.

These outputs are opportunity-specific and are not canonical corpus inputs.

## Integrity, evidence, and quarantine contract

- Original source mutation is forbidden.
- Source file hashes, document IDs, page IDs, reference rows, chunk IDs, and
  citation labels carry evidence lineage end to end.
- Page eligibility and quarantine decisions are explicit, not silently dropped.
- Security classification is enforced before retrieval scoring.
- Each completed stage is pinned by manifest and checksums.
- External LLM/embedding APIs are disabled unless separately approved.

## Current authoritative state

Snapshot `20260714T154731Z_129ff982c8`, Phase 4 `phase4_corpus_v1`, is the
authoritative corpus in this repository. Phase 5 `phase5_hybrid_retrieval_v1`
is the aligned retrieval build. Technical checks passed, while production
promotion remains blocked pending the two-expert gold set.
