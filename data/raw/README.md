# Raw Source Data

This directory is the documented local landing area for authorized source documents when a controlled run does not use the immutable snapshot layout directly.

Raw Devoteam and client documents are confidential inputs. They are intentionally excluded from Git and must not be copied into a commit, issue, release, or generated demo bundle. Keep the original files in an approved access-controlled store and preserve their checksums and source identifiers.

The signed production snapshot used by the current pipeline remains local under:

```text
data/snapshots/<snapshot_id>/raw/
```

To reproduce ingestion, configure the authorized source in `.env`, run the read-only inventory stage, and let the pipeline write a new immutable snapshot. Do not rename source files or edit integrity manifests merely to make validation pass.

Only this policy file is intended for Git. Placeholders, synthetic fixtures, or redistributable samples must go in a separately documented fixture directory and must contain no client information.
