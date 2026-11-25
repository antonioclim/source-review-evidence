# P7B measurement scope

The production corpus comprises the five original core modules plus the new
codeprobe_evidence_gates module. No source line, branch or surviving mutant is
excluded to raise an indicator. The thresholds remain 0.85 branch coverage and
0.70 mutation detection per core module.

The bootstrap instruments direct current-interpreter Popen descendants, preserving
-I/-S/-B and explicitly replaced environments. Every matching core import is
recorded with its byte hash. Coverage arcs from copied modules are united only
when the loaded bytes match the canonical source. Other process APIs and
non-Python children are recorded; this is not a syscall-complete monitor or a
security boundary against hostile code. Forced fixture exits may omit coverage
files. A core-loaded process without a save or an unbound core path is a failure
of the asserted measured domain, not silently accepted as complete.

The one original test that deliberately resets sys.settrace is retained.
Collection is restored after it. Instrumentation warnings are preserved in the
audit side-channel rather than contaminating the target's stderr. Product
warnings are unchanged. Control canaries exercise nested -I/-S Python with
replaced environments and os._exit.

Original fixed cohort: 52 specification files under cohort52/. Mapping:
40 unchanged byte/AST bindings, 11 numeric operator rebindings and one explicitly
semantic successor for M025, whose old type guard was refactored. New gates:
12 evenly spaced sites among 116 sorted comparison/Boolean candidates, fixed
before those outcomes. The two cohorts are reported separately. No equivalence
deductions are applied. Mutation executes in memory after exact source hashing;
a source-manifest rejection alone is not a behavioural detection.

Campaign rounds are separate: initial 78-test focused workload (13 original
formal + 30 P7A + 35 P7B), complete-source 889-test follow-ups, then five disclosed
adaptive contract tests and a new 83-test focused round on all faults. The final
survivors receive 894-test complete-source follow-up. Oracle and claims execute
in every tier. All original tests and the first 35 supplementary methods are
preserved. Runtime/timeout/import faults need review and never count as automatic
mutation kills. The standalone runner emits provisional detection classifications;
read the logs before accepting a new campaign's score.

A successful measurement says nothing about clean installation, browser branch
coverage, multiple operating systems, an independent evaluator, empirical fault
prevalence or publication. No study or pilot is activated.
