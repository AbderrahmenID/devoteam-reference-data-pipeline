# Pipeline Cleanup Report

Date: 2026-08-19
Scope: `Devoteam_AI_CLEAN_PIPELINE` only
Final status: **PIPELINE_GITHUB_BLOCKED_BY_DATA**

## Executive summary

The repository has been organized, documented, scrubbed of disposable caches and notebook outputs, and validated in a fresh Python environment. The Python test suite is healthy, the signed Phase 4 corpus and Phase 5 retrieval index verify successfully, and no GitHub file-size blocker was found.

The pipeline is not yet safe to describe as fully reproducible from raw evidence. The signed raw snapshot inventory names six source PDFs that are absent from the local snapshot. In addition, Tesseract is installed with English only; the French and Arabic language packs required by the multilingual extraction policy are missing. Raw client evidence and the approved Phase 8 template are confidential local inputs and must not be committed to a public repository.

## Cleanup metrics

| Metric | Result |
|---|---:|
| Files before cleanup | 872 |
| Files after cleanup | 768 |
| Repository size before cleanup | 177,905,384 bytes (169.66 MiB) |
| Repository size after cleanup | 175,994,282 bytes (167.84 MiB) |
| Cache files removed | 111 |
| Notebook files retained and sanitized | 13 |
| Gross disposable bytes removed | 1,950,316 bytes (1.86 MiB) |
| Raw snapshot files retained | 133 |
| Raw snapshot size retained | 120,714,006 bytes (115.12 MiB) |
| PDF files retained | 130 |
| Files larger than 10 MiB | 1 |
| Files larger than 25/50/90 MiB | 0 / 0 / 0 |
| GitHub size-limit blockers | 0 |
| Windows or user-specific source paths found after cleanup | 0 |
| Conflict markers found | 0 |
| Secret-pattern findings | 0 |

The after-cleanup count includes this report. Gross bytes removed comprise 1,654,218 bytes of Python/pytest caches and 296,098 bytes of embedded notebook outputs. Documentation and configuration added during the pass reduce the net size saving relative to the gross removal figure.

## Files removed or sanitized

The following removals were restricted to regenerable data:

| Classification | Location or pattern | Files affected | Bytes removed | Decision |
|---|---|---:|---:|---|
| CACHE | `.pytest_cache/**` | 5 | Included below | Deleted |
| CACHE | `src/devoteam_reference_ai/__pycache__/*.pyc` | 51 | Included below | Deleted |
| CACHE | `tests/__pycache__/*.pyc` | 55 | Included below | Deleted |
| CACHE total | All cache paths above | 111 | 1,654,218 | Deleted |
| GENERATED | Embedded output and execution metadata in `*.ipynb` | 13 notebooks | 296,098 | Cleared; notebook source retained |
| TEMP | None found with sufficient evidence | 0 | 0 | No action |
| DUPLICATE | Only zero-byte marker/error-file equivalence found | 0 | 0 | Retained where structurally meaningful |
| OBSOLETE | No signed phase package was proven obsolete | 0 | 0 | Retained |
| LOCAL_MACHINE_ONLY | No tracked machine artifact was proven safe to delete | 0 | 0 | Protected through ignore policy where applicable |

The signed root phase ZIP packages and all 13 phase notebooks were retained. Dependency tracing showed that the notebooks are active orchestration entry points and that the ZIP packages are checksum-pinned execution overlays. Removing either group would damage the documented Colab workflow or signed provenance.

## Data classifications and policy

### Private inputs — local only

- `data/snapshots/**/raw/**`: private client evidence and source inventory.
- `human_inputs/phase8/REFERENCE_TEMPLATE.docx`: approved local presentation template, 16,228,690 bytes (15.48 MiB).
- Real opportunity input files and generated internal exports.
- Local `.env` files and machine-specific credentials.

These paths are protected by `.gitignore`. Unique raw evidence must never be deleted as a cleanup shortcut. A public GitHub repository should contain documentation, code, configuration examples, schemas, tests, and small signed lineage metadata—not confidential evidence or deliverables derived from it.

### Canonical generated artifacts

Current authoritative corpus run:

`data/canonical/20260714T154731Z_129ff982c8/phase4_corpus_v1`

- 389 included pages and 19 excluded pages.
- 1,185 chunks.
- 161 references across 134 source documents.
- Signed Phase 4 manifest status: `PASS`.

Aligned retrieval index:

`data/indexes/20260714T154731Z_129ff982c8/phase5_hybrid_retrieval_v1`

- 1,185 indexed chunks.
- 768-dimensional embeddings.
- Signed Phase 5 status: `TECHNICAL_PASS`.
- Expert gold-set acceptance remains pending.

The processed corpus and index are reproducible generated products when all signed raw inputs and required system dependencies are present. They are ignored by default to prevent accidental publication of client-derived content. Small manifests, schemas, statistics, and integrity metadata are allowed where explicitly documented by the ignore rules.

## Reproducibility validation

Validation was performed from a newly created temporary virtual environment using the canonical root `requirements.txt`.

