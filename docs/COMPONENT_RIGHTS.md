# Component rights

[Overview](../README.md) · [Licence scope](../LICENSE) · [Per-file scope](../LICENSING_MAP.json)

The distribution uses MIT for author-controlled code and CC BY 4.0 for
author-controlled documentation, included figures and research records.
Existing grants, notices and third-party terms remain effective.

## Allocation

| Material | Applicable terms | Scope |
|---|---|---|
| Explicit source scope identified by the retained notice | Existing MIT | Includes the three associated Markdown documents within that explicit scope. |
| Other own source, integration helpers, tests and functional configuration | MIT | Includes new verification helpers and historical own-code snapshots. |
| Own code embedded in records | MIT | Source/input strings and mutation expressions retain their code terms. |
| Own documentation and included own figures | CC BY 4.0 | Existing MIT permissions remain available wherever already applicable. |
| Own constructed inputs, records, results and collection/database rights | CC BY 4.0 | Applies to rights the author may grant, without asserting exclusive copyright in bare facts. |
| SPDX documents declaring `dataLicense: CC0-1.0` | Existing CC0-1.0 | The metadata documents only, not the described software or evidence collection. |
| Existing licence and notice files | Their original terms | Preserved verbatim, including the original CodeProbe contributors attribution. |
| Third-party material | Its own terms | Outside any new grant by the author. |

The per-file scope map identifies the component allocation. The distribution
manifest records current file identities. Frozen computational records and
historical source snapshots retain their bytes; rights are documented in
sidecars rather than through new headers in the evidence.

## Mixed records

Some JSON and JSONL files contain authored source/input strings and mutation
expressions. Their code portions retain MIT terms while the surrounding own
records and collection rights use CC BY 4.0. The same distinction applies
to code quoted in Markdown, logs and patches. Third-party extracts and
original notices retain their original terms, whether or not an individual
fragment has a pointer in the scope map. No file extension alone changes
the provenance or licence of an embedded component.

## Preserved scope

The source notice identifies MIT coverage in the component's `src/`,
`tools/`, `schemas/`, `research/`, `tests/` and `app/s05/` directories.
The source MIT notice and its historical copy preserve their original
wording. No distribution term withdraws an existing MIT permission for
associated software documentation or other covered material.

External runtimes and comparator implementations are outside the selected
payload. Their identifiers and version records describe prerequisites;
they do not redistribute those implementations. Any addition of external
software must retain its own terms and notices.

The manuscript, OR1, original OR2 archive and publisher materials are outside
this distribution licence. References to them preserve provenance and do
not authorise their public redistribution.

## Official terms

- [MIT](https://spdx.org/licenses/MIT.html)
- [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en)
- [SPDX metadata data licence, §6.2](https://spdx.github.io/spdx-spec/v2.3.1/document-creation-information/#62-data-license-field)
