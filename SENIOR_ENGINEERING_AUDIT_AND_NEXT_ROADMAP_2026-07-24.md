# Senior Engineering Audit and Next Roadmap

**Project:** Devoteam Reference AI
**Audit date:** 2026-07-24
**Authoritative product goal:** Given a current offer or RFP, rank the past Devoteam references that match it best, explain the match with evidence, and let an authorized user filter, compare, select, and export the final references.

## 1. Executive decision

The project has a strong, reproducible technical foundation. Every saved notebook from Phase 1 through Phase 8 has been executed, and no stored notebook cell contains an execution exception. The immutable-source controls, extraction lineage, chunk-level traceability, local multilingual embeddings, BM25 index, vector artifacts, manifests, checksums, tests, and sample dossier generation are valuable work and should be preserved.

However, the system is **not yet ready for a real Devoteam pilot or for claims of validated matching quality**.

The most important reason is architectural: the current Phase 7 recommendation pipeline identifies itself as `bm25_secure_baseline`; its manifest records zero dense-query embedding calls and zero cross-encoder calls. Therefore the production-facing matching result does not yet use the Phase 5 dense/hybrid capability. In addition, exclusions are collected but not enforced, `MUST` gaps do not block selection, and “citation coverage” currently tests citation-field completeness rather than semantic citation correctness.

The correct next action is **not to continue directly to a real RFP and not to start the user interface first**. The next action is an additive hardening subphase:

> **Phase 5.2 — Matching Engine and Data-Contract Hardening**

This keeps the agreed 15 main phases (0–14) unchanged; Phase 5.2 is a quality subphase, like Phase 3.1 and Phase 5.1.

The existing outputs must remain frozen as the v1 baseline. The hardening work should create new versioned artifacts and compare them against v1 before a real business case is run.

## 2. What was audited

The audit covered:

- Root project structure and all phase folders.
- Phase 0 charter and acceptance criteria.
- All executed notebooks and their saved cell outputs.
- Phase reports, manifests, success markers, checksums, and run folders.
- Central configuration files and model-selection state.
- Phase 4 corpus statistics and canonical filter values.
- Phase 5 retrieval code, index artifacts, bootstrap metrics, and latency results.
- The Phase 5.1 query-intake workbook and governance state.
- Phase 6 requirement/filter review workbook.
- Phase 7 recommendation workbook, evidence matrix, manifest, ranking logic, and filter behavior.
- Phase 8 configuration, template verification, generated DOCX/PDF, citation links, and rendered PDF pages.
- Placeholder application, API, deployment, logging, and generated-report folders.

## 3. Execution status by phase

| Phase | Verified state | Engineering interpretation |
|---|---|---|
| 0 — Charter | Complete | Strong enterprise-pilot scope and measurable acceptance criteria. |
| 1 — Foundation | Executed; 9 tests passed | Safe baseline and read-only source controls are established. |
| 2 — Inventory/snapshot | Executed | 6,244 Drive items inventoried; 155 unique evidence targets; 134 downloaded; 21 unavailable or inaccessible. |
| 3 — Extraction/OCR | Executed | 134 documents and 408 pages processed; extraction exceptions were explicitly surfaced. |
| 3.1 — Repair gate | Executed | Four failed pages repaired; 389 of 408 pages are eligible; 19 pages remain excluded, including 17 under review. |
| 4 — Canonical corpus | Executed | 1,185 chunks from 132 eligible documents; 161 canonical references; lineage is retained. Metadata normalization still needs hardening. |
| 5 — Retrieval | Executed, technical pass | BM25, E5 multilingual embeddings, vector artifacts, and hybrid code exist. Bootstrap results are diagnostic only. |
| 5.1 — Expert evaluation | Intake edited; workflow not advanced | Fifty queries are complete, but independent labeling/adjudication and frozen expert metrics remain unfinished. |
| 6 — Opportunity analysis | Executed on a synthetic redacted sample | Six requirements and three filter proposals were generated; all human decisions remain `PENDING`. |
| 7 — Recommendations | Executed on the sample | Ten recommendations were produced using a BM25-only secure baseline; all reviewer decisions remain `PENDING`. |
| 8 — Reference dossier | Executed on the sample | A clean six-page template-derived draft was generated, but it is not final, exact-template, or business-approved output. |
| 9–14 — Productization through handoff | Not started | PostgreSQL/OpenSearch services, API, web application, security/operations, deployment, pilot, and acceptance remain. |

