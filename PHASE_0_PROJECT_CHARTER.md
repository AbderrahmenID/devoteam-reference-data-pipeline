# Devoteam Reference Intelligence Platform

## Phase 0 — Project Charter and Governance Baseline

**Document status:** Approved — Phase 0 complete
**Version:** 1.0
**Date:** 14 July 2026
**Project stage:** Phase 0 complete; Phase 1 authorized

---

## 1. Executive summary

Devoteam currently stores commercial reference information across a master spreadsheet and supporting documents in Google Drive. Finding the strongest past missions for a new RFP is largely manual, inconsistent, and difficult to audit.

The project will create a multilingual reference-intelligence platform that:

1. Analyzes a new RFP, AMI, terms of reference, or commercial need.
2. Extracts structured requirements and proposes visible, editable filters.
3. Retrieves candidate references using exact and semantic search.
4. Reranks candidates using detailed query–reference relevance.
5. Explains recommendations using evidence from original files and pages.
6. Identifies requirements for which no reliable evidence exists.
7. Populates an approved Devoteam reference template without inventing facts.
8. Records data, model, prompt, filter, and evidence versions for auditability.

This is an applied AI and enterprise search project with Document AI, information retrieval, RAG, MLOps, and LLMOps components.

---

## 2. Business objective

Reduce the time and risk involved in finding and preparing Devoteam references for commercial opportunities while increasing relevance, consistency, reuse, and evidence traceability.

### Intended business benefits

- Reduce manual reference-discovery time from hours to minutes.
- Reduce the risk of missing relevant past missions.
- Make reference selection consistent across consultants and bid teams.
- Provide defensible evidence for every factual recommendation.
- Accelerate completion of official reference templates.
- Expose missing documents, weak evidence, and portfolio-coverage gaps.
- Preserve institutional knowledge when employees or folder structures change.

---

## 3. Primary user journey

1. The user uploads or pastes a new opportunity.
2. The system extracts requirements and classifies them as mandatory, preferred, or contextual.
3. The user reviews and corrects the proposed interpretation and filters.
4. Security and confidentiality rules remove unauthorized content.
5. BM25 and multilingual semantic retrieval find candidate passages.
6. Candidate passages are aggregated into candidate references.
7. A cross-encoder reranks the strongest references.
8. Business rules apply evidence quality, metadata fit, recency, and diversity.
9. The system maps source evidence to opportunity requirements.
10. The user receives ranked references, explanations, warnings, files, and page numbers.
11. The user shortlists approved references.
12. The system populates the official reference template from validated evidence.
13. A human reviewer approves the document before external use.

---

## 4. Confirmed project facts

- The known master corpus contains 179 non-empty reference rows.
- The previously audited evidence corpus contained 134 accessible documents and 408 extracted pages.
- The corpus is multilingual, principally French, with English and Arabic content.
- A large proportion of evidence documents are scanned and require OCR.
- Some references have missing, inaccessible, or unlinked evidence.
- Existing client, country, and other metadata contain inconsistent variants.
- The project will run initially from Google Colab with user-authorized Drive access.
- The original source must never be modified, renamed, moved, or deleted by the pipeline.
- Sensitive fields and prohibited folders must not be ingested into searchable datasets.
- A future Devoteam reference template will be provided and analyzed separately.

### Verified Drive boundary

- Shared project root: `Devoteam internship`.
- `PC onssa Draoui` is treated as the source shortcut and remains read-only.
- `Devoteam_AI_CLEAN_PIPELINE` is the intended clean processing workspace.
- `Devoteam_AI_Project test1` is considered previous work and must be archived rather than used as the new production baseline.

---

## 5. Scope

### In scope

- Read-only Drive inventory and immutable source snapshots.
- Reference metadata cleaning and canonical IDs.
- Controlled taxonomies for clients, countries, sectors, offerings, and technologies.
- Reference-to-document linking with human review for uncertain matches.
- PDF, image, DOCX, and PPTX text extraction.
- OCR quality measurement and escalation queues.
- Page- and chunk-level provenance.
- BM25 lexical retrieval.
- Multilingual embedding retrieval.
- Hybrid fusion and cross-encoder reranking.
- Hard filters, soft preferences, and exclusions.
- Structured RFP requirement extraction.
- Evidence-backed RAG explanations.
- Requirement-coverage and gap analysis.
- Shortlisting and comparison.
- Validated reference-template generation.
- Expert relevance evaluation.
- Application, API, security design, monitoring, and operational documentation.

