# Contributing to CodeProbe

## Author and maintainer

**Antonio Clim** ([`@antonioclim`](https://github.com/antonioclim)) is the author
and maintainer identified for this project. Contribution proposals, technical
changes and documentation corrections are reviewed through the repository's
issues and pull requests. GitHub's automated committer labels do not identify
the scholarly author of the software.

This guide is a contribution process, not a claim that every past byte has a
single legal origin. Retain applicable copyright notices, the MIT licence and
accurate provenance. Do not manufacture co-authors or erase real contributions.
Accepted contributions should be credited according to their documented scope.

## Scope and scientific restraint

Contributions should improve correctness, robustness, security, usability,
transparent methodology or documentation. CodeProbe is an inspectable formative
static-analysis tool, not a validated disciplinary detector. The current scientific
route is an evidence contract: observation availability, measured values,
interpretation policy, source localisation and consumer admission remain separate.
It is vector-only and non-compensatory. Do not reintroduce a global scalar,
origin classification or screenshot threshold as current scientific guidance.
The retained compatibility score is not an AI-authorship probability. Do not add
a metric merely because it detects clean, well-documented or stylistically
consistent code.

A lower score after a code change is not proof of greater human authorship.
A higher score is not proof of misconduct. Clearly distinguish measured software
behaviour, assumptions, synthetic test fixtures and empirical findings. Claims
about error rates require a specified corpus, reference labels, denominator,
threshold, unit of analysis and uncertainty analysis. Do not recast the author's
legacy-use observation as a published validation study.

## Before implementing a change

Read README.md, SECURITY.md, docs/11-design-decisions.md and the documentation
for the affected boundary. State the problem, expected behaviour and a small
reproducer in an issue or PR. Use formal British English for project material.
Make a focused branch from the current main commit; inspect concurrent changes
before proposing integration. Never force-push over another person's work.

The browser runtime must remain inspectable and standard-library-only on the
Python side. Preserve authenticated runtime/worker/engine loading, bounded input,
terminable analysis and local processing. No remote upload of analysed source,
reports or filenames is introduced merely to simplify a feature. Do not turn
an explicitly unverified manual engine override into an authenticated route.

## Tests and release evidence

Use the distribution-root `tools/verify_distribution.py` for the current inventory. Record targeted checks for any changed behaviour, including the source identity, environment, executed cases and justified skips. A defect regression should fail on the demonstrated old behaviour and pass after the repair.

The component's older release, coverage and reproducibility gates retain their original input and runtime contracts. They are not the release gate for the selected 1.0.0 distribution. Do not edit historical locks, lower a coverage floor or remove a scientific assertion to admit a documentary change. The [current validation record](../validation/RP2_VALIDATION.json) distinguishes performed checks from unexecuted routes.

Changes to browser/runtime bytes require corresponding integrity metadata and SRI reconciliation. Worker doubles do not establish actual Chromium/Pyodide execution. Keep generated diagnostic outputs outside the distributed source unless they are deliberately selected and identified as validation evidence.

## Documentation and attribution

Keep input formats, parser limitations, output schemas, evidence-contract schemas and commands consistent
with implementation. Preserve the distinction between software version and report-schema version; a release-number change does not silently create a schema migration. Preserve the distinction between documentation formats and formats the engine can actually read. Update examples when behaviour changes;
identify placeholders and pseudocode rather than claiming they were executed.

Use the distribution-root [CITATION.cff](../CITATION.cff) for the current software citation. Cite the exact release
or commit used. Changing citation metadata does not rewrite an earlier release
or transfer copyright. Keep discussion of the legacy repository factual,
version-specific and linked to preserved evidence rather than personal criticism.

## Privacy and security reports

Follow SECURITY.md for security-sensitive issues. Never upload student source,
identified reports, credentials or private evaluation records to a public issue.
Provide a minimal authorised or synthetic reproducer. Any institutional data
collection, retention or participant consent is a separate decision, not an
assumption granted by this contribution guide.

## Acceptance and release

Antonio Clim reviews the proposed scope, implementation, evidence and attribution.
Integration requires the declared checks for the exact proposed files and an inspection of concurrent changes. Hosted CI results are required only if that workflow is actually configured and authorised. A contributor does not approve their own PR as an
independent reviewer; do not invent review approvals.

A contribution may be accepted without creating a release. Do not overwrite an
existing tag or published asset, change repository visibility, invite
collaborators, alter licensing or deploy the application without the maintainer's
specific authorisation. No numerical error-rate claim is established merely by
passing the software test suite.
