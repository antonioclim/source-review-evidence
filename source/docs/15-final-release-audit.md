# Distribution validation record

The current machine-readable result is [validation/RP2_VALIDATION.json](../../validation/RP2_VALIDATION.json). It records the scope, environment and outcomes actually obtained for this distribution. The component-facing [summary](../release/final-audit-summary.md) and [JSON view](../release/final-audit-report.json) refer to that record.

## Assessment boundaries

| Boundary | Evidence required |
|---|---|
| Package integrity | Exact member inventory, sizes and hashes |
| Documentary consistency | Current identity, links, scope and file selection |
| Isolated implementation behaviour | Executed checks with inputs, environment and outcomes |
| Strict historical reproduction | Original candidate, locked prerequisites and actual historical route execution |
| Native browser qualification | Actual browser/runtime execution under the stated environment |
| Publication | Observed repository/release or deposit record |

A passing result in one row is not a substitute for another. The retained A17 outcome remains `NOT_MET`; Q07 remains `NOT_QUALIFIED_NOT_WAIVED`. Packaging and documentary corrections preserve their meanings.

Historical audit files, test code and coverage policies retain their producing context. They do not constitute a fresh PASS for the selected distribution. See [the reproducibility guide](../../docs/REPRODUCIBILITY.md) for the retained technical checks and strict-route requirements.
