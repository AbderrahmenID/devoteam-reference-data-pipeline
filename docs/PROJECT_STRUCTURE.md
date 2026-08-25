# Project structure

This document is the repository inventory and source/output separation contract.
The repository contains 855 logical files before cache cleanup; generated
runtime data is intentionally kept local unless a small signed lineage artifact
is explicitly listed below.

| Path | Classification | Purpose | Commit policy | Generated | Required to reproduce |
| --- | --- | --- | --- | --- | --- |
| `src/devoteam_reference_ai/` | SOURCE_CODE | Production inventory, ingestion, extraction/OCR, repair, corpus, retrieval, evidence, validation, and export logic | Commit | No | Yes |
| `config/` | CONFIGURATION | Canonical security, source, OCR, chunking, quality, quarantine, retrieval, and output contracts | Commit | No | Yes |
| `requirements/`, `requirements.txt`, `pyproject.toml` | CONFIGURATION | Full and phase-specific Python dependency contracts | Commit | No | Yes |
| `scripts/` | SOURCE_CODE | Validation and controlled BRID command-line helpers | Commit | No | Yes |
| `tests/` | TEST | Unit, integrity, lineage, retrieval, and export controls | Commit | No | Yes |
| `docs/` | DOCUMENTATION | Canonical runbooks, architecture, structure, and cleanup decisions | Commit | No | Yes |
| `00_...ipynb` through `12_...ipynb` | DOCUMENTATION / SOURCE_CODE | Signed Colab orchestration for pipeline phases; outputs are cleared before Git review | Commit | No | Yes for notebook-driven runs |
| `PHASE_*_PACKAGE.zip` and release manifests | AUDIT / INTERMEDIATE_REQUIRED | Immutable, checksum-pinned overlays used by the signed notebooks | Commit only to the intended private repository | Yes, deterministic release packaging | Yes for historical notebook execution |
| `data/snapshots/<id>/raw/` | RAW_INPUT / SENSITIVE | Immutable local copies of the master workbook and evidence documents | Never commit | Yes, from authorized Drive source | Yes for full rebuild |
| `data/snapshots/<id>/{SNAPSHOT_MANIFEST.json,SHA256SUMS.txt,_SUCCESS.json}` | AUDIT | Snapshot identity and integrity | Commit only after confidentiality review | Yes | Yes for lineage |
| `data/extracted/<id>/phase3_extract_v1/` | INTERMEDIATE_REQUIRED / SENSITIVE | Page extraction, OCR checkpoints, and QA metadata | Local by default; only signed manifests are eligible | Yes | Yes unless extraction is rerun |
| `data/extracted/<id>/phase3_1_targeted_repair_v1/` | INTERMEDIATE_REQUIRED / SENSITIVE | Curated repaired pages, attempts, exclusions, and repair lineage | Local by default; only signed manifests are eligible | Yes | Yes unless repair is rerun |
| `data/canonical/<id>/phase4_corpus_v1/` | FINAL_ARTIFACT / SENSITIVE | Authoritative pages, chunks, reference/document catalogues, exclusions, and facets | Local by default; manifest, checksums, success marker, and statistics may be committed privately | Yes | Yes for MVP import and rollback |
| `data/indexes/<id>/phase5_hybrid_retrieval_v1/` | FINAL_ARTIFACT / SENSITIVE | BM25, dense, FAISS, lookup, and runtime metadata aligned to Phase 4 | Local by default; manifest/runtime/checksums may be committed privately | Yes | Yes for retrieval reproduction |
| `data/indexes/<id>/phase5_2_matching_hardening_v1/` | FINAL_ARTIFACT / AUDIT | Matching hardening outputs and quality gates | Local by default; signed manifests may be committed privately | Yes | Required for controlled downstream case |
| `data/evaluations/` | AUDIT / SENSITIVE | Expert-evaluation workbooks and status | Local only | Yes | Required for promotion, not baseline rebuild |
| `data/opportunities/`, `data/recommendations/`, `data/deliverables/` | GENERATED / SENSITIVE | Opportunity-specific analysis, evidence ranking, and dossiers | Local only | Yes | No for corpus rebuild |
| `human_inputs/phase6/OPPORTUNITY_SAMPLE_REDACTED.txt` and synthetic PDF | TEST | Safe controlled fixture | Commit | No | Yes for fixture checks |
| `human_inputs/phase6/OPPORTUNITY_INPUT.*` | RAW_INPUT / SENSITIVE | Optional real opportunity | Never commit | No | Only for that analysis |
| `human_inputs/phase8/REFERENCE_TEMPLATE.docx` | PRIVATE_REQUIRED_LOCAL | Approved 15.48 MiB presentation template, hash-pinned by config | Never commit by default | No | Yes for Phase 8 export |
| root `BRID_*` and Phase 7/8 audited exports | AUDIT / SENSITIVE | Synthetic-controlled outputs that still quote internal corpus evidence | Local only | Yes | No for corpus rebuild |
| `manifests/runs/`, `reports/generated/`, `logs/` | AUDIT / GENERATED_TEMP | Per-run manifests, reports, and logs | Ignore generated contents | Yes | No; regenerate |
| `__pycache__/`, `.pytest_cache/`, environments, model/OCR caches | CACHE / LOCAL_MACHINE_ONLY | Interpreter, test, dependency, and model caches | Delete and ignore | Yes | No |

## Canonical boundaries

- Source code never writes outside the repository root and never mutates the
  original Drive source.
- Raw inputs remain under the immutable snapshot or approved `human_inputs/`
  paths.
- Required extraction/repair intermediates stay under `data/extracted/`.
- The current processed corpus is Phase 4; retrieval artifacts are Phase 5.
- Opportunity-specific Phase 6–8 products are outputs, not corpus inputs.
- Signed manifests and hashes are the audit bridge between each boundary.

## Historical versions

This pipeline repository contains one authoritative canonical corpus:
`20260714T154731Z_129ff982c8/phase4_corpus_v1`. Later `v2` runtime assets live
in the sibling MVP repository and do not supersede or rewrite this signed source
lineage. The root phase packages are retained because notebooks verify and use
them; they are not duplicate corpus copies.