## 4. Verified current results

### 4.1 Corpus and extraction

- 134 evidence documents were downloaded.
- 21 requested evidence targets are unavailable or inaccessible.
- 408 pages were processed.
- 389 pages are retrieval-eligible.
- 19 pages remain excluded; 17 of them require review.
- Phase 4 produced 1,185 chunks across 132 eligible documents and 161 canonical references.
- The corpus is primarily French, with smaller English and Arabic slices.
- Two duplicate chunks form one duplicate group and should be collapsed or controlled during reference scoring.

The count sequence `179 known references → 968 observed workbook rows → 161 canonical references` is not automatically a defect because those counts have different meanings. It still needs a formal reconciliation table so future reviewers can trace every exclusion, merge, empty row, and normalization rule.

### 4.2 Retrieval bootstrap

The Phase 5 bootstrap metrics are:

| Retriever | Recall@10 | Precision@5 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| BM25 | 1.000 | 0.196 | 0.867 | 0.900 |
| Dense/E5 | 0.880 | 0.164 | 0.701 | 0.744 |
| Hybrid/RRF | 0.980 | 0.188 | 0.839 | 0.873 |

Observed local latency was approximately 92.6 ms p50 and 171.1 ms p95.

These results are useful engineering diagnostics, but they are not expert quality evidence:

- The probes were generated from catalogue metadata that is also present in retrieval text.
- They are not the independently judged Phase 5.1 test set.
- BM25 currently outperforms the fixed hybrid configuration.
- The local latency result is not an API/OpenSearch production latency result.

Therefore the project must not assume that hybrid is best. Fusion, weights, candidate depth, thresholds, and reranking must be selected by a development judgment set and then evaluated once on a frozen test set.

### 4.3 Phase 5.1 evaluation intake

The query intake contains 50 complete, non-duplicate queries:

- 30 French, 10 English, and 10 Arabic.
- 20 standard, 10 acronym-heavy, 10 sparse, and 10 ambiguous.
- All query texts and business contexts are populated.
- All filter JSON is syntactically valid.
- All rows state that they were not derived from the reference corpus.
- All rows are marked approved for evaluation.

Remaining limitations:

- Four governance roles remain unassigned.
- Notes still say `DRAFT`.
- The saved file is `.xlsm`, while the notebook expects `.xlsx`.
- The workflow remains `AWAITING_QUERY_INTAKE`.
- Filter tests cover only `country` and `sector`; the evaluation does not yet prove year range, client, offering, evidence strength, document type, data-quality, technology, or compound-filter correctness.
- The set needs explicit unanswerable/negative and access-denied cases.

### 4.4 Phase 6 sample analysis

The sample run produced six requirements and three filter proposals. The parser correctly interpreted “depuis 2019” as an inclusive lower bound. However:

- It is a short synthetic fixture, not a real long offer/RFP.
- Every requirement and filter still has a `PENDING` human decision.
- The deterministic parser has not been validated on tables, annexes, scoring grids, multilingual sections, conflicting clauses, or amended documents.

### 4.5 Phase 7 sample recommendations

The Phase 7 manifest confirms:

- `retrieval_mode = bm25_secure_baseline`
- `dense_query_embedding_calls = 0`
- `cross_encoder_calls = 0`
- 10 recommendations
- 74 candidate-pool evidence rows across 17 candidate references
- 57 evidence rows displayed for the top 10 recommendations
- no business-approved shortlist
- no production-promotion permission

