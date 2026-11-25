# Evidence and scope

[Overview](../README.md) · [Data](DATA.md) · [Reproducibility](REPRODUCIBILITY.md)

## The question

A reported source location is evidence for a particular observation. Its adequacy depends on the syntax that the observation traverses. A location containing a function's definition and body may omit a decorator expression that contributes to a computed count. Checking the record's shape or digest therefore answers a different question from checking coverage against the source.

The implementation makes the relevant obligations explicit:

| Obligation | Object of the check |
|---|---|
| Source admission | The supplied bytes and declared source context |
| Observation availability | Whether the observation applies and can be produced |
| Value conformance | Whether the reported value has the required representation and domain |
| Coordinate coverage | Whether the supplied location contains the required source spans |
| Policy evaluation | Whether the declared policy produces the recorded decision |
| Consumer admission and replay | Whether the receiving component can admit and check the supplied record |

A result retains its typed state. An obligation that was not evaluated does not contribute a passing result. The stored records distinguish this situation from invalid input and a failed executed check.

## Evidence included in the research record

### Paired cases: A17

The retained paired study contains 32 pairs across eight constructed families. Three challenge cases are ineligible under the recorded predecessor-admission condition: `F6-V2`, `F6-V3` and `F7-V4`. They remain recorded with that status.

Six cells show additional executed-check distinctions in the retained projection: `F3-V1`, `F3-V2`, `F3-V3`, `F3-V4`, `F6-V1` and `F6-V4`. Their interpretation follows the predicates actually executed. The pilot summary preserves the strict-continuation outcome **`NOT_MET`**.

### Finite oracle: A18

The retained oracle covers 32 constructed programs, 40 callables and 592 recorded checks. Its source templates come from a finite grammar. The additional iterative traversal shares CPython's parser with production, while using a separate traversal implementation. These dependencies define the scope of the agreement.

### Existing technical corrections

The technical derivative addresses three experimental-helper files. It binds callable identities consistently, separates the relevant input objects and aligns the independent traversal with the admitted source normalisation and parser mode. The retained before/after record contains 67 isolated expectations. These expectations concern helper behaviour; they do not add cases to A17 or A18.

## How to interpret the collection

The examples and oracle records support inspection of the declared contracts and their exercised boundaries. The stored comparisons concern the implementation's named projections. Counts of records, checks and repeated audit outputs should be interpreted according to their roles; they are not interchangeable sample sizes.

For the location and meaning of each evidence family, continue with [the data guide](DATA.md). For the requirements of a new execution, use [the reproducibility guide](REPRODUCIBILITY.md).
