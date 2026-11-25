# Reproducibility

[Overview](../README.md) · [Evidence and scope](EVIDENCE_AND_SCOPE.md) · [Provenance](PROVENANCE.md)

## Three distinct verification scopes

| Scope | Required input | What a passing result establishes |
|---|---|---|
| Distribution integrity | This distribution and its current manifest | The checked paths, sizes and digests agree with the manifest |
| Isolated implementation checks | The declared helper code, fixtures and recorded test environment | The specific exercised expectations hold for that run |
| Strict historical reproduction | The exact historical candidate and its admitted environment | The locked route has executed under its stated input and runtime conditions |

These scopes have different prerequisites. Retained outputs can be inspected without executing a historical runner. A new run must have its own input identities, environment record and output location.

## Current software and retained results

The technical derivative is **CP-FGCS-C2F2-FIX2**. It changes `common.py`, `arms.py` and `oracle_run.py` in the experimental helper code. The production-analysis code and the retained study outcomes remain identifiable separately through their source hashes.

The stored technical audit records 58 passing expectations before the parser-boundary correction and 67 afterwards, using the same set of 67 expectations. The exercised material comprised 12 explicit sources, two admission-boundary probes and one prepared consumer case. That audit used CPython 3.12.14. The technical audit did not rerun the paired study or finite oracle.

Version 1.0.0 reorganises material for a new distribution. Its current manifest governs this package. Historical manifests continue to identify their historical inputs; document conversion or file selection does not rewrite those identities.

## Strict historical route

The original P7D route binds CPython 3.13.5, recorded interpreter and platform identities and 145 installed dependency-file identities. Its frozen source inventory also includes documentation. It therefore cannot admit a newly curated distribution solely because its executable components have been retained.

The exact original candidate remains a separate archival object. The new distribution must use its own integrity checks and record the scope of any new functional verification. Historical runner refusals are retained as refusals rather than bypassed by editing stored locks, runtime strings or expected hashes.

## Clean-environment qualification

**Q07 remains `NOT_QUALIFIED_NOT_WAIVED`.** The historical clean-environment criterion requires a documented fresh host or container and the prescribed setup scope. It specifies a smoke route within 300 seconds and a quick start within 1,800 seconds. Timings from an existing host do not establish that qualification.

The associated **A17 outcome remains `NOT_MET`**. It is an outcome of the retained study, not a packaging fault that a new version number resolves.

## Before an execution

Identify the component version and exact input set, inspect the stated prerequisites and use a separate output destination. Preserve failed admissions and unexpected outputs with the run record. The release validation record should name the environment and tests that were actually executed; an unexecuted route has no passing result to report.

## Current distribution checks

The distribution-root [verifier](../tools/verify_distribution.py) checks the
exact GitHub browsing inventory in
[DISTRIBUTION_MANIFEST.json](../DISTRIBUTION_MANIFEST.json). The
[view validation](../validation/GITHUB_VIEW_VALIDATION.json) records the
targeted documentation checks and actual test discovery for this view.
[RP2_VALIDATION.json](../validation/RP2_VALIDATION.json) retains the earlier
component execution results; carrying that receipt forward does not claim a
new full regression run.

The complete archive `source-review-evidence-1.0.0.zip` provides the retained
evidence. [GITHUB_VIEW.json](../GITHUB_VIEW.json) binds its identity and points
to its preserved manifest. Use the complete archive for evidence paths
described in the [data guide](DATA.md). Neither integrity verification nor
test discovery executes A17, A18 or the strict historical pipeline.

The selected component retains old release and coverage utilities for
inspection. Some require excluded documentation, prior workflow files or an
earlier manifest schema. Their original gate is not silently substituted for
the new distribution's verifier, and its prerequisites are not edited to
manufacture an historical PASS.

