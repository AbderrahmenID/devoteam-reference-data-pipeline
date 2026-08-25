# Phase 4 — Canonical retrieval corpus

Phase 4 converts the signed Phase 3.1 page overlay into the only corpus that
later BM25, embedding, reranking, and LLM stages are allowed to read.

## Hard gates

- Input is pinned to the Phase 3.1 manifest and curated-page hash.
- Only `retrieval_eligible=true` pages are canonicalized.
- Raw OCR text is prohibited; only deterministically redacted text is used.
- Chunks never cross page boundaries, so every chunk has one exact page cite.
- Chunk IDs and text hashes are deterministic.
- `Valeur Projet`, team fields, and workbook comments are never ingested.
- Missing evidence and excluded pages remain visible in catalogues but never
  enter the chunk corpus.
- No embeddings, model downloads, OCR, or LLM calls occur.

## Outputs

`data/canonical/<snapshot>/phase4_corpus_v1/` contains:

- `canonical_pages.parquet`: the 389 eligible, cleaned, redacted pages.
- `chunks.parquet` and `chunks.jsonl`: stable page-constrained retrieval chunks.
- `documents_catalog.parquet`: all 134 downloaded evidence documents.
- `reference_catalog.parquet`: workbook reference rows, including broken links.
- `excluded_pages.csv`: the 19 non-indexable pages without page text.
- `filter_values.json`: available filter values and coverage counts.
- `corpus_statistics.json`: QA and distribution metrics.
- signed manifest, report, checksums, and success marker.

The signed baseline contains 1,185 chunks across 132 retrieval-eligible
documents, plus 161 workbook reference rows. These counts are pinned so a
silent change in cleaning, chunking, or source joins stops the run.

## Downstream contract

Phase 5 may use `chunks.parquet` only. It must preserve `chunk_id`,
`document_id`, `page_number_1_based`, `source_sha256`, `chunk_text_sha256`, and
the citation fields through BM25, vector search, reranking, and generation.
