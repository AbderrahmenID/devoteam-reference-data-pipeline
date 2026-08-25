# Phase 8 BRID v2 - audited reference export

## Purpose

This release converts the explicitly approved Phase 7 BRID evidence audit into
a template-aligned DOCX/PDF dossier. It is a controlled synthetic test and
must remain labelled `SYNTHETIC_TEST_ONLY`.

## Source contract

- `BRID_PHASE_7_EVIDENCE_AUDIT.xlsx` is hash-bound and is never modified.
- `PHASE_7_BRID_SHORTLIST_APPROVAL.json` records the user's explicit approval
  without inventing an approver name.
- `REFERENCE_TEMPLATE.docx` is hash- and structure-bound.
- Only the ten rows in `Audited Shortlist` are exported.
- Every exported row must be `SUPPORTED` and contain an exact Drive/page URL.
- All seven audited eligibility rules must pass.
- All eight MUST requirements must remain covered.
- `SCOPE-CLOUD` must remain an explicit non-blocking gap.
- No tender points are awarded automatically.

## Outputs

The release folder contains:

- `BRID_REFERENCE_DOSSIER_AUDITED.docx`
- `BRID_REFERENCE_DOSSIER_AUDITED.pdf`
- `BRID_REFERENCE_DOSSIER_DATA.json`
- `PHASE_8_BRID_REPORT.md`
- `PHASE_8_BRID_MANIFEST.json`
- `PHASE_7_BRID_SHORTLIST_APPROVAL.json`
- `SHA256SUMS.txt`
- `_SUCCESS.json`

## Status boundary

`TECHNICAL_PASS_AUDITED_EXPORT_COMPLETE` means the controlled synthetic export
is technically complete and visually verified. It does not authorize a real
tender response, production use, or client delivery. Phase 5.1 expert relevance
evaluation and final business/security validation remain separate gates.
