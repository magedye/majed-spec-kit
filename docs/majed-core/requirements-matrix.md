# Majed Core requirements coverage

**Scope:** `MSK-EXTENSION-CORE-001`  
**Baseline:** `f74bdb893dcba23de72069b46ced5baaeb1684ea`  
**Status legend:**

- `IMPLEMENTED_VERIFIED` — behavior exists and focused tests pass.
- `IMPLEMENTED_PARTIAL` — useful behavior exists; part of the capability is not implemented.
- `REUSE_ONLY` — native Spec Kit capability is reused, not rebuilt or qualified here.
- `DEFERRED` — intentionally outside this Core candidate.
- `UNDETERMINED` — source or decision is unavailable.
- `NOT_APPLICABLE` — out of the agreed Core scope.

`CORE_REQUIRED` means the owner request or the adopted Core slice requires the
capability. A `CORE_PARTIAL` overall result is expected while any
`CORE_REQUIRED` item is partial or deferred.

## MSK-01..20

| ID | Capability | Decision | Component / evidence | Status |
|---|---|---|---|---|
| MSK-01 | Understand the objective and preserve request, constraints, exceptions | IMPROVE / CONFIGURE | `majed-adeq` spec append; governance record template; `tests/specify_cli/presets/test_majed_adeq_preset.py` | IMPLEMENTED_PARTIAL |
| MSK-02 | Ambiguity analysis and clarification | CONFIGURE | `majed-adeq` clarify wrap; preset tests | IMPLEMENTED_VERIFIED |
| MSK-03 | Alternatives and trade-off evaluation | CONFIGURE | `majed-adeq` plan append; preset tests | IMPLEMENTED_VERIFIED |
| MSK-04 | Impact analysis and rollback readiness | IMPROVE | `majed-adeq` plan append; controlled workflow; tests | IMPLEMENTED_PARTIAL |
| MSK-05 | Confidence before and after execution | CONFIGURE | `majed-adeq` plan append; preset tests | IMPLEMENTED_VERIFIED |
| MSK-06 | Document quality and completeness | CONFIGURE | `majed-adeq` checklist append; preset tests | IMPLEMENTED_VERIFIED |
| MSK-07 | Requirement and obligation traceability | BUILD / INTEGRATE | `majed-governance` trace/check; record template; extension tests | IMPLEMENTED_PARTIAL |
| MSK-08 | Output consistency and contradiction detection | IMPROVE | `majed-governance` duplicate/missing checks; native `analyze` reused | IMPLEMENTED_PARTIAL |
| MSK-09 | Bounded convergence and gap correction | IMPROVE | Unsupported-completion and stale-evidence checks; no full convergence engine | IMPLEMENTED_PARTIAL |
| MSK-10 | Bug diagnosis and repair | REUSE | Native `bug` extension exists; not bundled or qualified here | REUSE_ONLY |
| MSK-11 | Proportional, resumable execution routing | INTEGRATE | `majed-controlled` quick/standard/controlled routes; workflow tests | IMPLEMENTED_VERIFIED |
| MSK-12 | Skill and context selection | DEFER | Not implemented; no new context-selection engine | DEFERRED |
| MSK-13 | Sources, versions, authority, and precedence | IMPROVE | Governance record `source`, `revision`, authorization fields; no source registry | IMPLEMENTED_PARTIAL |
| MSK-14 | Document and request intake | REUSE | Native `assess` extension is available; not bundled or qualified here | REUSE_ONLY |
| MSK-15 | Document change review and diff adoption | DEFER | Not implemented | DEFERRED |
| MSK-16 | Local Explorer and relationship view | DEFER | Explicitly outside Core; Full only | DEFERRED |
| MSK-17 | Compare/merge items while preserving obligations | DEFER | Not implemented | DEFERRED |
| MSK-18 | Source-grounded search | DEFER | Not implemented; no RAG claim | DEFERRED |
| MSK-19 | Evidence, review, and quality metrics | BUILD / INTEGRATE | Governance check/trace/decide; workflow evidence artifact; tests | IMPLEMENTED_PARTIAL |
| MSK-20 | Governed learning, maintenance, compatibility | IMPROVE | Bundle compatibility/limitations and RCCA reuse decision; no learning loop | IMPLEMENTED_PARTIAL |