### Out of scope for the initial pilot

- Autonomous multi-agent decision-making.
- Training a foundation LLM from scratch.
- Automatically publishing generated content without human approval.
- Automatically accepting fuzzy document or client matches.
- Indexing CVs, personal documents, financial data, or prohibited administrative material.
- Modifying or reorganizing the original Drive source.
- Knowledge graphs, GraphRAG, Kubernetes, or model fine-tuning unless later evidence justifies them.

---

## 6. Architecture principles

1. **Source protection:** Original Drive files are always read-only.
2. **Traceability by design:** Every searchable passage retains reference, document, page, and extraction provenance.
3. **Deterministic before generative:** Filtering, authorization, scoring, validation, and template rendering remain controlled code.
4. **LLM as assistant, not source of truth:** The LLM interprets and explains evidence but may not create unsupported facts.
5. **Hybrid retrieval:** Exact terms and semantic meaning are both required.
6. **Human control:** Users confirm interpreted requirements, uncertain links, and final templates.
7. **Provider independence:** LLM, embedding, reranker, and search providers must be replaceable.
8. **Configuration over hardcoding:** Taxonomies, filters, weights, thresholds, and model choices are versioned configuration.
9. **Evaluation before promotion:** Optional methods enter the release only after controlled comparison.
10. **Search index is rebuildable:** Canonical data and original evidence remain the authoritative sources.
11. **Notebooks demonstrate; modules operate:** Production logic lives in tested Python modules and services.
12. **Fail safely:** Missing or uncertain information is labeled, never guessed.

---

## 7. Initial information model

The canonical data layer will contain at least:

- `references`
- `clients`
- `client_aliases`
- `countries`
- `sectors`
- `offerings`
- `technologies`
- `documents`
- `reference_document_links`
- `pages`
- `chunks`
- `opportunities`
- `requirements`
- `search_runs`
- `recommendations`
- `evidence`
- `feedback`
- `template_runs`
- `pipeline_runs`

Every primary entity receives a permanent ID. Every derived record stores the pipeline, data, model, taxonomy, prompt, and configuration versions that produced it.

---

## 8. Filter policy

### Security filters — mandatory and invisible to ranking

- User authorization.
- Document access level.
- Reference confidentiality.
- Prohibited source categories.
- External-use permission.

These can never be disabled by an LLM or user query.

### Hard eligibility filters

- Explicit mandatory sector.
- Explicit mandatory country or region.
- Required offering or experience.
- Required technology or certification.
- Mandatory date range.
- Required evidence or attestation.
- Explicit exclusions.

### Soft ranking preferences

- Similar sector or client type.
- Same country or region.
- Similar offering and deliverables.
- Recency.
- Evidence completeness and quality.
- Approved business priority.

The system must display all business filters and allow the user to correct LLM-proposed interpretations. Target context must not automatically become a hard filter.

---

## 9. Model policy

### Initial model strategy

- Use pretrained multilingual embedding models.
- Use pretrained cross-encoder rerankers.
- Use a pretrained instruction-tuned LLM with structured output.
- Use RAG to supply Devoteam evidence at runtime.
- Do not train a foundation model from scratch.
- Do not fine-tune before enough validated examples exist.

### Model-selection method

At least two approved candidates will be tested for each material model role when feasible. Selection criteria include:

- Retrieval or extraction quality.
- French, English, and Arabic performance.
- Evidence faithfulness.
- Hallucination rate.
- Latency.
- Infrastructure requirements.
- Cost.
- Security and confidentiality compliance.

### External LLM condition

No confidential content may be sent to an external model until Devoteam approves the provider, data-processing terms, retention policy, and prompt-content policy. If approval is not available, the system must support a self-hosted model or redacted evaluation data.

---

## 10. Data and security rules

- Never modify the source Drive.
- Never place generated outputs inside the source folder.
- Never ingest prohibited columns merely to redact them later.
- Never log secrets, credentials, complete confidential prompts, or sensitive document text.
- Preserve original filenames and Drive IDs in provenance records.
- Use file hashes for change and duplicate detection.
- Apply least-privilege access.
- Enforce authorization before retrieval and generation.
- Require human approval before external template export.
- Record access, search, generation, and approval events.
- Define retention and deletion procedures before production deployment.

---

## 11. Quality and acceptance targets

The following are initial targets to approve or revise after the gold-set design:

| Area | Initial target |
|---|---:|
| Recall@10 | at least 0.85 |
| Precision@5 | at least 0.75 |
| nDCG@10 | at least 0.75 |
| MRR | at least 0.75 |
| Deterministic filter correctness | 100% |
| Evidence traceability | 100% |
| Citation correctness | at least 98% |
| Unsupported generated claims | below 2% |
| Deterministic template-field correctness | at least 99% |
| Search latency, production target | below 3 seconds at P95 |
| Full analysis, production target | below 20 seconds at P95 |

Metrics must be calculated on a frozen, expert-labeled test set. No model-quality claim may be made from hand-selected examples alone.

---

## 12. Evaluation policy

- Build a representative gold set of approximately 50–100 real or realistic opportunities.
- Use two Devoteam expert labelers where possible.
- Rate references as irrelevant, partially relevant, or highly relevant.
- Include multilingual, acronym-heavy, sparse, and ambiguous queries.
- Compare BM25, dense, hybrid, hybrid plus reranking, and approved advanced options.
- Record both average metrics and failure categories.
- Keep test queries separate from any later fine-tuning data.
- Measure business impact during the pilot: time saved, acceptance rate, replacements, corrections, and user satisfaction.

---

## 13. Deliverables

- Approved project charter and technical specification.
- Filter catalogue and taxonomy policy.
- Immutable snapshot and manifests.
- Canonical datasets and validation reports.
- Reusable Python package with tests.
- Reproducible research notebooks.
- BM25, vector, hybrid, and reranking modules.
- Expert gold set and evaluation report.
- RFP analyzer and structured requirement schema.
- Evidence-backed recommendation engine.
- Template mapping, validation, and rendering engine.
- User application and API.
- MLOps/LLMOps configuration and monitoring.
- Security, deployment, maintenance, and user documentation.
- Pilot and final acceptance report.

---

## 14. Proposed roles

| Role | Responsibility | Status |
|---|---|---|
| Business sponsor / supervisor | Approves business value, scope, adoption, and major releases | Role model approved; name to confirm |
| Product owner / bid manager | Owns user workflow, filters, and business acceptance | Role model approved; name to confirm |
| Data steward / Devoteam data owner | Owns reference quality, aliases, missing documents, and refreshes | Role model approved; name to confirm |
| Technical project implementer / AI-IR engineer | Builds retrieval, reranking, RAG, evaluation, and documentation under supervision | Role model approved |
| Software engineer | Builds API, application, tests, and deployment | Later phase |
| IT/security reviewer | Approves data processing, LLM policy, and access model | Role model approved; name to confirm |
| Two business/domain labelers | Create and adjudicate relevance labels | Role model approved; names to confirm |
| Template approver | Approves template field mapping and final output | To assign |
| Five to eight pilot users | Pilot the system and provide feedback | Population approved; users to identify |

One person may initially hold several roles, but ownership must be explicit before the pilot.

---

## 15. Initial risks

| Risk | Current response |
|---|---|
| Missing evidence documents | Keep references searchable, warn users, create repair queue |
| Weak OCR | Quality routing, retry, escalation, human review |
| Incorrect fuzzy links | Proposal-only matching with human approval |
| Inconsistent metadata | Versioned taxonomies and alias tables |
| LLM hallucination | Retrieval grounding, schemas, citation validation, human approval |
| Confidential-data exposure | Authorization before retrieval, provider approval, minimal prompts |
| No expert labels | Begin gold-set work early and run baseline comparisons |
| Notebook-only implementation | Reusable modules, API, tests, deployment structure |
| Model/provider lock-in | Provider adapters and versioned interfaces |
| One-person operational dependency | Documentation, ownership, scheduled refresh procedure |
| Optional-feature overengineering | Ablation testing and release gates |

---

## 16. Approved Phase 0 direction

The following direction was approved on 14 July 2026:

1. **Primary users:** Bid managers, consultants, and commercial proposal teams in Tunisia / North and West Africa, with later group expansion.
2. **Delivery level:** Enterprise pilot, not an internship-only demonstration.
3. **Initial environment:** Google Colab for controlled research plus a deployable application architecture; production remains independent of Colab.
4. **Production direction:** FastAPI, PostgreSQL, OpenSearch, and a web frontend.
5. **Model policy:** Pretrained models with RAG; no initial fine-tuning.
6. **LLM deployment:** Provider-neutral and security-gated; confidential data is not sent to an external model without Devoteam approval.
7. **Languages:** French first, with English and Arabic support.
8. **Approval:** Human approval required before a reference template is used externally.
9. **Evaluation:** Recall@10 is the primary retrieval metric, supported by Precision@5, MRR, and nDCG@10.
10. **Old workspace:** Archive and freeze it; do not use it as the clean baseline.

