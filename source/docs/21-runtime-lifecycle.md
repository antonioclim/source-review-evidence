# Runtime lifecycle and maintenance policy

## Retained inventory and dated observation

The packaged configuration remains pinned to **Pyodide 0.25.0**, with the five exact core-startup artefacts in `app/pyodide-provenance.json`. The current distribution preserves the pinned runtime configuration and its measured binary identities. The inventory authenticates selected bytes; it is not an SBOM for every optional package, a vulnerability scan or a proof of upstream build reproducibility.

The retained component review records an upstream observation dated **6 September 2026**: release **314.0.6**, reported as published on 25 August 2026, at https://github.com/pyodide/pyodide/releases/tag/314.0.6. These details are preserved as the earlier review's dated record; they were not reverified during RP2 and do not establish the current upstream release or advisory status. They also do not demonstrate a vulnerability in the retained runtime or compatibility of a direct upgrade. The distribution identifies Pyodide 0.25.0 as its frozen configured dependency, without asserting current upstream support or deployment approval.

## Review responsibilities

The maintainer should review upstream releases, security advisories and Python/WebAssembly/browser compatibility monthly and before any institutional deployment or published release. A reported vulnerability, failed integrity check or changed upstream startup behaviour triggers an additional review. This is a maintenance policy; no scheduler, background monitoring, notification service or guaranteed response time is claimed.

Record the review date, exact upstream versions and advisory identifiers, affected artefacts, evidence, applicability decision and upgrade/mitigation disposition. An empty search result must be labelled as a bounded search, not as proof of absence of vulnerabilities. Do not publish confidential student samples as reproducers. Routing is described in `SECURITY.md`.

## Upgrade acceptance

An upgrade is a separate reviewed source change. Identify the intended release and complete startup set from primary upstream metadata; fetch each artefact with bounded reads and no silent redirects; record actual sizes and digests; inspect licence/provenance and optional-package boundaries. Reconcile runtime Python/API changes, the bootstrap fetch contract, worker execution and the report schema.

Re-run the full native matrix, executable-line coverage at existing floors, Chromium functional and accessibility gates, source/worker/core/engine tamper checks, cancellation/deadline recovery and release reproducibility. Update configuration, embedded records, browser SRI, tests, documentation and source manifest coherently. Record the actual local or authorised CI results for the resulting exact tree; the presence of a harness alone supplies no passing result. Never update a URL without its authenticated inventory or turn off an integrity check to permit an upgrade.

Rollback means selecting the previous verified source/configuration/runtime set as a unit, after assessing the reason for rollback. It is not permission to use a known unsafe version indefinitely. A newer release tag, passing hashes and passing software tests do not alone authorise deployment, licensing changes or claims about authorship detection.