The difference between 74 and 57 is explained by two different grains, not by data loss. The manifest/report should make the distinction explicit.

### 4.6 Phase 8 sample dossier

The generated PDF is visually clean and all “open source” links tested are real hyperlinks. It remains a sample because:

- Five references were selected automatically from the synthetic fixture.
- Two references require evidence review.
- One selected reference covers only two of three `MUST` requirements.
- The configured maximum is two evidence items per reference, which cannot guarantee one supporting citation per required claim.
- The supplied template is fingerprint-checked, but the code generates a new document rather than populating the original template.
- Some evidence excerpts are cut mid-word.
- The document is untagged for accessibility and contains avoidable whitespace.
- Business and security validation are explicitly required.

## 5. Findings that must be corrected

### Critical

#### C1. The recommendation engine bypasses dense/hybrid retrieval

Phase 5 created E5 embeddings and hybrid infrastructure, but Phase 7 uses BM25 only. This is the central project gap because Phase 7 is the user-visible matching result.

**Required correction:** create one reusable, versioned retrieval service used by evaluation, recommendation, API, and UI. It must support BM25, dense, hybrid fusion, optional reranking, hard filters, access filters, and explanations. BM25 remains a baseline, not a discarded component.

#### C2. Opportunity exclusions are not enforced

Exclusions are loaded from the approved opportunity, but they are not applied when candidates are selected or ranked.

**Required correction:** compile exclusions into typed predicates, apply them before scoring where possible, record excluded reference IDs and reasons, and test zero-survival cases.

#### C3. `MUST` coverage is not an approval gate

The current ranking can shortlist a reference missing a mandatory requirement; this occurred in the sample.

**Required correction:** use three separate states:

- `ELIGIBLE`: all mandatory eligibility predicates pass.
- `CONDITIONALLY_ELIGIBLE`: human-approved exception with recorded rationale.
- `INELIGIBLE`: one or more mandatory requirements fail or lack adequate evidence.

An ineligible reference must not enter the final shortlist.

#### C4. Spreadsheet formula injection is present

The Phase 7 workbook contains `Evidence!E6 = #NAME?` because extracted source text beginning with `=` was interpreted as a formula. This is both a correctness and security defect.

**Required correction:** every string written to CSV/XLSX must be sanitized as untrusted content. Values beginning with spreadsheet formula trigger characters must be written as literal text, and regression tests must cover `=`, `+`, `-`, `@`, tab, CR, and LF prefixes.

#### C5. Citation completeness is presented as citation correctness

The current `citation_coverage = 1.0` means required citation fields are non-empty. It does not prove that the cited page supports the requirement or generated claim.

**Required correction:** expose separate metrics:

- citation-field completeness;
- citation resolvability;
- citation precision/relevance;
- claim support/faithfulness;
- mandatory-requirement evidence coverage.

### High priority

#### H1. Canonical metadata is not production-grade

Observed issues include:

- `reference_number` contains `#VALUE!` in 127 of 135 observed values.
- Country variants such as `Tunisie`/`tunisie` and multiple forms of Côte d’Ivoire.
- A city value used as a country.
- Client names differing only by punctuation, casing, or appended descriptions.
- Year represented as mixed free text instead of normalized start/end/ongoing fields.
- Evidence type and evidence strength overloaded in an “attestation available” field.

**Required correction:** introduce canonical IDs and display labels, ISO country codes, normalized date intervals, controlled evidence type/strength, alias tables, and an explicit raw-to-canonical mapping.

#### H2. Hybrid configuration is untuned

The fixed bootstrap hybrid is worse than BM25 on the current probes.

**Required correction:** compare BM25, dense, hybrid normalization, RRF, alternative weights, candidate depths, reference aggregation methods, and optional reranking. Tune only on a development set; keep the final test set frozen.

#### H3. Relative coverage threshold is not calibrated

Per-requirement scores are divided by the maximum result and a fixed relative threshold is used. If every result is weak, the best weak result can still appear covered.