---

## 17. Confirmed decisions and remaining governance actions

### Decision A — Target deployment: confirmed A1

- **A1 — Enterprise pilot:** Build a Colab research environment plus a deployable API/application architecture. **Confirmed 14 July 2026.**
- **A2 — Internship demonstration only:** Deliver notebooks and a temporary demo, without production hardening.
- **A3 — Immediate internal production:** Requires Devoteam infrastructure, SSO, security, operations, and support commitments now.

### Decision B — LLM confidentiality policy: confirmed B1

- **B1 — Provider-neutral, security-gated:** Develop with synthetic/redacted content until Devoteam approves an external or internal model. **Confirmed 14 July 2026.**
- **B2 — External enterprise API permitted:** Requires formal confirmation of provider and data-handling conditions.
- **B3 — Self-hosted only:** Requires an approved internal GPU/model-serving environment.

### Decision C — Initial user population: confirmed C1

- **C1 — Bid managers and consultants in Tunisia/North-West Africa. Confirmed 14 July 2026.**
- **C2 — Tunisia entity only.**
- **C3 — Group-wide from the first pilot.**

### Remaining governance actions

- Named sponsor, product owner, data steward, security reviewer, and expert labelers.
- Production hosting platform and identity provider.
- Approval of filter catalogue G1.
- Template format and approval rules.

### Decision D — Confidentiality classification: confirmed D1

| Level | Meaning | Search behavior | External LLM behavior | Template behavior |
|---|---|---|---|---|
| `PUBLIC` | Approved for external disclosure | Searchable by authorized users | May be used only with an approved provider | May be exported after normal review |
| `INTERNAL` | Ordinary internal business information | Searchable internally | Redacted or blocked until provider approval | Requires human approval before external use |
| `RESTRICTED` | Sensitive client, contractual, or operational information | Limited to authorized roles | Must not be sent externally | Values masked unless specifically approved |
| `CONFIDENTIAL` | Highest sensitivity or explicit legal restriction | Strict need-to-know access | Never sent to an external model | Not exported; only a protected internal placeholder |

**D1 was confirmed on 14 July 2026.** Default classification for unreviewed references and documents is `INTERNAL`. Security rules may raise the level automatically, but only an authorized reviewer may lower it.

### Decision E — Governance roles: confirmed E1

The responsibility model in Section 14 is approved. Named individuals may be assigned during supervisor coordination, but the responsibilities must not be removed or silently combined without recording the decision.

### Decision F — Pilot and acceptance design: confirmed F1

- Pilot population: five to eight users.
- Pilot duration: approximately four weeks.
- Expert relevance labelers: two.
- Evaluation opportunity set: 50 representative opportunities or queries.
- Primary retrieval target: Recall@10 at least 0.85.
- Deterministic filter correctness: 100%.
- Citation correctness: at least 98%.
- Business-efficiency target: at least 60% reduction in reference-discovery time.
- All targets require a documented measurement method and may be revised only through an approved evaluation decision.

### Decision G — Filter catalogue: confirmed G1

G1 was confirmed on 14 July 2026. The following catalogue is the approved version-1 baseline. Additions or behavioral changes must be versioned and evaluated.

#### Automatic security filters

- User and role authorization.
- Reference confidentiality level.
- Document access level.
- External-use authorization.
- Prohibited source category.

#### Immediately supported business filters

- Country.
- Region.
- Sector.
- Offering / mission type.
- Business unit.
- Project year or year range.
- Client.
- Evidence-document availability.
- Document type.
- Data-quality status.

#### Supported after validated extraction or taxonomy enrichment

- Technology or platform.
- Deliverable type.
- Certification or mandatory qualification.
- Client type.
- Project status or approved outcome, if a trustworthy source exists.
- Attestation availability and strength.
- Evidence-language preference.

#### Exclusions

- Exclude named clients.
- Exclude countries, regions, sectors, or offerings.
- Exclude references before or after a selected year.
- Exclude references without supporting evidence.
- Exclude low-quality or unvalidated records.

#### Filter behavior

- Every business filter is visible and editable.
- The LLM may propose filters but cannot silently enforce them.
- Requirements are classified as `MUST`, `SHOULD`, `PREFERRED`, or `CONTEXT`.
- Security filters run before retrieval and cannot be disabled.
- Hard filters exclude candidates; soft preferences modify ranking.
- Result counts and active-filter chips are shown in the application.
- Project value and sensitive team/personnel data are not search filters and are not ingested.

