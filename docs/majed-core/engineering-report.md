# Majed Spec Kit Core — engineering report

**Request:** `MSK-EXTENSION-CORE-002`
**Mode:** extension-first, upstream-preserving, controlled local execution
**Baseline:** `ba397542684da2b2d1fe00bbca05cf3911136237`
**Branch:** `feat/msk-extension-core-002`
**Delivery HEAD:** the commit containing this report (`git rev-parse HEAD`)

## 1. Result

`CORE_CANDIDATE_COMPLETE` for the agreed Core scope.

The four native components are integrated and locally qualified. All twelve
`CORE_REQUIRED` requirements have scoped acceptance criteria and focused
verification. This is a functional candidate, not an accepted or released
product:

- `OWNER_ACCEPTANCE: NOT_GRANTED`
- `POLICY_ACTIVATION: NOT_AUTHORIZED`
- `RELEASE_AUTHORIZED: NO`
- `UPSTREAM_CORE_MODIFIED: NO`
- `EFFECTIVENESS_NOT_VERIFIED` for behavioral/agent outcomes.

The two known upstream Windows composition-test failures remain; they are not
Majed defects and are disclosed in the qualification record.

## 2. Component versions

| Component | Version | Status |
|---|---|---|
| `majed-adeq` preset | 1.0.0 | IMPLEMENTED_VERIFIED |
| `majed-governance` extension | 1.1.0 | IMPLEMENTED_VERIFIED |
| `majed-controlled` workflow | 1.1.0 | IMPLEMENTED_VERIFIED |
| `majed-governed` bundle | 1.1.0 | IMPLEMENTED_VERIFIED |

## 3. Completion work in this request

### Requirement completion

- `intake`: source-span candidate extraction with `PENDING` status.
- `impact`: changed-file mapping, unmatched-path detection, rollback requirement
  for risky/non-reversible changes, dependency-note warning.
- `check`: source-span validation, required component/test links, duplicate
  evidence IDs, control-to-requirement links, acceptance/open-requirement
  consistency.
- `trace`: source, component, criteria, evidence, authorization, review columns.
- `converge`: one bounded remediation item per open requirement; optional
  derived plan output without mutating the record.
- `sources`: authority, revision, SHA-256, priority, and supersession validation.
- `metrics`: deterministic requirement/evidence/review/control/acceptance counts.

### Dependency and execution

- Added `dependency-check` and `dependency-version` workflow steps.
- Missing extension fails before preflight with `DEPENDENCY_MISSING`.
- Incompatible bridge version fails before governance checks.
- Bundle plans the extension before the dependent workflow.
- QUICK/STANDARD/CONTROLLED/ASSESS routes exercised.
- Native command dispatch exercised with a disposable stub `claude` CLI:
  2/4/6 dispatches for quick/standard/controlled.

### Packaging

- `bundle build` artifact created.
- Artifact installed in a clean consumer.
- Repeat install, `--refresh`, user-file preservation, and removal verified.
- Wheel/catalog distribution remains `NOT_VERIFIED`; the upstream
  force-include proposal is documented separately and not implemented.

## 4. Verification

| Check | Result |
|---|---|
| Focused Majed tests | 54 passed in 21.57s |
| Contract suite | 170 passed |
| Preset suite | 763 passed |
| Extension suite | 236 passed, 10 skipped |
| Bundle suite | 1272 passed, 4 skipped |
| Workflow definition suite | 66 passed, 2 known baseline failures |
| Bundle artifact build/install | PASS |
| Consumer execute routes | PASS (stub dispatch) |
| Dependency removal behavior | PASS (workflow fails at dependency-check) |
| Checker microbenchmark | 0.0455 ms/check, 1000 iterations |
| Synthetic negative detection | 5/5 |
| POSIX/CI/wheel/catalog | NOT_VERIFIED |
| Real agent behavior | EXECUTE_NOT_VERIFIED |
| Comparative effectiveness | EFFECTIVENESS_NOT_VERIFIED |

