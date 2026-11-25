# Data

[Overview](../README.md) · [Evidence and scope](EVIDENCE_AND_SCOPE.md) · [Provenance](PROVENANCE.md)

## Availability in the GitHub view

The evidence paths described below belong to the complete release archive
`source-review-evidence-1.0.0.zip`. This browsing tree retains the software and
reader guides; the 8,067 frozen-evidence and documentary-projection files are
carried by that archive. [GITHUB_VIEW.json](../GITHUB_VIEW.json) records its
exact identity, and the [complete manifest](../provenance/COMPLETE_ARCHIVE_MANIFEST.json)
lists its files. The root manifest has the narrower scope of this browsing tree.

## Collection

The evidence collection contains constructed source inputs, carrier records, declared profiles, expected values and retained execution outputs. Its purpose is to make the relationships between inputs, executed predicates and recorded outcomes inspectable.

The new distribution selects material from the frozen computational candidate **P7-R4-review-candidate+a2p7d.1**. The current inventory records the selected files and their identities. Editorial tracking material is handled separately from computational evidence. Original archival bytes remain preserved locally.

## Evidence families

The complete archive keeps the original relative paths for these logical families. The release inventory records which files are included and the source identity of each one.

| Original path family | Content |
|---|---|
| `experiments/p7c/data/` | Constructed source inputs, pilot carriers, profiles and expected vectors |
| `experiments/p7c/design/` | Retained design and freeze records |
| `experiments/p7c/reference/` | Reference outputs for the paired cases, oracle and associated checks |
| `results/` | Earlier retained computational results |
| `review_evidence/` | Audit and execution records, with their original contexts |

Source strings in an input record are data for analysis. Generated numeric exports retain the role given by their producing record. Scripts stored inside a historical run document that run; the distribution's current software inventory determines the maintained entry points.

## Key reference records

`experiments/p7c/reference/pilot_summary.json` records the paired-study summary. Its `P6_strict_continuation` field remains `NOT_MET`; the three ineligible challenges are retained with their identifiers. Healthy controls and additional-check distinctions are reported in their respective fields.

`experiments/p7c/reference/oracle.json` records the finite oracle's 32 programs, 40 callables and 592 checks. It also records the finite construction grammar and the shared parser dependency of the iterative audit.

These records retain their original numerical values and outcomes. The new distribution does not assign them a new execution date or imply that they were regenerated using the corrected helpers.

## Association with the software

The software derivative **CP-FGCS-C2F2-FIX2** and the frozen outputs have separate identities within the complete distribution. The release inventory and supplied checksums associate the code with the retained evidence. A shared distribution version does not replace the per-file provenance.

Historical absolute paths and environment observations describe the producing host. They are useful evidence about that execution, but they are not installation instructions for a different computer.

## Citation and rights

The initial distribution version is **1.0.0**, prepared for a single new Zenodo record containing the complete software-and-evidence archive. Cite that record's version DOI once it exists, together with the version and exact files used. [Component rights](COMPONENT_RIGHTS.md) distinguishes MIT code portions from CC BY 4.0 rights over the surrounding author-controlled records and collections. Existing third-party terms and SPDX metadata exceptions remain effective.

## Documentary status projections

Four historical status documents are distributed as explicit documentary projections. Each records its original source identity and transformation scope. Two editorial text fields per record are changed; the original predicates, status values, thresholds and numerical values remain semantically unchanged. These projections are distinguished from byte-identical computational records in [complete-archive transformation record](../provenance/COMPLETE_ARCHIVE_CHANGES.json).

The retained `FAIL`, `UNKNOWN`, `WAIVED` and `NOT_MET` outcomes describe the original checks. They do not express approval of this new release, and the projection does not establish a new study execution.
