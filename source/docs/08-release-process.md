# Preparing a distribution release

[Distribution overview](../../README.md) · [Integrity](09-release-integrity.md) · [Repository controls](16-ci-and-repository-controls.md)

## Release unit

Source Review Evidence uses a complete archive containing the implementation and selected retained evidence. Its version is **1.0.0**. A GitHub browsing tree may contain a smaller declared selection; the complete archive identifies the software–evidence association.

## Preparation checks

The current manifest identifies every distributed file by path, size and SHA-256. The distribution verifier checks that boundary. The validation record identifies the actual environment, executed checks and unexecuted routes. Review the [change record](../../provenance/DISTRIBUTION_CHANGES.json) and [component-rights guide](../../docs/COMPONENT_RIGHTS.md) before final packaging.

Historical source inventories and scientific locks remain attached to their original objects. They are not regenerated to admit editorial changes or to convert a retained failure into a pass.

## Browser publication route

The author will create a separate GitHub repository and a new Zenodo record. The intended GitHub tag is `v1.0.0`; the distribution and Zenodo version are `1.0.0`. The same complete archive will be attached to both records. The final upload guide will identify the exact browser batches, archive names, checksums and fields.

Manual Zenodo deposition is the selected route. Automatic GitHub–Zenodo release archiving is not part of this preparation. A repository URL, DOI, publication date or signature is recorded only when the corresponding object exists.

## Retained maintenance utilities

The component's `tools/check_release.py`, `tools/build_release.py` and recovery utilities retain the earlier component protocol. They remain available for inspection and isolated regression checks. Their historical manifests and CI expectations do not define the new distribution's release boundary. Use the current distribution verifier and validation record for this package.
