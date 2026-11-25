# CodeProbe formal boundary specification v2

**Status:** local Phase-6 candidate; manuscript integration is reserved for Phase 8.  
**Epistemic status:** `[DERIVED]` and `[EXECUTED]` where a named test is given.  
**Scope:** the bounded native CodeProbe source-review route, not static analysis in general.

## 1. Domain

Let an execution context be $\omega=(b,\ell,p,\pi,\rho)$, where $b$ is a finite byte sequence, $\ell$ a declared language, $p$ a logical path, $\pi$ a versioned interpretation profile and $\rho$ a declared runtime/build identity. The route emits a typed refusal or a finite set of observation records.

## 2. Gates

| Gate | Boundary | Pass condition | Failure condition |
|---|---|---|---|
| G1 | source admission | an IntakeRecord binds raw and normalised hashes, UTF-8 text and physical lines | typed refusal; no substitute bytes or silent decoding repair |
| G2 | observation availability | one of observed, not_applicable, insufficient_evidence or unavailable; observed iff value is non-null | state/value mismatch or missing typed reason |
| G3 | value and codomain conformance | atomic finite value, unit, codomain and measurement scale match the specification | domain, bound, unit or scale violation |
| G4 | source-evidence adequacy | structural evidence admission and, where required, coordinate coverage of all visited spans | unknown evidence, wrong scope or uncovered visited span |
| G5 | policy interpretation | versioned non-compensatory decision vector with declared threshold set | profile mismatch, undeclared threshold or non-applicable rule treated as a decision |
| G6 | consumer admission and source replay | accepted envelope or replay agreement; aliases preserve original source identity | typed rejection, replay mismatch or identity loss |

## 3. Non-substitution

For named gates $G_i,G_j$, an admissible witness satisfying $G_i=\mathrm{PASS}$ and $G_j=\mathrm{FAIL}$ refutes $G_i\Rightarrow G_j$ on the declared domain. The retained evidence supports five failed implications: G1 does not imply G2; G3 structural/digest conformance does not imply G4 coordinate coverage; G3 value conformance does not fix G5 policy outcome; G3/G4 validity does not imply G6 consumer admission; G6 internal digest consistency does not imply G6 source replay. These are selected witnesses. They do not establish statistical independence, exhaustive pairwise independence or an emergent system guarantee.

## 4. Threshold proposition

For $T=[L,U]\cap\mathbb Z$, define $D_T(x)=\{\mathbf 1[x>t]:t\in T\}$. If $x\le L$, every outcome is zero. If $L<x\le U$, both zero and one occur. If $x>U$, every outcome is one. In the middle region, $t=L$ gives one and $t=U$ gives zero. The middle region is empty when $L=U$. For this monotone predicate, endpoints determine the image of the full interval. P6-T01 independently checks 3,948 admissible tuples.

## 5. Measurement-scale proposition

The decision-point quantity $d$ is a non-negative count with a non-arbitrary zero. The conventional quantity $C=1+d$ is an affine translation. With $d_1=1$ and $d_2=3$, $d_2/d_1=3$, whereas $C_2/C_1=4/2=2$. Ratio claims about $C$ are therefore not invariant to the offset. Candidate specification 1.2.0 declares $C$ ordinal; ordering and threshold comparisons remain admissible. Historical numeric values are unchanged and retain their original provenance status.

## 6. Identity proposition

`record_id` identifies a versioned observation slot within a measurement result. It hashes `specification_id` and `entity_id`, excluding evidence and value. `measurement_digest` identifies deterministic result content and binds source bytes, evidence and observation content while excluding path metadata. A content mutation may preserve `record_id` and must change `measurement_digest`. A specification-version change must change the affected `record_id`.

## 7. Numerical comparison

Prospective manifest-bound quantities use finite decimal lexical values. The rule is $|a-b|\le\max(a_0,r_0\max(|a|,|b|))$ with inclusive equality. Binary64 compatibility uses half-ULP intervals. If the difference and tolerance intervals overlap, the result is `indeterminate_boundary`, which is not admitted as a pass. This policy does not reinterpret CE09 or CE11 outputs.

## 8. Falsification criteria

1. A non-substitution witness loses evidential weight if its predecessor did not pass under its own contract.
2. A threshold counterexample in the declared integer domain refutes the endpoint proposition.
3. A ratio-scale interpretation of `C` in the candidate refutes the scale repair.
4. A content change that leaves `measurement_digest` unchanged refutes content identity.
5. A binary boundary classified as a pass despite interval overlap refutes the numerical policy.
6. Any principal conclusion requiring prevalence, causal benefit, economic effect or universal correctness violates the frozen scope.
