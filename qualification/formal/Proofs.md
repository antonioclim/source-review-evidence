# CodeProbe A2/P6 — formal core and proof obligations

**Document version:** 2.0.0. **Scope:** the approved protocol successor. The executable specification in `spec_model.py` is an auditable reference model, separate from the unchanged P7-R4 production candidate. P7 must implement and qualify the production repair. The results of the model are not results of the original candidate.

## FP01. Admissible counterexamples and the five retained cases

Let D be the declared domain of well-typed execution contexts. Let P and Q be Boolean predicates on that same domain. If w belongs to D, P(w) is true and Q(w) is false, then the universal implication `for every x in D, P(x) implies Q(x)` is false. Substitution of w into the universal sentence contradicts it. This argument does not require a sample, an independence assumption or an estimate of prevalence. A record outside D cannot serve as w.

Four retained cases have this form: admitted source with unavailable requested observation; conforming value/structure with an insufficient coordinate cover; a producer-valid native identifier refused by the consumer grammar; a self-consistent rehashed record whose replay against the fixed context fails. Each case must retain its predecessor validation and the source/profile/build binding. The logical rule does not certify that the original implementation has executed every predicate named by the revised protocol.

The fifth case concerns two profiles and is formalised in FP04. Its distinct logical form is retained explicitly. No new G5 failure is manufactured. The illustrated labels and original executable IDs remain connected through the existing non-bijective crosswalk: Fig1:W1 to P6-C02/W3 syntax; Fig1:W2 to W1; Fig1:W3 to W3 policy; Fig1:W4 to W2; Fig1:W5 to W4. Original executable W5 remains an additional AST/physical-span case.

## FP02. Valid representation does not imply observation availability

For the projection r=(s,v,z), s is one of the four declared observation states, v is the atomic value or null and z is the typed reason. Define V2(r) by state membership, the biconditional `(s=observed) iff (v is not null)` and a nonempty reason for every non-observed state. These are necessary representation constraints; the full producer schema imposes additional conditions.

Given G1 PASS and V2(r), define G2(r) as `s=observed`. Therefore an observed zero satisfies both V2 and G2. The record `(unavailable,null,SYNTAX_ERROR)` satisfies V2 and falsifies G2. A non-observed non-null record falsifies V2; it yields INVALID_INPUT for this verification route. When source admission is not established, the observation-availability check is NOT_EVALUATED.

Thus V2 and G2 have different objects of assurance. A false availability predicate for a genuinely inapplicable observation does not diagnose an analyser defect. The state and reason must remain visible rather than being collapsed into an unqualified operational failure.

## FP03. Full consumer verification is conjunctive

Let C mean that the declared consumer admits a typed record and R mean that replay agrees with the supplied source/profile/build. Both statements must refer to the same declared context, using an explicit association when the consumer envelope and replay capsule have different types. Full G6 is C AND R.

For completed Boolean checks the four pairs (false,false), (false,true), (true,false), (true,true) yield false,false,false,true. Disjunction differs on the two mixed pairs. Neither admission alone nor replay alone establishes G6. A wrong context association is INVALID_INPUT. With a valid context, any completed required failure gives FAIL; two passes give PASS; otherwise the result is NOT_EVALUATED. The status of each subcheck is always retained.

This is a protocol rule. It does not identify an S01 envelope with an S04 capsule or infer that the current code has a single unified entry point for both. Production integration must enforce the association and preserve the types.

## FP04. The policy example is a relational non-determination result

Let x be the same observed value under the same measurement specification. Let pi and pi' be two admitted profiles. Suppose the two evaluations conform to their respective rules and D_pi(x) differs from D_pi'(x). Then no single function f of x alone can equal both decisions: equality to each would imply D_pi(x)=D_pi'(x), contradicting the premise.

Both evaluations can pass G5. The counterexample concerns erasure of the profile argument. In the retained case x=13, the profiles with threshold ranges [8,12] and [14,18] yield review_opportunity and no_rule_trigger. This is one relational case, not a fifth Boolean predecessor-pass/target-fail witness.

## FP05. Integer threshold image