---

## 18. Phase 0 completion gate

Phase 0 is complete only when:

- The project objective and scope are approved.
- Decisions A, B, and C are confirmed.
- Source and output boundaries are approved.
- Initial security and confidentiality rules are approved.
- Success metrics are accepted or revised.
- Business, data, security, and evaluation owners are named or assigned as pending actions.
- The reference template has an identified owner and delivery plan, or is recorded as a non-blocking dependency before template-engine work.
- The clean workspace is approved as the only new processing baseline.

### Current gate status

| Gate | Status |
|---|---|
| Objective and scope | Approved through A1 |
| Primary user population | Approved through C1 |
| Source and output boundaries | Approved |
| LLM security direction | Approved through B1 |
| Initial success metrics | Approved for the pilot through F1; measurement details pending gold-set design |
| Confidentiality classification | Approved through D1 |
| Governance responsibility model | Approved through E1; names pending supervisor coordination |
| Pilot design | Approved through F1 |
| Filter catalogue | Approved through G1 |
| Production hosting and identity provider | Deferred to production design; not blocking the enterprise pilot baseline |
| Template owner and delivery | Tracked dependency pending template provision; not blocking retrieval development |
| Clean workspace baseline | Approved by project direction |

This gate passed on 14 July 2026. New work must follow this approved baseline and the recorded change process.

---

## 19. Decision log

| Date | Decision | Status | Rationale |
|---|---|---|---|
| 14 Jul 2026 | Restart with a clean, senior-level architecture | Confirmed | Previous work became fragmented and difficult to defend |
| 14 Jul 2026 | Preserve original Drive as read-only source | Confirmed | Protect source truth and auditability |
| 14 Jul 2026 | Use hybrid retrieval, reranking, filters, evidence, and RAG | Confirmed design direction | Exact and semantic retrieval solve complementary problems |
| 14 Jul 2026 | Use pretrained models rather than train an LLM from scratch | Confirmed design direction | Cost, data, time, and quality considerations |
| 14 Jul 2026 | Make the platform adoptable by Devoteam | Confirmed objective | The deliverable must extend beyond internship notebooks |
| 14 Jul 2026 | Analyze and integrate the official template later | Pending template | Template has not yet been provided |
| 14 Jul 2026 | Select A1 enterprise-pilot delivery level | Confirmed | Build for Devoteam adoption while retaining a controlled research environment |
| 14 Jul 2026 | Select B1 provider-neutral, security-gated LLM policy | Confirmed | Prevent unapproved external processing and provider lock-in |
| 14 Jul 2026 | Select C1 Tunisia/North-West Africa initial users | Confirmed | Keep the pilot manageable while supporting later expansion |
| 14 Jul 2026 | Select D1 four-level confidentiality classification | Confirmed | Separate ordinary internal material from restricted and strictly confidential information; default unreviewed content to INTERNAL |
| 14 Jul 2026 | Select E1 governance responsibility model | Confirmed | Make business, data, technical, security, evaluation, and pilot responsibilities explicit |
| 14 Jul 2026 | Select F1 pilot and acceptance design | Confirmed | Evaluate technical quality and measurable business impact with a controlled user pilot |
| 14 Jul 2026 | Select G1 filter catalogue | Confirmed | Separate security, hard, soft, enriched, and exclusion filters with visible user control |

---

## 20. Phase 0 approval result

Phase 0 is approved with decisions `A1`, `B1`, `C1`, `D1`, `E1`, `F1`, and `G1`.

### Approved baseline

- Enterprise-pilot delivery level.
- Provider-neutral and security-gated LLM policy.
- Tunisia / North and West Africa initial user population.
- Four-level confidentiality model with `INTERNAL` as the unreviewed default.
- Explicit business, data, technical, security, evaluation, and pilot responsibilities.
- Five-to-eight-user, approximately four-week pilot with two expert labelers and 50 evaluation opportunities.
- Version-1 security, business, enrichment, and exclusion filter catalogue.

### Tracked non-blocking actions

- Add the names of the sponsor, product owner, data steward, security reviewer, labelers, and template approver.
- Confirm the production hosting platform and identity provider before production deployment.
- Receive and analyze the official reference template before template-engine implementation.
- Finalize metric measurement details while building the expert gold set.

The next authorized stage is **Phase 1 — Clean Project Foundation**. No source data will be modified during that phase.
