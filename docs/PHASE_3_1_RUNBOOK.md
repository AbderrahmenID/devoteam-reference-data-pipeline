# Phase 3.1 targeted QA repair

Phase 3.1 is an immutable overlay on the completed Phase 3 extraction. It does
not rerun the 385 accepted pages and does not overwrite Phase 3.

## Contract

- Input is pinned to the signed Phase 3 manifest and pages hash.
- Exactly 21 `REVIEW` or `FAILED` pages are targeted.
- OCR retries are bounded, page-checkpointed and resumable.
- PDF/image pages use Latin-first targeted OCR; Arabic-aware retries are added
  only when evidence indicates Arabic text.
- Image-only PowerPoint slides are repaired from embedded slide images.
- Only final `PASS` pages are marked `retrieval_eligible=true`.
- Unresolved pages remain excluded and receive internal visual previews.
- Source files and Phase 3 outputs are never modified.
- No external LLM is called.

## Outputs

`data/extracted/<snapshot>/phase3_1_targeted_repair_v1/` contains:

- `pages_curated.parquet`: all 408 pages with repair overlay and retrieval gate.
- `repaired_pages.parquet`: the 21 selected repair results.
- `repair_attempts.parquet`: bounded attempt-level audit data.
- `repair_results.csv`: safe operational summary without raw text.
- `unresolved_review_queue.csv`: any pages still excluded after repair.
- `review_previews/`: internal visual previews for unresolved pages.
- `PHASE_3_1_MANIFEST.json`, `SHA256SUMS.txt`, `_SUCCESS.json`.

## Downstream rule

Phase 4 may read only rows where `retrieval_eligible == true`. It must preserve
the Phase 2 source file ID, page number, source path and hashes for citations.
