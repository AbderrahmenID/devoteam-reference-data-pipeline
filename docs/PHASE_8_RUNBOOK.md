# Phase 8 — Controlled reference dossier generation

Phase 8 converts an approved Phase 7 shortlist into a template-derived internal
reference dossier. It uses only canonical reference metadata, deterministic
scoring outputs, and exact page-level citations.

## Decision boundary

- A real opportunity requires every Phase 7 recommendation to be reviewed and
  at least one row marked `SHORTLIST`.
- The signed synthetic sample may select the first five rows only to validate
  document generation.
- No LLM, external translation service, or hidden content generation is used.
- Source documents and page images are not copied into the deliverable.
- The generated dossier is always marked `DRAFT INTERNE — VALIDATION REQUISE`.
- A selected reference with weak textual evidence is retained only as an
  explicitly blocked review item; it cannot be considered client-ready.
- No client delivery or production promotion is automatic.

## Template use

`human_inputs/phase8/REFERENCE_TEMPLATE.docx` is hash-pinned. Phase 8 verifies
its summary-table and detailed-reference structure, then reproduces that visual
and semantic pattern with evidence-grounded project data. The example content
inside the template is never treated as approved source data.

## Outputs

`data/deliverables/<opportunity_id>/phase8_reference_dossier_v1/` contains:

- `REFERENCE_DOSSIER_DRAFT.docx`
- `REFERENCE_DOSSIER_DRAFT.pdf`
- `REFERENCE_DOSSIER_DATA.json`
- `PHASE_8_REPORT.md`
- `PHASE_8_MANIFEST.json`
- `SHA256SUMS.txt`
- `_SUCCESS.json`

The DOCX/PDF includes a summary table, detailed reference sheets, requirement
coverage, evidence excerpts, and clickable Drive/page citations. A human must
validate wording, confidentiality, and commercial suitability before use.
