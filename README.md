# Source Review Evidence

**Version 1.0.0 — prepared initial distribution**

Software and retained computational evidence for examining what a source-review record establishes about its source. The implementation separates source admission, observations, evidence locations, policy decisions and consumer checks. Its records make these distinctions available for inspection.

The research context is **Checking the Report, Checking the Source: Evidence Obligations in Heuristic Source Review**. Version 1.0.0 starts a separate distribution for these materials. Existing component identifiers are retained where they bind code, records or checksums.

## What to explore

- **Source coverage:** whether a reported location contains the source spans required by a declared observation.
- **Evidence obligations:** which checks admit a record and which require access to the source or policy.
- **Retained comparisons:** the predicates exercised by the stored cases and the outcomes they produced.
- **Implementation checks:** finite oracle records and the existing technical corrections to the experimental helpers.

## Reading order

| Document | Purpose |
|---|---|
| [Evidence and scope](docs/EVIDENCE_AND_SCOPE.md) | The questions addressed by the code and retained evidence |
| [Reproducibility](docs/REPRODUCIBILITY.md) | The distinction between file integrity, isolated checks and strict historical reproduction |
| [Data](docs/DATA.md) | Inputs, reference outputs, interpretation and association with the software |
| [Provenance](docs/PROVENANCE.md) | Version identities, retained originals and component rights |
| [Changelog](CHANGELOG.md) | The scope of this initial distribution |
| [Component guide](source/README.md) | Supported languages, browser/native entry points and extended input boundaries |
| [Component rights](docs/COMPONENT_RIGHTS.md) | Existing notices and the scope of distribution permissions |

The [distribution manifest](DISTRIBUTION_MANIFEST.json) identifies this view's paths and SHA-256 digests. The [view validation record](validation/GITHUB_VIEW_VALIDATION.json) records the checks performed on the browsing view; [RP2_VALIDATION.json](validation/RP2_VALIDATION.json) retains the earlier component-validation results. A corrected helper does not turn a retained output into a result of a new run.

## Complete archive and repository view

This repository tree is the GitHub browsing view. It contains the complete
`source/` component, current reader documentation, selected checks, protocols
and historical helper code. Its own [manifest](DISTRIBUTION_MANIFEST.json) identifies exactly
the files in this tree.

The complete software-and-evidence distribution is the release asset
**`source-review-evidence-1.0.0.zip`**. Use that same archive from the GitHub release or its
associated Zenodo record when inspecting the frozen inputs and outputs. The
complete archive contains 8,437 files; 8,067 retained evidence and
documentary-projection files are available there rather than in this browsing
tree. Their original relative paths are preserved in the archive.

| Location | Available here | Use the complete archive for |
|---|---|---|
| `source/` and `tools/` | Component implementation, documentation and selected local checks | The same software bytes alongside the frozen evidence |
| `experiments/p7c/code/` | Experimental helpers | Inputs, design records and reference outputs under `experiments/p7c/` |
| `protocol/`, `qualification/` and `review/` | Retained protocol and verification-scope material | The execution evidence addressed by those records |
| `docs/` | Current reader documentation | The evidence families described by those guides |
| `results/` and `review_evidence/` | Described in the data guide | The retained computational records themselves |

[GITHUB_VIEW.json](GITHUB_VIEW.json) binds this view to the complete archive by
filename, size and SHA-256. The preserved
[complete-archive manifest](provenance/COMPLETE_ARCHIVE_MANIFEST.json) identifies its full file set;
the root manifest identifies this browsing tree. Historical reproduction
helpers retain their original prerequisites and are not a claim that those
routes execute from this smaller view.

## Distribution identity

The intended public version is **1.0.0** for the new GitHub release and a new Zenodo record containing the complete software-and-evidence archive. The technical derivative remains **CP-FGCS-C2F2-FIX2**. Earlier CodeProbe labels identify inherited software components and record formats.

The published record supplies the actual repository address, publication date and version DOI. These identifiers are not embedded in this prepared archive. [CITATION.cff](CITATION.cff) records the author, title and version; cite the version DOI alongside it once the record exists.

## Licences

Author-controlled code, helpers, tests, functional configuration and historical code snapshots use **MIT**. Author-controlled documentation, included figures and research-record rights use **CC BY 4.0**. Existing notices and permissions remain effective, including MIT-covered documentation and CC0 metadata documents. Mixed records retain separate terms for their code and data portions.

The [licence scope](LICENSE), [component rights](docs/COMPONENT_RIGHTS.md) and [per-file allocation](LICENSING_MAP.json) identify the applicable terms. The complete licence texts are in [LICENSES](LICENSES/README.md).

## Integrity and execution

The extracted GitHub browsing view can be checked locally with:

```bash
python3 tools/verify_distribution.py
```

This checks the file boundary recorded in the manifest. The [component guide](source/README.md) describes native and browser analysis; [reproducibility](docs/REPRODUCIBILITY.md) distinguishes those routes from strict historical reproduction. Posting the prepared distribution uses the separate browser-only guide.

## Selected local checks

The supplied [runner](tools/run_local_checks.py) lists or executes the selected
component checks in a temporary copy, keeping the retained evidence unchanged:

```bash
python3 tools/run_local_checks.py --list
python3 tools/run_local_checks.py
```

The runner reports unavailable dependencies and platform-specific skips.
Its Node scenarios exercise controlled Worker and input contracts. The
[retained component validation](validation/RP2_VALIDATION.json) gives the earlier
observed local results. The [view validation](validation/GITHUB_VIEW_VALIDATION.json)
records the targeted checks of this package. These checks do not run the frozen
studies or qualify a native browser.
