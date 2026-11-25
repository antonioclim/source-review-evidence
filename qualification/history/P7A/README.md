# CodeProbe — local APEX2 P7A working revision

**Active revision:** `P7-R4-review-candidate+a2p7a.1`.
**Status:** intermediate, unreleased, not a submission kit. The LP02/v3.2 archives
remain unchanged. This working tree implements the P6 numeric and G2/G5/G6 contracts.

Use `python -I -B VERIFY_P7A.py` for this exact working tree. The historical
`VERIFY.py` and prior result records remain for provenance and are not the
qualification authority of this revision. Do not interpret public v2.3.0 metadata
under `source/` as a new public release. No release receipt has been refreshed.

Run the new local qualification in a new directory outside this tree:

```
python -I -B qualification/run_p7a.py --output ../P7A_check
```

Add `--full` to include the unchanged 824-test source cohort. The retained single
skip remains declared. The Linux resource probe is explicitly platform-scoped.
Read `P7A_CURRENT_STATE.md` before using the result. No cloud, portal or repository
write is part of the command.

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
