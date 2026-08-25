# Phase 7 BRID controlled hybrid matching

## Purpose

Run the approved synthetic BRID case through the hardened Phase 5.2 hybrid
matching engine and assemble a reviewable reference portfolio. Every output is
`SYNTHETIC_TEST_ONLY`.

## Inputs

- Approved `BRID_PHASE_6_REVIEW.xlsx`.
- Signed Phase 5 BM25 and multilingual E5 indexes.
- Signed Phase 5.2 normalized reference contract.
- `config/phase7_brid_controlled_case.yaml`.

The workbook and signed inputs are pinned by SHA-256. Any later edit stops the
run rather than silently changing the result.

## Control model

- Authorization and the signed-client-attestation gate run before scoring.
- The 2019–2026 SDSI window, BFSI condition, and African-region condition are
  portfolio rules, not global candidate filters.
- User facets are available but never auto-applied.
- MATCH requirements enter retrieval.
- POLICY requirements become eligibility controls.
- SUBMISSION and NON_MATCH requirements remain visible but do not distort
  reference retrieval.
- The approved 100-point model is consumed, but no tender points are awarded
  automatically. Team and methodology account for 25 points outside the
  reference corpus.
- Citation correctness, Phase 5.1 expert evaluation, business shortlist
  approval, and production promotion remain human gates.

## Colab execution

1. Open `12_PHASE_7_BRID_HYBRID_MATCHING.ipynb`.
2. Choose **Runtime → Run all**.
3. Allow Google Drive mounting.
4. Keep the first model download running; the pinned
   `intfloat/multilingual-e5-base` model executes locally in Colab.
5. Confirm the final status is either:
   - `TECHNICAL_PASS_READY_FOR_EVIDENCE_AUDIT`, or
   - `TECHNICAL_PASS_WITH_PORTFOLIO_GAPS`.

The second status is not a software failure; it means the corpus could not
satisfy one or more approved portfolio conditions.

## Review

Open `BRID_PHASE_7_REVIEW.xlsx` in the printed output folder. Audit every cited
passage for factual support. Only then mark each recommended portfolio row
`SHORTLIST` or `REJECT`. Do not enter tender points in Phase 7.
