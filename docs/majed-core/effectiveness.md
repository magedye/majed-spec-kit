# Scoped effectiveness evaluation

**Status:** `EFFECTIVENESS_NOT_VERIFIED` for behavioral/productivity outcomes.  
**Method:** deterministic structural comparison and checker detection; no agent
task comparison was run. This is not a superiority claim.

## Configurations

| Configuration | What exists |
|---|---|
| Original Spec Kit | Upstream templates, commands, workflow engine, bundles |
| Spec Kit + ADEQ | `majed-adeq` preset only |
| Integrated Majed Core | ADEQ preset + governance extension + controlled workflow + bundle |

## Structural coverage

| Measure | Original Spec Kit | Spec Kit + ADEQ | Integrated Majed Core |
|---|---:|---:|---:|
| ADEQ decision sections in the effective spec template | 0/6 | 6/6 | 6/6 |
| ADEQ plan sections (alternatives, impact/recovery, confidence, evidence) | 0/4 | 4/4 | 4/4 |
| Governance commands | 0 | 0 | 8 |
| Controlled workflow routes | 0 | 0 | 4 (quick/standard/controlled/assess) |
| Scoped `CORE_REQUIRED` requirements verified | 0/12 | Not applicable | 12/12 (see limitations) |

The 6/6 and 4/4 figures are asserted by the preset tests; they measure template
structure, not agent output quality.

## Detection effectiveness (synthetic fixtures)

Five negative governance records were used as deterministic fixtures:

| Fixture | Expected detection | Result |
|---|---|---|
| `COMPLETE` with no evidence | `UNSUPPORTED_COMPLETION` | PASS |
| `COMPLETE` with only self-asserted evidence | `SELF_ASSERTED_COMPLETION` | PASS |
| Evidence from an older revision | `STALE_EVIDENCE` | PASS |
| Review labeled independent without independence | `FALSE_INDEPENDENCE` | PASS |
| `ACCEPTED` without authenticated owner | `UNAUTHENTICATED_ACCEPTANCE` | PASS |

Detection rate on these five fixtures: **5/5**. This measures the checker's
rules, not real-world claim detection.

## Operational overhead

Local microbenchmark on the qualification host:

```text
1000 validate_record() calls
0.0455 seconds total
0.0455 ms per check
```

This excludes process startup, filesystem I/O, agent execution, and workflow
command dispatch. It is not a product latency claim.

## Rework and agent behavior

`NO_TELEMETRY`. No matched agent tasks, holdout, token/cost meter, or rework
measurement were available. Therefore:

- no claim that Majed Core produces better requirements;
- no claim that it reduces rework;
- no claim that it reduces operational cost;
- no claim of comparative superiority.

## Sample and limitations

- 3 configurations (structural only).
- 5 synthetic detection fixtures.
- 0 agent tasks, 0 holdout tasks.
- 1 host, Windows 11, Python 3.12.10.
- No independent review or owner acceptance.

**Conclusion:** the Core demonstrates deterministic structure and detection
mechanisms, but behavioral effectiveness remains `EFFECTIVENESS_NOT_VERIFIED`.