Assume x, L and U are integers, x>=0 and 0<=L<=U. Let T be all integers from L through U and let I(x) be the set of values of the indicator x>t for t in T. T is finite and nonempty.

If x<=L, then x<=t for every t in T, so I(x)={0}. If x>U, then x>t for every t in T, so I(x)={1}. If L<x<=U, t=L supplies 1 and t=U supplies 0. The codomain contains only 0 and 1, hence I(x)={0,1}. If L=U, the middle region is empty. The nominal threshold has no effect on the full-interval image, though its admitted value must lie between L and U.

The endpoint computation uses a constant number of integer comparisons, independent of interval width. Its bit cost depends on operand length; it is not constant in the number of input bits. Exhaustive enumeration costs proportionally to U-L+1 and provides a separate finite check, not the general proof. A non-monotone sequence with endpoint values 0 and an interior value 1 shows why arbitrary policies cannot use this reduction.

## FP06. Boundary distance and integer decision-change radius

For the same domain with fixed L and U, define r_dec(x) as the smallest absolute nonzero change |y-x| over nonnegative integers y whose decision region differs from that of x. Below or at L, the nearest different region starts at L+1, so r_dec=L+1-x. In the middle, a move to L changes the region downward and a move to U+1 changes it upward: r_dec=min(x-L,U+1-x). Above U, the nearest other region ends at U: r_dec=x-U.

Every listed candidate is admissible and has a different region. Every smaller integer change remains in the same closed or half-open region, proving minimality. A different region always exists under these assumptions. The quantity is strictly positive. In contrast, min(|x-L|,|x-U|) is the geometric distance to a boundary and can be zero. At x=L=2 and U=4 the two quantities are 1 and 0 respectively.

Changing a particular decision does not refute FP05. The theorem would be refuted by an admissible tuple where the actual interval image differs from the piecewise formula. The radius register records these three notions separately.

## FP07. Exact lexical-decimal comparison

A finite decimal is a signed coefficient c multiplied by 10^e. For e>=0 it is the integer c*10^e; otherwise it is the rational c/10^(-e). Decimal parsing may be used to obtain the immutable sign/digit/exponent tuple. Context-dependent arithmetic and normalisation are excluded from the decision path.

Let a,b,at,rt be these rational values with at>=0 and rt>=0. Compute delta=|a-b| and tolerance=max(at,rt*max(|a|,|b|)). All rational operations reduce to integer addition, multiplication and comparison with positive denominators. Cross-multiplication preserves the order. Therefore `delta<=tolerance` includes exact equality and is independent of Decimal precision, rounding mode and inexact traps whenever the computation completes.

A canonical value string can remove insignificant trailing zeroes and signed zero, while preserving the numerical value. Every intermediate quantity here is a terminating decimal: the rational denominators contain only factors 2 and 5 and the operations use addition, subtraction, multiplication and maximum. For denominator 2^p*5^q, multiplying the numerator by 2^(k-p)*5^(k-q), k=max(p,q), produces a coefficient over 10^k. This gives exact serialisation without rounding. The input spelling and its lexical identity remain separate data if needed.

The P3 input 1+10^-28 compared with 0 at tolerance 1 is outside by integer comparison 10^28+1>10^28. The P6 reference model is required to preserve that difference at every tested Decimal context. A fixed precision of 50 is not a proof for unrestricted finite lexical strings.

The mathematical domain is unchanged. A finite implementation must document resource budgets. Resource exhaustion or an explicitly budgeted refusal must be typed separately and must never return a passing comparison. This proof does not certify the current implementation's memory safety or its future resource guards; those are P7 obligations.

## FP08. Numeric soundness of conservative binary64 admission

For finite binary64 operands, use exact rational centres a,b and radii ua=ulp(a)/2, ub=ulp(b)/2. The declared sets are the closed intervals A=[a-ua,a+ua] and B=[b-ub,b+ub]. They are conservative uncertainty sets. Around a power-of-two transition the symmetric interval can exceed the actual round-to-nearest preimage. No exact preimage or tie-membership equivalence is asserted.

