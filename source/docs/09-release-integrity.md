# Distribution integrity

[Overview](../../README.md) · [Reproducibility](../../docs/REPRODUCIBILITY.md)

## Current manifest

`DISTRIBUTION_MANIFEST.json` at the distribution root records the admitted paths, byte lengths and SHA-256 digests. `tools/verify_distribution.py` checks that declared boundary and reports its result as JSON. Run it from the extracted distribution root:

```bash
python3 tools/verify_distribution.py
```

The manifest declares any intentional self-exclusion. An archive digest is recorded outside the archive it identifies, avoiding a self-referential digest. A changed byte, missing member or unexpected file must be interpreted according to the verifier's recorded policy; it must not be hidden by updating an expected hash without a documented change.

## What integrity establishes

A passing integrity result binds the checked files to the supplied manifest. It does not identify an authenticated publisher, establish ownership, run a study or qualify a browser environment. The exact output and execution scope are recorded in [the validation record](../../validation/RP2_VALIDATION.json).

## Historical identities

The original OR2, FREEZE2 and earlier component inventories retain their original scope. The selected source tree changes because documents and release metadata have a new distribution boundary. Historical digests remain evidence about their original inputs; they are not rewritten to make this package satisfy a different historical inventory.

Frozen computational records and explicit documentary projections remain separately identified in the [data guide](../../docs/DATA.md) and [change record](../../provenance/DISTRIBUTION_CHANGES.json).
