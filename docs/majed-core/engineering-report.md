# Majed Spec Kit Core — engineering report

**Request:** `MSK-EXTENSION-CORE-001`  
**Mode:** autonomous, extension-first, upstream-preserving  
**Baseline:** `f74bdb893dcba23de72069b46ced5baaeb1684ea`  
**Branch:** `feat/msk-extension-core-001`  
**Delivery HEAD:** the commit containing this report (`git rev-parse HEAD`)

## 1. Result

`CORE_PARTIAL`

Four native components are implemented and locally qualified. The Core is not
complete because several `CORE_REQUIRED` capabilities are partial (notably
automatic semantic traceability, full convergence, lifecycle/drift, and
independent review), and no comparative effectiveness study was performed.

No authorization is granted by this report:

- `OWNER_ACCEPTANCE: NOT_GRANTED`
- `POLICY_ACTIVATION: NOT_AUTHORIZED`
- `RELEASE_AUTHORIZED: NO`
- `UPSTREAM_CORE_MODIFIED: NO`

## 2. What was implemented

### 2.1 `majed-adeq` preset

- Appends ADEQ sections to `spec-template`, `plan-template`, `tasks-template`,
  and `checklist-template`.
- Wraps `speckit.clarify` with a decision-changing clarification guard while
  preserving the native body through `{CORE_TEMPLATE}`.
- Covers outcome/non-goals, assumptions, alternatives, impact/recovery,
  confidence, obligations, and evidence planning.
- Verified by `tests/specify_cli/presets/test_majed_adeq_preset.py`.

### 2.2 `majed-governance` extension

- Adds `speckit.majed-governance.check`, `.trace`, and `.decide`.
- Provides a project-owned JSON record template and schema.
- Deterministic stdlib validator detects:
  - unsupported `COMPLETE` claims without evidence;
  - self-asserted evidence used as completion proof;
  - stale evidence revisions;
  - untrusted/expired authorization sources;
  - false independence;
  - missing/unsupported control claims;
  - unauthenticated acceptance;
  - unsupported budget claims.
- Adds `workflow_bridge.py` for the controlled workflow because the current
  bundled-workflow install path does not copy workflow-package companions.
- Verified by `tests/extensions/test_majed_governance.py`.

### 2.3 `majed-controlled` workflow

- One native workflow with `quick`, `standard`, and `controlled` routes.
- `assess` mode: deterministic preflight → evidence record → review gate →
  acceptance gate → close.
- `execute` mode: native `speckit.specify`, `clarify`, `plan`, `tasks`,
  `analyze`, and `implement` commands, with gates and an acceptance boundary.
- Uses native checkpoints, pause, resume, and gate verdict inputs.
- Verified by `tests/specify_cli/workflows/test_majed_controlled_workflow.py`.

### 2.4 `majed-governed` bundle

- Composes the preset, extension, and workflow through native references.
- Local clean-consumer install, list, repeat install, user-file preservation,
  and removal are tested.
- `specify bundle validate --path bundles/majed-governed` passes.
- Verified by `tests/specify_cli/bundles/test_majed_governed_bundle.py`.

## 3. Git history

| Commit | Change |
|---|---|
| `c03a161` | `feat: add majed-adeq decision-quality preset` |
| `f00be7a` | `feat: add majed-governance assurance extension` |
| `56524fe` | `feat: add majed-controlled profile workflow` |
| `5d4395a` | `feat: add majed-governed installable bundle` |
| `ae28be2` | `fix: install controlled workflow bridge with governance extension` |
| `60381c1` | `fix: harden governance console output and workflow fixture` |
| final docs commit | Requirements matrix, compatibility, roadmap, qualification, this report |

No file under `src/specify_cli/` was modified. No upstream template was replaced.
No push, merge, release, deployment, or global installation was performed.

## 4. Verification

| Check | Result |
|---|---|
| New focused tests | 32 passed in 19.05s |
| Affected component/contract/extension suite | 3999 collected; 3719 passed, 278 skipped, 2 failed |
| Bundle validation | pass |
| Clean consumer install/list/reinstall/remove | pass |
| Controlled workflow `assess` run | completed; evidence `owner_acceptance=NOT_GRANTED` |
| Governance record check | PASS with 3 limitations/warnings |
| POSIX / CI matrix | NOT_VERIFIED |
| Wheel/catalog distribution | NOT_VERIFIED |
| `mode=execute` agent dispatch | NOT_RUN |
| Comparative effectiveness | EFFECTIVENESS_NOT_VERIFIED |

The two suite failures are the known upstream Windows Q-03 composition-test
fixture issue (`run: 'true'`), unrelated to the Majed components. The prior
review verified the test-only correction in `ca3233a`; that candidate was not
merged here.

## 5. Requirement coverage

The detailed matrix is in [requirements-matrix.md](requirements-matrix.md).
Summary:

- `CORE_REQUIRED`: MSK-01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 13, 19.
- Implemented verified: MSK-02, 03, 05, 06, 11.
- Implemented partial: MSK-01, 04, 07, 08, 09, 13, 19.
- Reuse/interface: MSK-10, 14.
- Deferred to Full: MSK-12, 15, 16, 17, 18.
- Partial compatibility/maintenance: MSK-20.

## 6. Governance and enforcement boundaries

- Gate choices are recorded but are not authenticated approval.
- `accept` remains `PENDING` / `owner_acceptance: NOT_GRANTED`.
- Local JSON evidence is not tamper-proof.
- No host-wide Policy Enforcement Point, identity provider, or network/OS gate
  is implemented or claimed.
- No budget/cost hard cap is claimed.
- No anti-replay transaction layer is claimed.
- RCCA v1.4.0 is used as a reference only; its candidate policies are not
  activated.

## 7. Pending owner decisions

1. Accept or reject this `CORE_PARTIAL` candidate as the basis for a limited
   first Core implementation phase.
2. Bind owner acceptance to the delivery HEAD and evidence hashes.
3. Provide or close the C-01..C-11 authority register; decide the constitution
   vs CI/SUPPORT drift.
4. Decide whether to accept the two known upstream Windows baseline test
   failures or authorize the prior test-only correction separately.
5. Authorize the OS/Python matrix and any POSIX qualification.
6. Decide whether a published wheel/catalog distribution is required; if so,
   add the component paths to the wheel force-include list and qualify the built
   artifact.
7. Decide whether to authorize comparative effectiveness work.
8. Provide independent review by a different model/human, or explicitly accept
   the session-level independence limitation.

## 8. Final limitations

- `MSK-CORE-IMPLEMENT-002` was not located; its detailed scope is `NOT_VERIFIED`.
- The bundle is installable from the source checkout; catalog publication and
  wheel-bundled installation are not qualified.
- The workflow's `execute` mode is structurally validated but was not dispatched
  against a real agent in this qualification.
- The existing upstream baseline still has two known Windows test failures.
- This is a candidate, not an accepted or released product.
