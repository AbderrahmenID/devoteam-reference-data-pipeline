# Devoteam Reference Data Pipeline

## Purpose

This repository builds the trusted multilingual reference corpus used by the
Devoteam Reference Intelligence MVP. It preserves document provenance, applies
deterministic quality and security controls, and produces corpus and retrieval
artifacts without requiring the MVP to process source documents at startup.

The repository contains internal Devoteam/client-derived material. Treat its
GitHub destination as **private** and review data classifications before sharing
any generated artifact.

## Pipeline Overview

Source documents → inventory → ingestion → text extraction / OCR → page repair
→ normalization → reference/evidence linkage → page-constrained chunking →
quality filtering and quarantine → trusted corpus → retrieval-ready artifacts.

Reusable implementation lives in `src/devoteam_reference_ai/`. The numbered
root notebooks are checksum-pinned Colab orchestrators for the signed phase
packages; they are retained because they are active audit and execution entry
points, not scratch notebooks.

## Main Outputs

The authoritative snapshot is `20260714T154731Z_129ff982c8`. Its canonical
corpus is `data/canonical/20260714T154731Z_129ff982c8/phase4_corpus_v1/`:

- `canonical_pages.parquet`: normalized eligible pages with lineage.
- `chunks.parquet`: 1,185 page-constrained retrieval chunks.
- `reference_catalog.parquet`: 161 trusted reference records.
- `documents_catalog.parquet`: document-level eligibility and metadata.
- `excluded_pages.csv`: quarantine/exclusion decisions.
- `filter_values.json`: approved retrieval facets.
- `PHASE_4_MANIFEST.json`, `SHA256SUMS.txt`, `_SUCCESS.json`: signed lineage and integrity state.

The aligned retrieval run is
`data/indexes/20260714T154731Z_129ff982c8/phase5_hybrid_retrieval_v1/`:

- `bm25_index.npz` and `bm25_vocabulary.json`.
- `embeddings.npy` and `chunk_lookup.parquet` with row alignment.
- `faiss.index` and `retrieval_runtime.json`.
- `PHASE_5_MANIFEST.json`, `SHA256SUMS.txt`, `_SUCCESS.json`.

Generated datasets are local/internal by default. Small signed manifests and
statistics are the only processed-data files intentionally eligible for Git.

## Repository Structure

- `src/devoteam_reference_ai/`: production inventory, extraction, repair, corpus, retrieval, evidence, and export modules.
- `config/`: canonical versioned behavior, security, OCR, chunking, quality, and retrieval configuration.
- `requirements/`: phase-specific locks plus `pipeline.txt`, the complete supported dependency set.
- `scripts/`: validation and controlled BRID command-line helpers.
- `tests/`: unit, contract, lineage, corpus, retrieval, and export tests.
- `data/`: local raw snapshots, required intermediates, canonical products, and retrieval artifacts.
- `human_inputs/`: approved local inputs; private real opportunities and the reference template are ignored by Git.
- `docs/`: runbooks, architecture, structure, and cleanup decisions.
- `manifests/`, `reports/`, `logs/`: runtime audit outputs.
- numbered root notebooks and signed phase packages: retained Colab orchestration and immutable phase audit history.

See `docs/PROJECT_STRUCTURE.md` for commit and reproducibility policy by folder.

## Prerequisites

- Python 3.10 or newer.
- Tesseract OCR with `eng`, `fra`, and `ara` language packs.
- LibreOffice (`soffice`) for Office-document conversion during extraction.
- Enough local disk space for private snapshots, OCR checkpoints, embeddings,
  and temporary rendered pages.

Poppler is not required by the current implementation; PDF rendering uses
PyMuPDF.

## Installation

```powershell
git clone https://github.com/AbderrahmenID/devoteam-reference-data-pipeline.git
cd devoteam-reference-data-pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:PYTHONPATH = (Resolve-Path .\src).Path
```

Run `powershell -ExecutionPolicy Bypass -File scripts/preflight.ps1` before a
pipeline stage. Model weights and OCR caches are downloaded/installed outside
the repository and must not be committed.

## Data Setup

Copy `.env.example` to `.env` only in an approved private runtime and export the
values into the shell or notebook environment. Set `DEVOTEAM_SOURCE_SHORTCUT_ID`
to the authorized read-only Drive shortcut. Do not commit `.env`, credentials,
private Drive identifiers, client source documents, or real opportunity files.