**CORE_REQUIRED items:** MSK-01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 13, 19.
Several remain partial; therefore the overall result is `CORE_PARTIAL`, not
`CORE_CANDIDATE_COMPLETE`.

## ADEQ-01..24

| ID | ADEQ obligation | Coverage | Status |
|---|---|---|---|
| ADEQ-01 | Understand the intended outcome | Preset spec outcome/non-goals; record template | IMPLEMENTED_VERIFIED |
| ADEQ-02 | Preserve and trace obligations | Preset obligation trace; governance trace | IMPLEMENTED_PARTIAL |
| ADEQ-03 | Inspect sources and reconcile authority | Record source/revision; authority findings | IMPLEMENTED_PARTIAL |
| ADEQ-04 | Identify consequential ambiguity | Clarify wrap | IMPLEMENTED_VERIFIED |
| ADEQ-05 | Clarify with options and advice | Clarify wrap | IMPLEMENTED_VERIFIED |
| ADEQ-06 | Avoid unnecessary interruptions | Clarify wrap guidance | IMPLEMENTED_VERIFIED |
| ADEQ-07 | Reuse before building | Plan alternatives; native-component architecture | IMPLEMENTED_VERIFIED |
| ADEQ-08 | Recommend before consequential execution | Plan alternatives and decision criteria | IMPLEMENTED_VERIFIED |
| ADEQ-09 | Explain impact and recovery readiness | Plan impact/recovery section | IMPLEMENTED_VERIFIED |
| ADEQ-10 | Separate pre-execution confidence | Plan confidence section | IMPLEMENTED_PARTIAL |
| ADEQ-11 | Update confidence after verification | Plan post-verification field; no automatic backfill | IMPLEMENTED_PARTIAL |
| ADEQ-12 | Plan proportionately | Quick/standard/controlled profiles | IMPLEMENTED_VERIFIED |
| ADEQ-13 | Maintain coherent documents | Preset templates; no full cross-artifact engine | IMPLEMENTED_PARTIAL |
| ADEQ-14 | Check documentation quality and consistency | Checklist append; governance duplicate checks | IMPLEMENTED_PARTIAL |
| ADEQ-15 | Preserve pre-existing work | Bundle repeat install and user-file tests | IMPLEMENTED_VERIFIED |
| ADEQ-16 | Complete the authorized scope | Workflow routes and documented scope | IMPLEMENTED_PARTIAL |
| ADEQ-17 | Diagnose failures and verify the original symptom | Native bug workflow reused; not qualified here | REUSE_ONLY |
| ADEQ-18 | Use relevant existing capabilities | No `src/specify_cli` changes; native Preset/Extension/Workflow/Bundle | IMPLEMENTED_VERIFIED |
| ADEQ-19 | Define observable success before coding | Spec success criteria + evidence plan | IMPLEMENTED_VERIFIED |
| ADEQ-20 | Verify and review according to risk | Profile routing; review gates | IMPLEMENTED_VERIFIED |
| ADEQ-21 | Converge and audit completion honestly | Unsupported-completion and self-assertion checks | IMPLEMENTED_PARTIAL |
| ADEQ-22 | Execute within valid delegation | Authorization representation; no host identity enforcement | IMPLEMENTED_PARTIAL |
| ADEQ-23 | Escalate decisions rather than routine steps | Workflow gates; decision brief | IMPLEMENTED_VERIFIED |
| ADEQ-24 | Learn and measure practical effectiveness | `EFFECTIVENESS_NOT_VERIFIED`; no comparative measurement | DEFERRED |

## Execution governance domains D1..D6

