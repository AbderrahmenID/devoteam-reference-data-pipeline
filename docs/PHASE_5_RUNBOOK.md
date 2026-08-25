# Phase 5 — Multilingual hybrid retrieval

Phase 5 builds the first searchable index from the signed Phase 4 corpus. It is
an indexing and retrieval phase, not an LLM generation phase.

## Retrieval design

- BM25 provides exact lexical and acronym matching.
- `intfloat/multilingual-e5-base` runs locally for French, English, and Arabic
  semantic retrieval. Its repository revision is pinned.
- Embeddings are normalized and stored as a rebuildable matrix plus an exact
  FAISS inner-product index.
- Reciprocal-rank fusion combines BM25 and dense candidates without pretending
  their raw scores are directly comparable.
- Mandatory authorization and hard metadata filters are applied before secure
  scoring. They cannot be disabled by a query or model.
- Search results retain chunk, document, page, hash, and Drive citation fields.

## Evaluation boundary

The notebook creates 50 deterministic metadata-grounded bootstrap probes to
test index operation, fusion, filters, and traceability. They are explicitly
labeled `BOOTSTRAP_METADATA_NOT_EXPERT` and cannot support a production-quality
claim.

It also creates `EXPERT_GOLD_SET_TEMPLATE.xlsx` for two Devoteam labelers. The
Phase 0 targets—Recall@10, Precision@5, MRR, and nDCG@10—remain a promotion gate
until 50–100 real opportunity queries are labeled and adjudicated.

## Outputs

`data/indexes/<snapshot>/phase5_hybrid_retrieval_v1/` contains:

- `bm25_index.npz` and `bm25_vocabulary.json`
- `embeddings.npy` and `faiss.index`
- `chunk_lookup.parquet`
- `bootstrap_queries.parquet`, `bootstrap_results.parquet`, and metrics
- `EXPERT_GOLD_SET_TEMPLATE.xlsx`
- model/runtime metadata, reports, hashes, and success marker

## Runtime expectation

The first run downloads a pinned 1.1 GB model and can take approximately
10–25 minutes depending on Colab networking and GPU availability. Embedding
rows are checkpointed, so rerunning in the same runtime resumes rather than
starting the matrix again. Later verified runs return immediately.