**Required correction:** require both relative rank and an absolute/calibrated relevance condition. Add an `INSUFFICIENT_EVIDENCE` outcome instead of forcing every requirement to have a match.

#### H4. Evidence quality can be overstated

Using the maximum document-quality value from any evidence item can overstate the evidence quality of the whole reference.

**Required correction:** calculate evidence quality per requirement, distinguish contract existence from successful-completion evidence, and expose the weakest mandatory evidence state.

#### H5. Phase 5.1 does not test the full filter contract

The current filter queries cover only country and sector.

**Required correction:** add deterministic tests for year overlap, location/region, client, offering, technology, evidence strength, document type, data quality, status, access group, and combinations. User-visible facet counts must be computed from the same authorized result universe.

#### H6. Template semantics need an explicit decision

The current output is template-derived, not an exact native-template fill.

**Required correction:** Devoteam must choose one contract:

1. populate and preserve the supplied template exactly; or
2. approve a new generated template with the same information architecture.

The implementation and acceptance test must match that decision.

### Medium priority

- `config/project.yaml` still says the current phase is 1.
- `models.yaml` still describes embedding/reranker selection as unresolved even though Phase 5 pins E5.
- The central `logs` folder is empty.
- The central run-manifest registry is incomplete after Phase 1.
- `.pytest_cache` and `__pycache__` artifacts are synchronized to Drive.
- Phase 8 excerpt truncation should occur at word/sentence boundaries with an explicit ellipsis.
- Phase 5 writes a FAISS index, but the in-process live search calculates dense scores directly with NumPy. That is acceptable for 1,185 chunks, but production Phase 9 must have one explicit serving architecture.

## 6. Correct next execution order

### Step 1 — Freeze the current v1 baseline

Do not overwrite existing Phase 1–8 runs. Record their hashes, reports, metrics, and limitations as the v1 technical baseline.

### Step 2 — Build Phase 5.2: Matching Engine and Data-Contract Hardening

The next notebook/package should be additive and follow the current project method:

- `10_PHASE_5_2_MATCHING_ENGINE_HARDENING.ipynb`
- `config/phase5_2_matching_hardening.yaml`
- `src/devoteam_reference_ai/phase5_2_matching_hardening.py`
- `tests/test_phase5_2_matching_hardening.py`
- versioned output folder with manifest, checksums, report, and success marker

It should perform:

1. Canonical metadata normalization and lineage reconciliation.
2. Safe spreadsheet/CSV serialization.
3. Typed hard filters, soft preferences, exclusions, and access predicates.
4. BM25, dense, and hybrid candidate generation through one interface.
5. Reference-level aggregation that controls duplicate chunks/documents.
6. Mandatory eligibility gating.
7. Requirement-level evidence assessment.
8. Explainable score components without claiming calibrated probabilities.
9. v1-versus-v2 comparison on a development fixture.
10. Strict run manifest and quality-gate report.

### Step 3 — Repair the evaluation contract

Keep the 50 current queries as a versioned test-set candidate. Create a separate development set for tuning, and add:

- full filter catalogue tests;
- compound filters;
- unanswerable/negative cases;
- access-denied cases;
- adversarial spreadsheet/prompt-content cases;
- separate French, English, and Arabic reporting.

Finish independent labels/adjudication before any official quality claim or pilot.

### Step 4 — Run one real authorized offer/RFP through Phase 6

After Phase 5.2 passes:

- ingest one real authorized offer;
- extract requirements, mandatory eligibility rules, scoring criteria, exclusions, dates, geography, sector, technology, evidence constraints, and evaluation weights;
- preserve page/section citations back to the offer;
- require human approval before matching.

### Step 5 — Run Phase 7 v2 on the approved opportunity

The user should receive:

