# Measurement scale, identity and numerical comparison — local Phase-6 candidate

**Status:** local candidate; not released and not a retroactive reinterpretation of public v2.3.0.

## Measurement scale

`python.callable.decision_point_count` remains a ratio-scale count. `python.callable.mccabe_complexity` is defined as `C = 1 + d`, where `d` is the decision-point count. Version 1.2.0 declares `C` conservatively as ordinal. Ordering and fixed-threshold comparisons remain admissible. Ratio statements about `C`, such as “twice as complex”, are inadmissible because the additive offset changes ratios. The numeric value is unchanged; only its scientific scale declaration changes.

## Identity

`record_id` identifies the versioned observation slot within one measurement result and hashes `specification_id` plus `entity_id`. It is stable under evidence or value changes and is not a global content identifier. `measurement_digest` binds deterministic result content, including artifact hashes, evidence and observations, while excluding path metadata. The pair of roles prevents a mutable content hash from being mistaken for a stable slot identifier.

## Numerical comparison

Manifest-bound results use finite decimal lexical values and the inclusive rule `|a-b| <= max(abs_tol, rel_tol * max(|a|, |b|))`. Binary64 inputs are diagnostic only. Half-ULP intervals that overlap the boundary yield `indeterminate_boundary`, which cannot pass a scientific claim check. The policy applies prospectively. Historical CE09 and CE11 values retain their original status and are not recomputed by this patch.
