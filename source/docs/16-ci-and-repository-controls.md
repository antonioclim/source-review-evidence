# Repository controls

## Local preparation

Source Review Evidence is prepared as a separate repository and initial release. The selected public tree contains no active GitHub Actions workflow. This file selection does not establish a GitHub server setting: disabling Actions for the new repository must be observed in its actual settings when that repository exists.

The current validation is performed locally and recorded in [RP2_VALIDATION.json](../../validation/RP2_VALIDATION.json). Retained JavaScript, Python and browser harnesses describe checks that may be run under their prerequisites. Their presence does not imply a successful hosted CI job or native browser execution.

## Remote controls

The final browser guide covers repository creation, Actions settings, file uploads, the `v1.0.0` release and manual Zenodo deposition. No repository, tag, release, DOI or Zenodo record is created by this documentation.

A read-only inspection should compare the observed repository identity, branch, files and release assets with the prepared inventory. Any file normalisation introduced during browser upload must be assessed against the actual bytes. Automatic GitHub–Zenodo archiving is outside the selected manual deposition route.

## Retained maintainer policies

The component retains earlier dependency, coverage, process and release checks. Some expect the original workflow files, complete component documentation or earlier manifest schema. Those expectations are evidence about the earlier maintenance environment. The new distribution uses its own manifest and declared validation scope without relabelling historical gates as passed.

Runtime-loading integrity, bounded source intake and controlled native process execution remain implementation properties documented in [browser security](04-browser-security.md), [runtime integrity](18-runtime-integrity.md) and [the component guide](../README.md).
