# CodeProbe — local APEX2 P7B working revision

**Active revision:** `P7-R4-review-candidate+a2p7b.1`.
**Status:** intermediate, unreleased, not a submission kit. The LP02/v3.2
editorial archives and public v2.3.0 source provenance remain unchanged.
P7B preserves the production source implemented in P7A. It adds contract tests,
process-scoped measurement and dependency/provenance metadata.

Verify the current working tree and its bounded metadata:

```
python -I -B VERIFY.py
python -I -B VERIFY_METADATA.py
```

Run the 83-test focused qualification, oracle and claims-as-tests:

```
python -I -B qualification/run_p7b.py --output ../P7B_check
```

`--full` selects the unchanged 824 source tests plus 30 P7A and 40 P7B tests:
894 tests, with the existing platform-specific skip reported. `--coverage`
requires the already installed coverage.py 7.13.3 and measures six core modules
through direct current-Python subprocess descendants; it does not install it.
`--mutation --workers 4` is an explicit, expensive option: all 52 transported
historical faults and 12 new-module faults, with full-source follow-up for
survivors. Depending on survivors it can take tens of minutes. Read
`qualification/p7b/MEASUREMENT_SCOPE.md` first. Results are retained in a new
external directory; existing output is never cleared or silently retried.

`qualification/run_p7a.py` is retained as a compatibility/regression route and
emits its original P7A result-schema label. Its label does not identify a newly
published or independently certified P7B package. The prior verifier and metadata
are archived as inert history under `qualification/history/P7A/`.

The observed Python dependency versions and installed-file hashes are in
`metadata/review-environment.observed.json`. They are not a portable wheel lock,
OS SBOM, vulnerability clearance or clean-machine Q07 qualification. No portal,
repository write, A19/A20 or human study is executed by these commands.

The text below is a historical LP02 README. Its old timings and result claims
remain attached to that baseline. Use the commands above for the current tree.

## Retained LP02 baseline README (historical text)

# CodeProbe P7-R4 local review candidate

## Supplementary information identification

- **Article:** *CodeProbe: Evidence Gates Can Fail Separately in Heuristic Source Review*
- **Journal:** *Software Quality Journal*
- **Supplementary item:** Online Resource 2
- **Author:** Antonio Clim
- **Affiliation:** Department of Economic Informatics and Cybernetics, Bucharest University of Economic Studies, Bucharest, Romania
- **Corresponding email:** antonio.clim@csie.ase.ro

Status: **local, unreleased review candidate; package revision R4**. This package does not replace or modify the public CodeProbe v2.3.0 release.

The claim-carrying review kit binds nine retained principal claims to executable obligations, deterministic outputs and a SHA-256 results manifest. Historical CE09/CE11-dependent quantities remain `UNVERIFIED_CONTEXT_ONLY` and do not support the retained principal conclusions.

## Five-minute smoke test

```text
python -I -S -B review/run_smoke.py
```

## Full reproduction

```text
python -I -S -B review/run_reproduction.py --output reproduced-results
```

Compare `reproduced-results/results-manifest.json` with `results/results-manifest.json`. The R4 clean qualification completed in 164.688 seconds with zero SHA-256 mismatches; the smoke route completed in 6.766 seconds. See `documentation/REVIEWERS_GUIDE.md` and `documentation/REVIEWER_QUICK_START.md`. No external network access is required or intentionally used. The full source suite intentionally exercises loopback-only HTTP and process fixtures. Syscall-level network telemetry was not collected.

## Citation-metadata boundary

The root `CITATION.cff` identifies only this local unreleased P7-R4 review package. Public-release metadata for CodeProbe v2.3.0 remains under `source/` and records source lineage only. No public version, tag or DOI is assigned to this review candidate. For peer-review identification, use the article and Online Resource metadata above together with the archive SHA-256 supplied in the submission package.

## Witness identifiers — LP02 documentary clarification

Figure-local W1–W5 and executable P6-C02/W1–W5 have different groupings. Read `documentation/WITNESS_CROSSWALK.md` and `metadata/witness-crosswalk.json` before matching a figure row to a result record. The code identity remains P7-R4; LP02/v3.2 identifies only the documentary packaging revision.
