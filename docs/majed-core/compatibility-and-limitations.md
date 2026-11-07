# Compatibility and limitations

## Native compatibility

| Area | Status | Evidence |
|---|---|---|
| Preset manifest/composition | Compatible | `majed-adeq` installs and composes append/wrap contributions; preset tests pass |
| Extension manifest/install | Compatible | `majed-governance` installs from directory; extension tests pass |
| Workflow schema/engine | Compatible | Definition validates; quick/standard/controlled/assess routes; pause/resume tests pass |
| Bundle manifest/install | Compatible | `bundle validate --path` passes; clean consumer install/list/reinstall/remove pass |
| Upstream source modifications | None | No files under `src/specify_cli/` changed |
| New runtime dependencies | None | Python standard library only |

## Version constraints

- Components declare `speckit_version: ">=1.3.0"`.
- The local qualification used Spec Kit `1.3.3.dev0`, Python `3.12.10`, on
  Windows 11 (`HQ-IT-ISD6272L`).
- POSIX execution of the new tests/scripts was not run in this qualification;
  the scripts use `pathlib`, `json`, `hashlib`, and `datetime` only, and the
  workflow shell chain uses `||`, which is supported by both `sh` and `cmd`.
  Cross-platform CI remains `NOT_VERIFIED`.

## Native mechanism limits discovered

1. **Bundled workflow companion files.** The current bundled-workflow install
   path copies `workflow.yml` but not companion files from the workflow package.
   The workflow therefore calls the deterministic bridge installed by the
   `majed-governance` extension. The bundle installs the extension first. A
   standalone workflow install must install the extension first.
2. **Wheel packaging.** The local source-checkout path resolves components via
   `_locate_bundled_*`. A published wheel would need these component paths added
   to the build's force-include list. This delivery does not modify
   `pyproject.toml`; wheel distribution is `NOT_VERIFIED`.
3. **Catalog discovery.** The bundle is installable by local path. It is not
   published to an external catalog, and this qualification does not claim
   catalog precedence or historical release selection.

## Governance and host enforcement limits

- A workflow gate records a choice. It does **not** authenticate the owner,
  reviewer, or executor.
- `accept` in the workflow is recorded as a gate choice but leaves
  `owner_acceptance: NOT_GRANTED` and `authenticated: false`.
- The local JSON governance record is not tamper-proof. A self-consistent local
  checksum is `SELF_ASSERTED`, not independent operational proof.
- The extension can detect unsupported completion, stale evidence, untrusted
  authorization sources, false independence, and unsupported control claims in
  the record. It cannot prevent an agent from using another tool path.
- No Policy Enforcement Point (PEP), OS/network mediation, credential control,
  or host-wide permission gate is implemented or claimed.
- No budget/token/cost enforcement exists. The record reports
  `NO_TELEMETRY`/`NOT_ENFORCED`; no hard cap is claimed.
- No anti-replay transaction manager exists. Native workflow resume may repeat
  an interrupted side effect before its completion checkpoint.

## Baseline compatibility note

The branch is based on upstream `f74bdb893dcba23de72069b46ced5baaeb1684ea`.
The prior candidate `ca3233afe5192ba01861098c429effea7e6a4f6c` contains a
Windows portability fix for two existing `test_command_definition.py`
composition tests. That candidate was inspected as evidence and is **not
merged** here. Consequently those two existing tests still fail on Windows in
this upstream baseline. They are unrelated to the Majed components; the prior
review verified the fix in `ca3233a` (`junit-postfix3.xml`, 68 passed).

## RCCA v1.4.0 reuse

RCCA v1.4.0 is `IMPLEMENTED_CANDIDATE / NOT_ACTIVE`; its package status records
`runtime_enforcement: NOT_IMPLEMENTED`, no independent review, no owner
acceptance, and zero executed behavioral cases. This delivery reuses the
concepts of source-bound evidence, freshness, control records, and separate
enforcement/verification status. It does not vendor RCCA code, activate its
policies, or claim its tests qualify this project.

## Effectiveness

`EFFECTIVENESS_NOT_VERIFIED`. No matched upstream-vs-ADEQ-vs-Core comparative
evaluation was performed. No sample size, percentage improvement, or superiority
claim is made.
