# majed-controlled workflow

A native Spec Kit workflow for profile-routed delivery with a deterministic
governance preflight, derived evidence capture, checkpointed review gates, and
a separate owner-acceptance boundary.

## Inputs

| Input | Values | Meaning |
|---|---|---|
| `task` | text | The task or decision to execute |
| `profile` | `quick`, `standard`, `controlled` | Routing and applicable checks |
| `mode` | `assess`, `execute` | `assess` runs preflight + gates; `execute` runs the SDD command route |
| `integration` | integration id or `auto` | Agent integration for command steps |
| `evidence_path` | path | Governance record; required for `controlled` |
| `review_verdict` | `approve`, `reject`, `pending`, empty | Review gate input |
| `accept_verdict` | `accept`, `pending`, `reject`, empty | Owner-acceptance gate input; a gate choice is not authenticated acceptance |

## Routes

- **quick**: `specify` → `implement` → acceptance gate.
- **standard**: `specify` → review gate → `plan` → `tasks` → `implement` → acceptance gate.
- **controlled**: `specify` → review gate → `clarify` → `plan` → review gate →
  `tasks` → `analyze` → `implement` → acceptance gate.
- **assess**: preflight → evidence record → review gate → acceptance gate → close.

The workflow uses the native engine. It does not implement a second engine,
retry loop, task store, or approval server.

## Run locally

```bash
specify workflow add --dev ./workflows/majed-controlled
specify workflow run majed-controlled \
  --input task="Add a bounded feature" \
  --input profile=controlled \
  --input mode=assess \
  --input evidence_path=.specify/governance/record.json \
  --input review_verdict=approve \
  --input accept_verdict=pending
```

Or run the local YAML directly:

```bash
specify workflow run ./workflows/majed-controlled/workflow.yml --input task="..." --input profile=quick
```

The deterministic bridge is installed by the `majed-governance` extension at
`.specify/extensions/majed-governance/scripts/python/workflow_bridge.py`. This
is deliberate: in the current Spec Kit release, installing a bundled workflow
copies its `workflow.yml` but not companion files from the workflow package.
The bundle installs the extension before the workflow, so the bridge is present
when the workflow runs. If you install the workflow independently, install the
governance extension first.

The first two steps enforce the dependency contract:

- `dependency-check` fails with `DEPENDENCY_MISSING` when the extension bridge
  is absent.
- `dependency-version` requires bridge version `>= 1.1.0`; an older or
  incompatible bridge fails before any governance check or command dispatch.

Mandatory governance checks therefore cannot silently pass when the extension is
missing. The shell steps use `python3`, `python`, or `py -3` in that order; the
bridge is stdlib-only.

## Execute qualification

The qualification suite exercises the real integration dispatch path with a
disposable stub CLI named `claude` on `PATH`:

- QUICK: specify + implement (2 dispatches).
- STANDARD: specify + plan + tasks + implement (4 dispatches).
- CONTROLLED: specify + clarify + plan + tasks + analyze + implement
  (6 dispatches), with a governance record.
- ASSESS: preflight, review gate, acceptance gate, evidence close.

The stub records the native command invocations and exits successfully. This
verifies routing and native dispatch mechanics, not real agent quality.
`REAL_AGENT_BEHAVIOR: NOT_VERIFIED`.

## Evidence and acceptance

The `record-preflight` shell step writes a derived JSON artifact under
`.specify/workflows/majed-controlled/evidence/<run_id>.json`. It is
`DERIVED / NON-AUTHORITATIVE`.

The `close` step records the gate choices but always sets
`owner_acceptance: NOT_GRANTED` and `authenticated: false`. A gate label,
including `accept`, is not proof of owner identity or authority.

## Limitations

- Command steps require an installed agent integration; the `assess` mode is
  fully executable without dispatching agent commands.
- Resume is native engine resume. An interrupted side effect before its
  completion checkpoint may repeat; this workflow does not add a transaction
  manager.
- The workflow cannot enforce host-wide tool, shell, or network permissions.
- The workflow does not claim independent review or owner acceptance.
