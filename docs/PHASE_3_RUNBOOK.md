# Phase 3 runbook — multilingual extraction

## Purpose

Extract page-level French, English, and Arabic text from the pinned Phase 2
snapshot. Digital PDF text is preferred. Tesseract OCR runs only on pages
without sufficient digital text. DOCX and PPTX are converted to PDF when
LibreOffice is available and use a native-text fallback otherwise.

## Run

Open `02_PHASE_3_MULTILINGUAL_DOCUMENT_EXTRACTION.ipynb` in Colab and use
**Runtime → Run all**. Do not unzip the package manually.

## Resume behavior

Every completed document writes an atomic checkpoint. If Colab disconnects,
rerun the same notebook; completed documents are verified and skipped.

## Quality behavior

There is no blanket human-transcription checkpoint. Pages are classified as
`PASS`, `REVIEW`, `FAILED`, or `BLANK`. Only the targeted review queue must be
inspected before low-quality pages can support generated claims.

## Security

Raw text stays `INTERNAL`. A deterministically redacted text field is created
for later retrieval and LLM gates. Phase 3 makes no LLM calls and never writes
to the original source or the immutable Phase 2 snapshot.