- ranked eligible references;
- filters for year/range, location, region, sector, client, offering, technology, engagement type, evidence strength, status, language, and authorization;
- an explicit match explanation by requirement;
- mandatory gaps and evidence weakness;
- citations to exact source pages;
- compare/select/reject/shortlist actions;
- stable results and facet counts under the same authorization context.

### Step 6 — Generate the Phase 8 v2 output

Only human-selected eligible references should be exported. Every factual statement must be connected to evidence; unsupported fields must be blank or marked `INSUFFICIENT_EVIDENCE`. The selected exact-template or approved-new-template contract must be honored.

### Step 7 — Productize only after the matching contract passes

Then continue the agreed main roadmap:

- Phase 9: PostgreSQL/OpenSearch data and search services.
- Phase 10: FastAPI backend and integration.
- Phase 11: web application, authentication, roles, filters, comparison, and approval workflow.
- Phase 12: security, testing, observability, MLOps/LLMOps, and regression evaluation.
- Phase 13: deployment, CI/CD, backups, recovery, monitoring, and runbooks.
- Phase 14: controlled user pilot, acceptance, documentation, training, and handoff.

## 7. Acceptance gates

### Phase 5.2 gate

- No spreadsheet formula execution from extracted text.
- No unresolved `#VALUE!`, `#NAME?`, or equivalent errors in governed outputs.
- Every canonical reference has raw lineage and normalized filter fields.
- Every exclusion and hard filter has a unit test and an audit reason.
- Ineligible references cannot be shortlisted.
- BM25, dense, and hybrid are compared; the selected configuration is evidence-based.
- Scoring components and retrieval versions are recorded.
- Duplicate chunks/references cannot inflate scores silently.

### Phase 6–8 real-case gate

- All extracted mandatory requirements are reviewed.
- All final references pass mandatory eligibility or have a formally approved exception.
- Every requirement status is `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, or `NOT_APPLICABLE`.
- Citation-field completeness, citation resolvability, and semantic citation correctness are reported separately.
- The final shortlist is human-approved.
- The export contains no unsupported factual claims.

### Pilot gate

Use the charter’s frozen expert-set targets after the labels are complete:

- Recall@10 at least 0.85.
- Precision@5 at least 0.75.
- nDCG@10 at least 0.75.
- MRR at least 0.75.
- Mandatory-filter correctness 100%.
- Citation correctness at least 98%.
- Unsupported factual claims below 2%.
- Template-field correctness at least 99%.
- Search p95 below 3 seconds and full analysis p95 below 20 seconds in the actual deployed environment.

Current bootstrap numbers must not be compared directly with these acceptance targets because the judgment protocol and relevance cardinality differ.

## 8. Authoritative references for the improvements

- OpenSearch explains that hybrid search combines keyword and semantic search through a search pipeline that normalizes and combines scores: https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/
- OpenSearch provides an experiment workflow that evaluates search configurations against query judgments, supporting evidence-based fusion/weight selection: https://docs.opensearch.org/latest/search-plugins/search-relevance/optimize-hybrid-search/
- OpenSearch supports aggregations with hybrid search, which is required for user-visible facets: https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/aggregations/
- OWASP documents CSV/formula injection when untrusted spreadsheet values are interpreted as formulas: https://owasp.org/www-community/attacks/CSV_Injection
- NIST’s Generative AI Risk Management Profile supports lifecycle-wide governance, measurement, documentation, and risk controls: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- RAGAS separates retrieval and generation evaluation rather than relying on one opaque score: https://aclanthology.org/2024.eacl-demo.16/
- MIRACL demonstrates multilingual retrieval evaluation with language-specific human relevance judgments: https://aclanthology.org/2023.tacl-1.63/

## 9. Final recommendation

Preserve the work already completed. Do not restart the project and do not discard BM25. Insert Phase 5.2 as a controlled, versioned hardening subphase, prove that the new recommendation engine correctly uses filters, exclusions, embeddings/hybrid retrieval, mandatory gates, and evidence, and only then run the first real offer.

That sequence gives Devoteam a defensible matching product rather than a notebook demonstration.
