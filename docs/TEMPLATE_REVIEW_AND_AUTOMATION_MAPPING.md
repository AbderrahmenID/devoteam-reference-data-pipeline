# Reference template review and automation mapping

## Decision

Keep the document's business structure and visual identity. Do **not** edit or
overwrite the supplied `Template Ref.docx`. A separate automation-safe copy will
be created in the document-generation phase after the canonical dataset and
retrieval results are validated.

The supplied document is a populated 41-page reference pack, not an empty
technical template. It contains:

- a two-page landscape summary matrix with 17 references;
- seven thematic capability columns;
- 17 portrait detail cards;
- embedded contract, attestation, and supporting-document images.

## What will remain unchanged

- Devoteam's red/white visual identity and typography;
- the summary-matrix-first structure;
- the detailed reference cards;
- the supporting evidence after each selected reference;
- French as the default generated-document language;
- the seven business themes, subject to taxonomy validation.

## Corrections required in the automation-safe copy

1. Mark the summary header as a repeating Word table header.
2. Prevent reference rows from splitting across pages; reference 9 currently
   continues on page 2 without a repeated header.
3. Remove the accidental blank page 30 and normalize section/page breaks.
4. Standardize labels and spelling, including `Date d’achèvement` and
   `Nom de l’autorité contractante`.
5. Separate `Client / Autorité contractante` from `Bailleur / Financement`.
6. Standardize periods as `date_début`, `date_fin`, and `en_cours`; render
   `Présent` only from the explicit `en_cours` value.
7. Generate country text and flag from one ISO country code rather than storing
   them independently.
8. Add structured placeholders/content controls. The supplied document has none.
9. Add evidence captions with source file, source page, evidence type,
   verification status, and internal provenance ID.
10. Add alt text to generated images and use proper heading/table semantics.
11. Generate a variable number of selected references without manual copying or
    deleting of pages.
12. Apply confidentiality and export-policy checks before any reference is
    included in an external document.

## Canonical field mapping

| Template output | Canonical source field | Rule |
|---|---|---|
| `#` | `display_rank` | Generated after retrieval and human approval |
| Intitulé du projet | `mission_name` | Evidence-supported text only |
| Client | `contracting_authority_name` | Keep separate from funder |
| Bailleur / Financement | `funder_name` | Optional; never merge silently with client |
| Pays | `country_iso2`, `country_display_fr` | Flag derived from ISO code |
| Période | `start_date`, `end_date`, `is_ongoing` | Deterministic formatting |
| Thématiques clés | `service_theme_ids[]` | Controlled multi-label taxonomy |
| Description du projet | `project_description` | Supported summary, with provenance |
| Services réalisés | `services_delivered[]` | Structured bullets, not free-form invention |
| Justificatif | `evidence_items[]` | File ID, page, type, hash, access and review status |

## Generation policy

- Retrieval produces ranked candidate reference IDs.
- A security filter removes disallowed references before generation.
- An LLM may transform **approved structured facts** into concise wording, but it
  may not choose unsupported facts or directly edit the DOCX.
- The LLM must return schema-validated JSON with field-level citations.
- Deterministic Python document code populates the automation-safe template.
- Missing facts render as `Non renseigné` or are omitted according to the field
  policy; they are never guessed.
- The final DOCX/PDF requires a human approval step and a citation audit.

## Phase impact

No Phase 2 redesign is required. Phase 2 records the metadata, hashes, evidence
relationships, exclusions, and access status needed by this mapping. The
automation-safe DOCX should be implemented only after Phase 3 extraction and
Phase 4 canonical-data validation.
