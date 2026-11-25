# Provenance

[Overview](../README.md) · [Changelog](../CHANGELOG.md) · [Reproducibility](REPRODUCIBILITY.md)

## Identities

| Identity | Role |
|---|---|
| **1.0.0** | Intended initial version of this separate distribution |
| **CP-FGCS-C2F2-FIX2** | Existing cumulative technical derivative |
| **CP-SQJ-P3-FIX1** | Earlier technical derivative in the same local lineage |
| **P7-R4-review-candidate+a2p7d.1** | Frozen computational candidate underlying the retained evidence |

These identifiers refer to different objects. The distribution version identifies a new package boundary. Component identifiers and source hashes preserve the relationship to the earlier implementation and evidence.

The original OR2 archive has SHA-256:

```text
22057522aa1cd6dc2cb1a6a3ad9fd71531881fc5738f830f17258c935fef9a85
```

It remains unchanged in the local archival collection. Its digest records provenance; the new public distribution has its own inventory and digest.

## Changes represented by the distribution

The existing cumulative derivative replaces three experimental-helper files: `experiments/p7c/code/common.py`, `experiments/p7c/code/arms.py` and `experiments/p7c/code/oracle_run.py`. The retained patch identities distinguish these changes from the original candidate. The parser-boundary correction in `common.py` normalises the admitted text consistently and uses the production parser's type-comment mode.

The new distribution replaces inherited release-facing metadata with metadata for version 1.0.0. Readable documentation is prepared in Markdown, while the provenance inventory records which documents were converted, replaced or excluded. Executable code, computational records and documentation are tracked as separate kinds of material.

The inherited name **CodeProbe** remains in software modules, record schemas and source identities where changing it would alter interfaces or obscure provenance. It is not used as the title of this distribution.

## Component rights

The [licence scope](../LICENSE) and [per-file allocation](../LICENSING_MAP.json) distinguish author-controlled code, documentation and research records. Existing copyright, permission and third-party notices retain their terms. The original source MIT notice remains byte-identical. Mixed records preserve the terms applicable to their code and data portions.

No repository address, DOI or publication date is inferred from historical metadata. The prepared archive retains its own identity; the published record supplies the actual public identifiers.

## Current transformation record

[DISTRIBUTION_CHANGES.json](../provenance/DISTRIBUTION_CHANGES.json) records the
selection of this GitHub view and its documentary adaptations. The
[current manifest](../DISTRIBUTION_MANIFEST.json) binds this view's bytes, and
[GITHUB_VIEW_VALIDATION.json](../validation/GITHUB_VIEW_VALIDATION.json) records
its targeted checks. The earlier
[component validation](../validation/RP2_VALIDATION.json) remains a separate
execution receipt.

[GITHUB_VIEW.json](../GITHUB_VIEW.json) identifies the complete release archive
by filename, size and SHA-256. Its preserved
[manifest](../provenance/COMPLETE_ARCHIVE_MANIFEST.json) and
[transformation record](../provenance/COMPLETE_ARCHIVE_CHANGES.json) describe the
complete distribution, including the 8,067 evidence and projection files
omitted from this browsing tree. The archive records are not the current
branch inventory. [Component rights](COMPONENT_RIGHTS.md) explains the scoped
terms; [LICENSING_MAP.json](../LICENSING_MAP.json) lists the files present here.

