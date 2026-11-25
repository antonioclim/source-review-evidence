# Hash and identity records

| Object | Identity record |
|---|---|
| Current distribution files | [DISTRIBUTION_MANIFEST.json](../../DISTRIBUTION_MANIFEST.json) |
| Source and documentary changes | [DISTRIBUTION_CHANGES.json](../../provenance/DISTRIBUTION_CHANGES.json) |
| Current validation | [RP2_VALIDATION.json](../../validation/RP2_VALIDATION.json) |
| Component metadata view | [release-manifest.json](../release/release-manifest.json) |
| Original candidate identity | [Distribution provenance](../../docs/PROVENANCE.md) |

The final archive digest is computed from the packaged archive and supplied beside it in the final delivery. It is not embedded as a purported digest of itself. GitHub-generated source archives and the complete distribution archive may contain different file selections; each must be identified by its own exact bytes.

Checksums establish correspondence to the supplied identity record. Publisher authentication and component rights have separate evidence requirements.