For x in A and y in B, the triangle and reverse triangle inequalities give:

`max(0,|a-b|-ua-ub) <= |x-y| <= |a-b|+ua+ub`.

The map (x,y) -> max(|x|,|y|) is 1-Lipschitz in the maximum norm. Set m=max(|a|,|b|) and u=max(ua,ub). Then:

`max(0,m-u) <= max(|x|,|y|) <= m+u`.

Because rt is nonnegative and max(at,.) is monotone, applying the tolerance map to the magnitude endpoints gives valid lower and upper tolerance bounds. Consequently delta_high<=tolerance_low proves that every represented pair passes. Delta_low>tolerance_high proves that every pair fails. Other cases return indeterminate_boundary, which never passes.

These sufficient conditions are sound and deliberately conservative. Overlap of independently bounded ranges does not prove the existence of both satisfying and violating pairs, because their extrema can depend on the same operands. Therefore the indeterminate status can also occur when a tighter dependency-aware method could decide. This limitation is stated explicitly instead of converting an interval algorithm into an unproved completeness claim.

At zero and in the subnormal range the half-ULP radius remains a nonzero exact rational, even if forming it in binary64 would underflow. At the largest finite operand the interval endpoint may exceed that finite float, but rational arithmetic remains finite. NaN and infinity are rejected before interval construction. Repeated equal floats do not impose an unrecorded correlation between their underlying quantities.

The P3 strict-interior witness belongs to A for 0.1, exceeds the stated tolerance and rounds to 0.1. The exact centre satisfies that tolerance. The same declared interval thus contains both behaviours, so admitting the case is unsound. The revised reference rule returns indeterminate_boundary. The unchanged production module continues to reproduce its old erroneous admission.

## FP09. Identity and scale scope preserved

The observation-slot identity remains determined by the declared specification/entity preimage. Content identity remains determined by the measurement-content scope. A path-only change has no digest effect only where the contract explicitly excludes the path; a change to the included content must be checked against its exact digest input. Hash equality is not authentication, and no proof of injectivity or global uniqueness is claimed.

C=1+d preserves order and differences while changing ratios. The approved ordinal interpretation for policy is retained as a conservative convention. The offset example does not prove that ordinal structure is the only admissible mathematical description. The production identity and scale mechanisms have not been rewritten in P6.

## FP10. Prospective false-alert decision and cluster limitation

The dormant human study retains its original four continuation thresholds. Pooled Wilson 95% is explicitly descriptive when alerts in the same project are dependent. Let Z_j be the within-project false-alert fraction and E_j indicate that project j produces at least one false alert. For resolved projects with a nonzero alert denominator, 0<=Z_j<=E_j. Under a defined independent and identically sampled project frame, E[Z_j]<=Pr(E_j=1). A one-sided exact binomial upper bound for that event probability is therefore a conservative bound for the project-balanced fraction, not the alert-weighted micro ratio.

For zero events among J such projects, the bound at tail probability alpha=0.025 solves (1-p)^J=alpha, hence p_upper=1-alpha^(1/J). With J=6 it is approximately 0.459; with J=17 it is below 0.20. The new guard requires both the existing Wilson diagnostic and this conservative project safeguard to pass. A small all-zero pilot can therefore remain inconclusive. Changing the estimand to the pooled alert ratio would invalidate this domination argument; the two quantities are reported separately.

Projects with no adjudicated alerts are unresolved for this safeguard; they are not silently dropped into a favourable subset. Any unresolved project prevents continuation. Non-independent project selection prevents a population-confidence claim. The human study remains inactive and requires its own future authorisation, ethics determination, independent project frame and resources. This calculation is a prospective design result, not CodeProbe participant data.

## Verification limits

Proofs here establish the stated logical and arithmetic properties. `run_checks.py` supplies finite discriminating cases and independent integer/minimisation/score-inversion checks. The same analyst created and reviewed the materials; neither two scripts nor two runs is an independent human evaluation. No proof assistant or SMT certificate was produced. Production execution, multiprocess coverage, the 52-mutant cohort, resource enforcement and full manuscript concordance remain P7–P10 obligations.
