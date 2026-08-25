# Phase 2 runbook — read-only inventory and immutable snapshot

## Purpose

Phase 2 identifies the source corpus, discovers the master workbook,
follows only policy-permitted Google Drive evidence links, downloads an
immutable copy into the clean project, and records cryptographic hashes.

## Safety boundary

- The source Drive facade exposes read/list/download/export only.
- No source create, update, move, rename, permission, or delete operation exists.
- `Valeur Projet`, `Équipe`, and `Équipe Intervenante` values are never
  accessed by link-discovery logic or persisted.
- Website and logo links are never followed as evidence.
- No OCR, embeddings, search index, template generation, or LLM call occurs.

## Run

Open `01_PHASE_2_READ_ONLY_INVENTORY_SNAPSHOT.ipynb` in Google Colab and
select **Runtime → Run all**. The notebook installs this extension package
automatically; do not unzip it manually.

## Successful output

A new folder is created under `data/snapshots/<snapshot_id>/`. It is valid
only when `_SUCCESS.json` and `SNAPSHOT_MANIFEST.json` exist and all files
match `SHA256SUMS.txt`.

## Reruns

Every successful rerun creates a new immutable snapshot. Existing snapshots
are never overwritten. Failed runs keep `_FAILED.txt` and never receive the
success marker.
