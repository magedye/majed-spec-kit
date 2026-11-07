# Qualification evidence

## Environment

| Item | Value |
|---|---|
| Host | `HQ-IT-ISD6272L` |
| OS | Windows 11, `10.0.26200` |
| Python | `3.12.10` |
| Spec Kit | `1.3.3.dev0` |
| Pytest | `9.2.0` |
| Repository | `D:\APP\maged-spec-kit\majed-spec-kit` |
| Branch | `feat/msk-extension-core-001` |
| Baseline | `f74bdb893dcba23de72069b46ced5baaeb1684ea` |

## Focused component tests

```text
python -m pytest \
  tests/specify_cli/presets/test_majed_adeq_preset.py \
  tests/extensions/test_majed_governance.py \
  tests/specify_cli/workflows/test_majed_controlled_workflow.py \
  tests/specify_cli/bundles/test_majed_governed_bundle.py \
  -q -p no:cacheprovider
```

Result:

```text
collected 32 items
32 passed in 19.05s
```

Coverage in this run:

- preset manifest, append composition, wrap preservation, tasks/checklist;
- governance positive path, unsupported completion, self-asserted evidence,
  stale revision, false independence, untrusted/expired authorization,
  missing control, invalid schema, trace/decision views, CLI exit codes;
- workflow definition, controlled preflight failure, quick pass, controlled
  evidence pass, pause/resume, execute-branch command structure;
- bundle manifest resolution, clean install, list, repeat install, user-file
  preservation, removal.

## Affected component, contract, and extension suite

```text
python -m pytest \
  tests/specify_cli/presets tests/specify_cli/extensions \
  tests/specify_cli/workflows tests/specify_cli/bundles \
  tests/contract tests/extensions \
  -q -p no:cacheprovider
```

Result:

```text
3999 collected
3719 passed, 278 skipped, 2 failed
```

The two failures are **pre-existing upstream baseline failures** on Windows:

```text
tests/specify_cli/workflows/test_command_definition.py::TestComposition::test_same_call_bound_per_fan_out_item
tests/specify_cli/workflows/test_command_definition.py::TestComposition::test_same_call_bound_per_loop_iteration
```

They are the known Q-03 cross-platform fixture issue (`run: 'true'` on a Windows
shell). The prior review verified the test-only correction in
`ca3233afe5192ba01861098c429effea7e6a4f6c` (`junit-postfix3.xml`, 68 passed).
That candidate is **not merged** into this branch, so the failures remain here.
They are unrelated to the Majed components; the new component tests all pass.

## Bundle validation

```text
specify bundle validate --path bundles/majed-governed
```

Result:

```text
✓ majed-governed is well-formed and valid.
exit=0
```

## Clean consumer installation and workflow demonstration

A disposable consumer project was initialized by the bundle installer with the
`claude` integration:

```text
specify bundle install ./bundles/majed-governed/bundle.yml \
  --integration claude --offline
```

Observed:

```text
✓ Workflow 'Majed Controlled Delivery' (majed-controlled) installed
✓ Installed 'majed-governed' (3 added, 0 already present).
```

A governance record was copied from the installed template and given the
baseline revision. The workflow was run in `assess` mode:

```text
specify workflow run majed-controlled \
  --input task="Demonstrate governed Core candidate" \
  --input profile=controlled \
  --input mode=assess \
  --input evidence_path=.specify/governance/record.json \
  --input review_verdict=approve \
  --input accept_verdict=pending \
  --json
```

Observed:

```json
{
  "run_id": "ce72781a",
  "workflow_id": "majed-controlled",
  "status": "completed",
  "current_step_id": "close",
  "current_step_index": 3
}
```

Evidence artifact:

```text
.specify/workflows/majed-controlled/evidence/ce72781a.json
```

The artifact records:

```json
"close": {
  "review_status": "APPROVED_SELF_ASSERTED",
  "review_independent": false,
  "gate_accept_choice": "pending",
  "acceptance_status": "PENDING",
  "owner_acceptance": "NOT_GRANTED",
  "authenticated": false
},
"owner_acceptance": "NOT_GRANTED"
```

This is the intended boundary: the gate records a choice; it does not grant
owner acceptance.

## Governance record check

```text
python .specify/extensions/majed-governance/scripts/python/governance_core.py \
  check --record .specify/governance/record.json --root . --json
```

Observed: `PASS` with three warnings (pending requirement, pending owner
acceptance, no budget telemetry). `PASS` here means the local record has no
checker errors; it is not owner acceptance.

## What is not qualified

- POSIX execution of the new scripts/tests: `NOT_VERIFIED`.
- CI matrix / Python 3.11, 3.13–3.15: `NOT_VERIFIED`.
- Published wheel force-include and catalog installation: `NOT_VERIFIED`.
- `mode=execute` agent command dispatch: structurally validated, not executed
  against a real agent in this qualification.
- Comparative effectiveness: `EFFECTIVENESS_NOT_VERIFIED`.
- Independent review and owner acceptance: `NOT_GRANTED`.
