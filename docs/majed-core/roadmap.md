# Core-to-Full roadmap

## Delivered in this Core candidate

- Native `majed-adeq` preset with append/wrap contributions.
- Native `majed-governance` extension with deterministic checks and derived views.
- Native `majed-controlled` workflow with profile routing, preflight, evidence,
  gates, pause/resume, and an explicit non-acceptance boundary.
- Native `majed-governed` local bundle with install, repeat install, preservation,
  validation, and removal tests.
- Requirement matrix, qualification record, compatibility limits, and engineering
  report.

## Mandatory before owner acceptance or merge

1. **Owner acceptance** linked to the candidate revision and evidence hashes.
2. **Evidence binding**: record the candidate commit, test artifacts, environment,
   and workflow run ID together. A local gate label is not acceptance.
3. **Authority decisions** for the unresolved constitution/CI scope difference
   (D1/CI) and any remaining C-01..C-11 register items.
4. **Authorized cross-platform verification**: run the affected tests on the
   owner-approved OS/Python matrix; do not claim POSIX from Windows-only evidence.
5. **Baseline decision** on the two known Windows composition-test failures:
   accept the upstream baseline limitation, or authorize the prior test-only
   correction separately.
6. **Independent review** by a different model/human or an explicit owner
   acceptance of the session-level independence limitation.
7. **Wheel packaging decision** if distribution beyond a source checkout is
   desired; add the component paths to force-include and verify the built wheel.

## Full roadmap (deferred, not authorized by this Core candidate)

- `MSK-12`: skill/context selection and progressive loading.
- `MSK-15`: document change preview, diff review, and adoption custody.
- `MSK-16`: Explorer/Studio UI and relationship views (no Core dependency).
- `MSK-17`: semantic compare/merge with obligation preservation.
- `MSK-18`: source-grounded search; no RAG or semantic-answer claim.
- `MSK-10/14/17`: deeper reuse/qualification of native bug and assess workflows.
- Anti-replay transaction management, budgets, leases, concurrency isolation.
- Host/OS/network Policy Enforcement Point and trusted owner identity.
- Lifecycle/drift requalification and scoped evidence invalidation.
- Comparative effectiveness study with matched tasks, holdout, and measured
  sample sizes.

## Explicit non-goals

- Rewriting Spec Kit core or adding a second workflow/approval engine.
- Activating RCCA/AGHR candidate policies.
- Claiming universal host enforcement from a workflow gate.
- Publishing, merging to `main`, pushing, releasing, or installing globally.
