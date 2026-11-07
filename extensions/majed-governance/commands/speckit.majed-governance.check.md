---
description: "Validate a governance record and report unsupported claims"
---

# Governance Record Check

Validate a project-owned JSON governance record. This command is **read-only**:
it does not edit the record, authenticate an owner, or enforce host permissions.

## User Input

```text
$ARGUMENTS
```

Resolve the record path from the user input. If no path is supplied, use
`.specify/governance/record.json`; if that file is absent, ask for the record
path instead of inventing one.

## Execution

Run the deterministic validator from the project root:

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py check --record <record.json> --root . --json
```

Use `python3`/`py -3` when `python` is not on `PATH`. The script uses only the
Python standard library.

## Interpretation

- Exit `0`: `PASS` — no errors. Warnings may still record limitations.
- Exit `2`: `FINDINGS` — one or more errors, such as a `COMPLETE` requirement
  with no passing evidence, stale evidence, a self-asserted completion, false
  independence, untrusted authorization, or an unsupported control claim.
- Exit `3`: `INVALID` — the record cannot be read or does not match the
  supported schema.

Report the exact status, error/warning counts, and every error code. Do not
downgrade an error to a warning, and do not treat a `PASS` as owner acceptance,
release authorization, or proof of host-wide enforcement.

## Required distinctions

- A test result is not owner approval.
- A workflow gate is not authenticated identity.
- A local JSON record is not tamper-proof.
- `SELF_ASSERTED` evidence cannot by itself support `COMPLETE`.
- `SELF_REVIEW` or a same-agent review is not independent verification.
