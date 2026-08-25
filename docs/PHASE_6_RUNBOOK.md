# Phase 6 — Opportunity/RFP analysis and filter compilation

Phase 6 converts one RFP, AMI, terms of reference, or commercial need into a
reviewable requirement set and visible business-filter proposals. It is the
control layer between opportunity intake and retrieval/RAG.

## What the phase does

- Accepts TXT, Markdown, digital PDF, or DOCX input inside the clean project.
- Preserves source filename and SHA-256 without copying the original input.
- Minimizes emails, phone numbers, and explicit monetary values in analyzed text.
- Detects French, English, Arabic, or mixed content.
- Classifies units as `MUST`, `SHOULD`, `PREFERRED`, or `CONTEXT`.
- Proposes only filter values that exist in the signed Phase 4 catalogue.
- Marks hard, soft, context, and exclusion candidates without applying them.
- Produces a review workbook, JSON/JSONL outputs, report, manifest, and hashes.

## Security and quality boundary

- No external LLM is called.
- No raw opportunity text is written to logs.
- No business filter is silently confirmed or applied.
- Security filters remain mandatory and outside LLM/user control.
- Project value, team-member, and personal-data fields are never search filters.
- A scanned PDF with insufficient digital text stops with `OCR_REQUIRED`; it
  must use the already approved OCR route rather than a hidden low-quality path.

## Colab input behavior

The notebook looks under `human_inputs/phase6/` for exactly one file named
`OPPORTUNITY_INPUT` with a supported extension. If none exists, it creates and
uses `OPPORTUNITY_SAMPLE_REDACTED.txt` to validate the technical workflow.
Sample results prove operability only; they are not a real commercial result.

## Outputs

`data/opportunities/<opportunity_id>/phase6_opportunity_analysis_v1/` contains:

- `requirements.jsonl`
- `filter_proposals.json`
- `opportunity_analysis.json`
- `OPPORTUNITY_REVIEW.xlsx`
- `PHASE_6_REPORT.md`
- `PHASE_6_MANIFEST.json`
- `SHA256SUMS.txt`
- `_SUCCESS.json`

The technical phase passes when outputs are reproducible and all tests pass.
The opportunity remains `READY_FOR_HUMAN_REVIEW` until a business user approves
requirements and filter behavior.
