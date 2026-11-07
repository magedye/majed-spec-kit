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
| Branch | `feat/msk-extension-core-002` |
| Delivery baseline | `ba397542684da2b2d1fe00bbca05cf3911136237` |

## Focused Majed tests

```text
python -m pytest \
  tests/specify_cli/presets/test_majed_adeq_preset.py \
  tests/extensions/test_majed_governance.py \
  tests/extensions/test_majed_governance_completion.py \
  tests/specify_cli/workflows/test_majed_controlled_workflow.py \
  tests/specify_cli/workflows/test_majed_execute_dispatch.py \
  tests/specify_cli/bundles/test_majed_governed_bundle.py \
  -q -p no:cacheprovider
```

Result:

```text
collected 54 items
54 passed in 37.93s
```

This covers:

- ADEQ append/wrap composition and preservation;
- intake source spans, linkage, impact, rollback, sources, converge, metrics;
- unsupported completion, self-assertion, stale evidence, false independence,
  untrusted/expired authorization, duplicate evidence, control links,
  acceptance/open-requirement consistency;
- quick/standard/controlled/assess routing;
- native command dispatch through a disposable `claude` stub CLI (2/4/6 calls);
- workflow gates, pause, resume, missing-extension and incompatible-version
  failure behavior;
- bundle manifest resolution, artifact build/install, repeat install, refresh,
  user-file preservation, and removal.

## Regression suites

| Suite | Result |
|---|---|
| `tests/contract` | 170 passed |
| `tests/specify_cli/presets` | 763 passed |
| `tests/specify_cli/extensions` | 236 passed, 10 skipped |
| `tests/specify_cli/bundles` | 1272 passed, 4 skipped |
| `tests/specify_cli/workflows/test_command_definition.py` | 66 passed, 2 failed (known baseline) |

The two failures are the pre-existing upstream Windows Q-03 fixture issue:

```text
test_same_call_bound_per_fan_out_item
test_same_call_bound_per_loop_iteration
```

They are unrelated to the Majed components. The prior review verified the
test-only correction in `ca3233a`; that candidate was not merged here.

## Bundle artifact and consumer qualification

```text
specify bundle build --path ./bundles/majed-governed --output ./dist
specify bundle install ./dist/majed-governed-1.1.0.zip --integration claude --offline
```

The artifact install test passed in a clean consumer. The consumer demo also
installed from `bundle.yml` and ran:

| Run | Result |
|---|---|
| QUICK `mode=execute` | completed; 2 stub dispatches (specify, implement) |
| STANDARD `mode=execute` | completed; 4 stub dispatches (specify, plan, tasks, implement) |
| CONTROLLED `mode=execute` | completed; 6 stub dispatches (specify, clarify, plan, tasks, analyze, implement) |
| QUICK `mode=assess` | completed; review + acceptance gates + close |
| CONTROLLED `mode=assess` | completed; preflight + evidence + gates + close |

Example dispatch log:

```text
-p /speckit-specify Bundle-installed standard dispatch
-p /speckit-plan Bundle-installed standard dispatch
-p /speckit-tasks Bundle-installed standard dispatch
-p /speckit-implement Bundle-installed standard dispatch
```

The stub verifies native integration dispatch mechanics. Real agent behavior is
`EXECUTE_NOT_VERIFIED`.

## Dependency contract

| Check | Result |
|---|---|
| Bundle plans extension before workflow | PASS (`test_manifest_is_structurally_valid...`) |
| Missing extension fails before preflight | PASS; `dependency-check` reports `DEPENDENCY_MISSING` |
| Incompatible bridge version fails | PASS; `dependency-version` reports `compatible: false` |
| Extension removed while workflow remains | Workflow fails at `dependency-check` with exit 1 |
| Bundle removal | PASS; user file preserved; owned components removed |

## Packaging limits

- Local source-checkout install: PASS.
- Bundle artifact build/install: PASS.
- Wheel-installed CLI without the component force-include: `NOT_VERIFIED`.
- Catalog-based distribution: `NOT_VERIFIED`.
- Upstream packaging proposal is documented in
  [compatibility-and-limitations.md](compatibility-and-limitations.md).

## Effectiveness

- Checker microbenchmark: 1000 `validate_record()` calls in 0.0455s
  (0.0455 ms/check on this host).
- Synthetic negative detection: 5/5.
- Behavioral/agent comparison: `EFFECTIVENESS_NOT_VERIFIED`.
- No rework, token, cost, or agent-quality measurement was possible.

## Not verified

- POSIX execution of the new scripts/tests.
- CI matrix, Python 3.11/3.13–3.15.
- Published wheel and catalog install.
- Real agent behavior and output quality.
- Independent review and owner acceptance.