Phase 2 writes immutable private inputs beneath
`data/snapshots/<snapshot_id>/raw/`. Do not relocate the existing authoritative
snapshot: later manifests and the MVP lineage contract reference its current
relative paths. The Phase 8 approved template is expected locally at
`human_inputs/phase8/REFERENCE_TEMPLATE.docx` and is ignored by Git.

## Running the Pipeline

The repository intentionally does not add wrapper commands around the signed
phase implementations. Run the existing entry points in this order:

1. Foundation: run all cells in `00_PHASE_1_PROJECT_FOUNDATION.ipynb`.
2. Inventory and read-only ingestion: `01_PHASE_2_READ_ONLY_INVENTORY_SNAPSHOT.ipynb`.
3. Multilingual extraction/OCR: `02_PHASE_3_MULTILINGUAL_DOCUMENT_EXTRACTION.ipynb`.
4. Targeted repair: `03_PHASE_3_1_TARGETED_QA_REPAIR.ipynb`.
5. Canonical corpus: `04_PHASE_4_CANONICAL_CORPUS.ipynb`.
6. BM25/dense retrieval artifacts: `05_PHASE_5_HYBRID_RETRIEVAL.ipynb`.
7. Optional evaluation and downstream controlled cases: notebooks `06` through `12`.

Each notebook verifies the signed package, pinned input hashes, expected prior
success marker, and its own output manifest. Run notebooks from the repository
root and set `DEVOTEAM_PROJECT_ROOT` when the checkout is not in the historical
Colab folder layout.

The non-processing validation entry points are:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python scripts/validate_foundation.py --project-root .
python scripts/validate_phase2.py --project-root . --snapshot data/snapshots/20260714T154731Z_129ff982c8
python -m pytest -q
```

The synthetic BRID contract can be checked without processing confidential
source documents:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python scripts/run_phase6_brid_case.py
python scripts/run_phase7_brid_case.py --project-root . --mode bm25
```

`--mode bm25` is a mechanical local dry run only; it does not replace the pinned
hybrid production-candidate path.

## Validation

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/preflight.ps1
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -m pytest -q
python scripts/validate_foundation.py --project-root .
python scripts/validate_phase2.py --project-root . --snapshot data/snapshots/20260714T154731Z_129ff982c8
```

Successful canonical runs require `_SUCCESS.json`, a phase manifest, and a
matching `SHA256SUMS.txt`. Tests cover reference-ID stability, evidence lineage,
page and chunk integrity, quality/quarantine behavior, metadata contracts, and
retrieval/index alignment.

## Canonical Corpus

`phase4_corpus_v1` for snapshot `20260714T154731Z_129ff982c8` is authoritative
in this repository. Its manifest records 389 canonical pages, 19 excluded pages,
1,185 chunks, 161 references, and 134 documents. Phase 5 is technically valid,
but production promotion remains blocked pending two-expert gold-set review.

## Relationship to the MVP

Application consuming these artifacts:
[devoteam-reference-intelligence-mvp](https://github.com/AbderrahmenID/devoteam-reference-intelligence-mvp)

The sibling `devoteam-reference-mvp` repository consumes copies of the Phase 4
corpus and Phase 5 retrieval artifacts listed above. Its import manifest maps
`chunks.parquet`, `reference_catalog.parquet`, `filter_values.json`,
`bm25_index.npz`, `bm25_vocabulary.json`, `embeddings.npy`,
`chunk_lookup.parquet`, and the phase manifests. The MVP must not execute this
full pipeline during normal startup.

The MVP also maintains a separately reviewed runtime v2; this pipeline's signed
v1 artifacts remain the immutable source lineage and rollback baseline.

## Data Governance

- Raw source documents can contain confidential client and personal information.
- Original sources are read-only; pipeline writes stay inside the project root.
- Generated corpus and retrieval artifacts must retain source hashes, page IDs,
  reference IDs, eligibility decisions, and version manifests.
- Do not publish raw evidence, real opportunities, approval workbooks, audited
  dossiers, or private Drive identifiers to a public repository.
- External LLM and embedding API calls remain disabled by default.

## Known Limitations

- The expert Phase 5.1 gold set is still pending two reviewers.
- Full extraction requires authorized private inputs and external system tools.
- Early signed notebooks retain optional Colab-specific discovery behavior;
  portable runs should set `DEVOTEAM_PROJECT_ROOT` explicitly.
- Private source availability and the two-reviewer Phase 5.1 gold set remain
  external governance dependencies rather than files published in Git.
