# Naming and path policy

The distribution keeps executable paths stable so that component imports, browser resources and retained evidence remain interpretable. **1.0.0** is the distribution version; internal CodeProbe module names and schema identifiers retain their technical roles.

## Rules

1. Keep conventional root names such as `README.md`, `CITATION.cff`, `VERSION` and `DISTRIBUTION_MANIFEST.json`.
2. Keep existing runtime paths unless a demonstrated defect requires a documented change. A documentation revision does not justify renaming modules or scientific identifiers.
3. Use descriptive Markdown names for reader guides. Number component documentation only where the inherited sequence remains useful.
4. Keep current release metadata separate from frozen computational records and historical qualification inventories.
5. Record every selected, replaced or excluded file in the distribution's provenance. Update active links and documentary checks when the selection changes.

## Current records

The [component catalogue](00-file-catalogue.md) lists the selected `source/` paths. [DISTRIBUTION_MANIFEST.json](../../DISTRIBUTION_MANIFEST.json) binds current bytes. [DISTRIBUTION_CHANGES.json](../../provenance/DISTRIBUTION_CHANGES.json) records the transformation from the baseline. The component-facing `release/file-rename-map.csv` is a view of the current mapping, not proof that an old naming migration was rerun.

The retained naming and reference utilities contain expectations from the earlier complete kit. Current documentary adaptations must be explicit and must preserve assertions about runtime behaviour or scientific records.