The two failures are the pre-existing upstream Q-03 fixture issue:

```text
test_same_call_bound_per_fan_out_item
test_same_call_bound_per_loop_iteration
```

The prior review verified the test-only correction in `ca3233a`; that candidate
was not merged here.

## 5. Requirements coverage

Detailed matrix: [requirements-matrix.md](requirements-matrix.md).

- `CORE_REQUIRED`: 12/12 have scoped acceptance criteria and verification.
- `REUSE_ONLY`: MSK-10, MSK-14 (native capabilities; not rebundled here).
- `DEFERRED` to Full: MSK-12, MSK-15, MSK-16, MSK-17, MSK-18.
- MSK-20 remains `IMPLEMENTED_PARTIAL` (no learning/lifecycle loop).
- MSK-09 correction executes through native tasks; the extension produces the
  bounded plan and does not auto-approve or auto-correct.
- MSK-13 validates a source manifest; it is not a new host-wide source resolver.
- MSK-19 computes local evidence/review metrics; it does not perform an
  independent review.

## 6. Governance and enforcement boundaries

- Workflow gates record choices; they do not authenticate identity.
- `accept` remains `owner_acceptance: NOT_GRANTED` and `authenticated: false`.
- Local JSON evidence is not tamper-proof.
- No host-wide PEP, OS/network mediation, or credential control is implemented.
- No budget/token/cost hard cap is claimed.
- No anti-replay transaction manager is claimed.
- RCCA v1.4.0 remains an inactive candidate reference.

## 7. Pending owner decisions

1. Accept or reject this `CORE_CANDIDATE_COMPLETE` scoped candidate.
2. Bind owner acceptance to the delivery HEAD and evidence hashes.
3. Decide the constitution vs CI/SUPPORT drift and any remaining C-01..C-11
   register items.
4. Decide whether to accept the two pre-existing upstream Windows baseline
   failures or authorize the prior test-only correction separately.
5. Authorize POSIX/CI matrix qualification.
6. Decide whether wheel/catalog distribution is required; if so, authorize the
   documented upstream force-include proposal and qualify the built artifact.
7. Authorize or decline comparative effectiveness work.
8. Provide independent review by a different model/human, or explicitly accept
   the session-level independence limitation.

## 8. Completion contract

```text
CORE_IMPLEMENTATION_STATUS: CORE_CANDIDATE_COMPLETE (agreed scoped Core)
NATIVE_EXTENSION_COMPATIBILITY: VERIFIED_LOCAL_SOURCE_AND_BUNDLE_ARTIFACT; WHEEL_AND_CATALOG_NOT_VERIFIED; POSIX_NOT_VERIFIED
PRESET_STATUS: IMPLEMENTED_VERIFIED
EXTENSION_STATUS: IMPLEMENTED_VERIFIED
WORKFLOW_STATUS: IMPLEMENTED_VERIFIED (routing/gates/resume/dispatch; real agent behavior NOT_VERIFIED)
BUNDLE_STATUS: IMPLEMENTED_VERIFIED (artifact install/reinstall/refresh/remove)
REQUIREMENTS_COVERAGE: 12/12 CORE_REQUIRED scoped criteria verified; Full items deferred
FUNCTIONAL_VERIFICATION: PASS (54/54 focused; regression suites pass except 2 known upstream baseline failures)
INTEGRATION_VERIFICATION: PASS (clean consumer; dependency and removal behavior)
EFFECTIVENESS_STATUS: EFFECTIVENESS_NOT_VERIFIED
UPSTREAM_CORE_MODIFIED: NO
INDEPENDENT_REVIEW_STATUS: NOT_PERFORMED
OWNER_ACCEPTANCE_STATUS: NOT_GRANTED
RELEASE_AUTHORIZATION_STATUS: NOT_AUTHORIZED
OWNER_ACCEPTANCE: NOT_GRANTED
POLICY_ACTIVATION: NOT_AUTHORIZED
RELEASE_AUTHORIZED: NO
```
