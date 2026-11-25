# Source and evidence lineage

Source Review Evidence 1.0.0 is a separate distribution of the source-review implementation, retained computational evidence and documented technical corrections. Its release number identifies this distribution. Component versions and schema identifiers in retained code and records identify the components that produced or consumed those records.

## Retained implementation

The analysis code, schemas, browser assets and numerical policy are retained from the documented working baseline. The cumulative technical derivative is `CP-FGCS-C2F2-FIX2`. Its existing corrections concern three research scripts:

- `experiments/p7c/code/common.py`;
- `experiments/p7c/code/arms.py`;
- `experiments/p7c/code/oracle_run.py`.

The distribution manifest records the actual selected files and their hashes. A packaging revision does not change the interpretation of an older execution record or qualify an untested environment.

## Frozen records and documentary projections

Computational inputs, outputs and unfavourable results retain their recorded values. Historical status documents that are presented as editorial projections are identified separately, with their source hashes and the exact scope of the transformation. They are not labelled immutable raw records.

The historical OR2 and technical-derivative archives remain preservation baselines. They are not prerequisites that a reader must obtain to inspect the selected source and evidence in this distribution.

## Verification scope

Distribution integrity, bounded software checks, strict historical reproduction and native deployment are separate verification tasks. The recorded A17 outcome remains `NOT_MET`. Q07 remains `NOT_QUALIFIED_NOT_WAIVED`.

The historical P7D route checks the complete source inventory and its frozen context. Its locks must not be regenerated merely to admit a new documentation layout. Current distribution checks have their own manifest and stated scope.

## Attribution and rights

Antonio Clim is the named author and maintainer in the retained source notices. Existing copyright and licence notices keep their documented scope. External runtimes and comparators retain their upstream rights. The repository metadata must use the actual new release identifiers once those identifiers exist.

See [the distribution provenance](../../docs/PROVENANCE.md), [the change record](../../provenance/DISTRIBUTION_CHANGES.json) and [component rights](../../docs/COMPONENT_RIGHTS.md).