| Domain | Delivered | Status | Limit |
|---|---|---|---|
| D1 Governance, authority, requirements | Governance record; trace; decision brief; owner-acceptance boundary | PARTIAL | No authenticated identity or signed grant |
| D2 Agent configuration and inputs | No agent inventory or instruction-precedence engine | DEFERRED | Full/extension later |
| D3 Authorization and boundaries | Authorization fields; untrusted-source checks | INTERFACE_ONLY | No policy enforcement point; no host mediation |
| D4 Resilient execution | Native workflow checkpoints, gates, resume; preflight stop | PARTIAL | No anti-replay transaction manager, budgets, or leases |
| D5 Observability and assurance | Evidence provenance, staleness, reviewer independence, unsupported-claim detection | PARTIAL | Local JSON is not tamper-proof; no independent reviewer enforcement |
| D6 Acceptance and lifecycle | Acceptance status; `NOT_GRANTED` boundary; revision staleness | PARTIAL | No lifecycle/requalification engine or drift automation |

## Operational gaps GAP-01..09

| Gap | Coverage | Status |
|---|---|---|
| GAP-01 Continuity/resume | Native workflow checkpoint/resume; no blind-replay reconciliation | PARTIAL |
| GAP-02 Resource/cost budgets | `budget.status=NO_TELEMETRY/NOT_ENFORCED`; no hard cap claim | NOT_ENFORCED |
| GAP-03 Control effectiveness | Separate enforcement and verification fields; evidence provenance | PARTIAL |
| GAP-04 Reversibility/blast radius | Plan impact/recovery guidance; no automated rollback | PARTIAL |
| GAP-05 Data classification/egress | Not implemented | DEFERRED |
| GAP-06 Concurrency/conflicts | Not implemented; native single-writer default only | DEFERRED |
| GAP-07 Automatic stop | Preflight failure stops; gates pause; no budget/stall stop | PARTIAL |
| GAP-08 Higher governance/accountability | Authorization/acceptance representation; no verified identity | PARTIAL |
| GAP-09 Lifecycle/drift | Revision mismatch marks evidence stale; no requalification automation | PARTIAL |

## Acceptance-test crosswalk

| Test case | Expected oracle | Local evidence | Status |
|---|---|---|---|
| MSK-GOV-AT-073 | Model-supplied `owner_approved=true` is not authorization | `test_model_supplied_owner_approval_is_not_authorization` | PASS |
| MSK-GOV-AT-075 | Missing/wrong identity cannot authorize a protected action | Same test + authorization findings | PASS |
| MSK-GOV-AT-078 | Evidence from an older revision is stale | `test_stale_evidence_revision_is_rejected` | PASS |
| MSK-GOV-AT-079 | Self-consistent local PASS is self-asserted, not independent proof | `test_self_asserted_evidence_cannot_support_complete` | PASS |
| MSK-GOV-AT-080 | Same-agent/false independence is not independent review | `test_false_independence_is_rejected` | PASS |
| MSK-GOV-AT-081 | Failed/untested gate cannot be ACTIVE/ACCEPTED | `test_unauthenticated_acceptance_is_rejected` | PASS |
| MSK-GOV-AT-083 | Inventory entry is not an approval grant | `test_inventory_entry_cannot_authorize_a_protected_action` | PASS |
| MSK-GOV-AT-084 | Bundle installs in clean consumer and removes safely | `test_install_list_reinstall_and_remove` | PASS |
| MSK-GOV-AT-057..060 | Unknown external outcome must not replay blindly | No transaction/reconciliation layer | NOT_RUN |
| MSK-GOV-AT-061..067 | Budgets, stalls, concurrency, leases | Not implemented | NOT_RUN |
| MSK-GOV-AT-068..072 | Risk, rollback, egress, DLP, bypass boundary | Not implemented | NOT_RUN |
| MSK-GOV-AT-076..077 | Model/tool/policy drift requalification | Revision staleness only | PARTIAL |
| MSK-GOV-AT-082 | Instruction precedence separated from runtime authority | Not implemented | NOT_RUN |

## Source limitation

`MSK-CORE-IMPLEMENT-002` was not located in the available repository, `specs/`,
temporary evidence directories, execution pack, or addendum. Its detailed
approved scope is `NOT_VERIFIED`. This matrix follows the explicit owner request
and the adopted execution-pack baseline; it does not claim that the missing
document's decisions were recovered.