| Check | Result | Evidence |
|---|---|---|
| Fresh dependency installation | PASS | Canonical requirements installed successfully |
| Package/config import | PASS | Runtime dependencies and configuration imported |
| Python version | PASS | Python 3.10.11 |
| LibreOffice | PASS | Executable found at the standard Windows installation path |
| Tesseract executable | PASS | Executable found |
| Tesseract languages | FAIL | `fra` and `ara` language packs are missing; English is available |
| Signed raw snapshot integrity | FAIL | 129 files verified; 6 signed source files are missing; 0 hash mismatches |
| Signed Phase 4 verification | PASS | Corpus manifest and outputs verify |
| Signed Phase 5 verification | PASS | Retrieval manifest and outputs verify |
| Test suite | PASS WITH SKIP | 205 passed, 1 skipped |
| Final PDF/visual-QA release | PENDING | Phase 8 final release test is intentionally skipped |

### Missing files in the signed raw snapshot

The following paths are declared in `SHA256SUMS` but absent locally:

1. `raw/evidence/1R6ZGMRSbf7UsP7QaB-z0tTXtrzzFgTTA__Attestation BIAT Amélioration de la gestion Infrastructure et Production S.I. 2020 (5).pdf`
2. `raw/evidence/1YUwwzd8gyj5AkN7bCyCXVd9INbgGoyFi__Ministère de l'Economie Numérique et des Télécom.pdf`
3. `raw/evidence/1lBR4uKSSNeHYm4LCycXEsTHs0U2K9fLE__Ministere de lequipement et du transport Maroc_Attestation- amelioration orga et technique DSI- 2012.pdf`
4. `raw/evidence/1lrqoN0Ca3ciBwE3dGGiILXPONKWwyM-o__SUNU = Mise en place d'un API Gareway.pdf`
5. `raw/evidence/1rQf-m40Wrca-4bB-PDHpfYOWLalc7XEg__SUNU = Urbanisation et l'architecture du SI Groupe.pdf`
6. `raw/evidence/1xnmfOjsD7OP-XjlU8rOQTwgBhH_rIbBy__Attestation Ministère de l'éducation.pdf`

Restore these exact files from the controlled evidence store and rerun snapshot verification. Do not alter `SHA256SUMS` merely to make the check pass.

## GitHub-readiness checks

- `README.md`: **PASS** — purpose, architecture, setup, configuration, commands, outputs, tests, limitations, security, and MVP relationship are documented.
- `.gitignore`: **PASS** — secrets, local environments, caches, private raw evidence, local templates, internal generated outputs, and machine artifacts are protected.
- Project structure documentation: **PASS** — see `docs/PROJECT_STRUCTURE.md`.
- Architecture documentation: **PASS** — see `docs/PIPELINE_ARCHITECTURE.md`.
- Absolute Windows/personal paths in source and active configuration: **0**.
- Large-file check: **PASS by size** — no file exceeds 25 MiB; the only file above 10 MiB is the private local Phase 8 template.
- Confidential-data check: **BLOCKED until staged-content review** — 130 PDFs and client-derived artifacts exist locally. Ignore rules protect them, but a real Git index does not exist here, so staged-file verification cannot be performed.
- `git status --short`: **NOT AVAILABLE** — this directory is not a Git repository.
- `git diff --check`: **NOT AVAILABLE** — this directory is not a Git repository.

No commit, push, repository initialization, or sibling-repository modification was performed.

## Configuration changes

- Added canonical dependency entry points: `requirements.txt` and `requirements/pipeline.txt`.
- Replaced private Drive identifiers in active YAML and notebook configuration with environment-variable placeholders.
- Made `DEVOTEAM_PROJECT_ROOT` portable, defaulting to the repository root.
- Routed Phase 2 YAML loading through the shared environment-expanding configuration loader.
- Added `scripts/preflight.ps1` for machine, dependency, snapshot, corpus, and index checks.
- Replaced `README_START_HERE.md` with a compatibility pointer while preserving the filename required by signed notebooks.

These are packaging, documentation, portability, and validation changes. Pipeline extraction, corpus, retrieval, matching, recommendation, and presentation algorithms were not changed.

## Required actions before publication or clean replay

1. Restore the six missing raw evidence PDFs from the approved controlled source and verify their signed hashes.
2. Install the Tesseract French (`fra`) and Arabic (`ara`) language data and rerun `scripts/preflight.ps1`.
3. Create or place this folder in the intended Git repository, then inspect the exact staged file list before any commit.
4. Confirm that no `data/snapshots/**/raw/**`, real opportunity input, client-derived output, `.env`, credential, or local template is staged.
5. Run `git diff --check`, the full test suite, and the signed Phase 4/5 verification in that repository.
6. Complete the expert Phase 5 gold-set acceptance and Phase 8 PDF/visual-QA release when those governance inputs are available.

Until those actions are complete, the honest readiness state remains **PIPELINE_GITHUB_BLOCKED_BY_DATA**.
