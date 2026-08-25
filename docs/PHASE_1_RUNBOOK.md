# Phase 1 Runbook

## Purpose

Create and validate the clean engineering foundation. This phase does not open
or process the source corpus.

## Colab execution

1. Place `00_PHASE_1_PROJECT_FOUNDATION.ipynb` and
   `PHASE_1_FOUNDATION_PACKAGE.zip` in `Devoteam_AI_CLEAN_PIPELINE`.
2. Open the notebook in Google Colab.
3. Run all cells from top to bottom.
4. Authorize the normal Google Drive mount when prompted.
5. Do not change `PROJECT_ROOT` unless the Drive folder was deliberately renamed.
6. Confirm the final output says `PHASE 1 FOUNDATION: PASS`.

## Expected outputs

- Validated configuration under `config/`.
- Reusable code under `src/devoteam_reference_ai/`.
- Passing automated tests under `tests/`.
- Runtime directories under `data/`, `logs/`, `manifests/`, and `reports/`.
- A run manifest under `manifests/runs/`.

## Safe rerun behavior

The notebook verifies the package checksum and refuses to overwrite a different
existing file. Matching files are skipped. This makes normal reruns idempotent.

## Failure response

- Do not manually delete failed outputs.
- Preserve the error and run manifest.
- Correct the specific configuration or path issue.
- Rerun from the first cell.
