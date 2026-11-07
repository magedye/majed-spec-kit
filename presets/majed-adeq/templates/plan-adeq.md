## ADEQ Alternatives and Trade-offs *(majed-adeq)*

| Decision | Options considered | Selected | Trade-off and reason |
|---|---|---|---|
| [Decision] | [Reuse / configure / improve / integrate / build / defer] | [Selected] | [Why; what is given up] |

- **Reuse check:** [Which existing Spec Kit capability was inspected first?]
- **Minimal-change check:** [Why is the selected change the smallest justified one?]
- **Deferred options:** [What was deliberately deferred and why]

## Impact, Dependencies, and Recovery *(majed-adeq)*

- **Affected components:** [Paths, contracts, schemas, templates, workflows]
- **Affected users/operations:** [Who must change behavior or rerun work]
- **Dependencies and ordering:** [What must happen first]
- **Failure containment:** [How failures are bounded to the affected scope]
- **Rollback or compensation:** [Exact restore/recovery path]
- **Irreversible effects:** [List, or "none identified"]

## Confidence and Uncertainty *(majed-adeq)*

- **Pre-execution confidence:** [High / Medium / Low]
- **Reasons:** [Evidence, precedent, unknowns]
- **What would change the confidence:** [Test result, review finding, owner decision]
- **Post-verification confidence:** [Fill after actual verification; do not backfill]

## ADEQ Evidence Plan *(majed-adeq)*

| Evidence ID | Claim it supports | Method | Revision/environment | Status |
|---|---|---|---|---|
| EV-001 | [Claim] | [Focused test / command / review / measurement] | [Revision + environment] | [Planned] |

- **Completion rule:** A task is complete only when its required evidence is
  present, current for the tested revision, and honestly labeled.
- **Non-claims:** Passing tests do not by themselves prove owner acceptance,
  host-wide enforcement, release readiness, or comparative superiority.
