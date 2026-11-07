---
description: "Prepare an owner decision brief without granting acceptance"
---

# Governance Decision Brief

Prepare a concise owner decision brief from a project-owned JSON governance
record. This command **does not grant owner acceptance, release authorization,
or policy activation**.

## User Input

```text
$ARGUMENTS
```

Resolve the record path from the user input. If no path is supplied, use
`.specify/governance/record.json`.

## Execution

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py decide --record <record.json>
```

Use `python3`/`py -3` when `python` is not on `PATH`.

## Presentation rules

- Lead with `OWNER_DECISION_REQUIRED` or `NO_OPEN_ITEMS`.
- List open requirements, authorization items, review limitations, control
  gaps, and the current acceptance status separately.
- Never convert a `PENDING` or `SELF_REVIEW` item into an approval.
- State the host-enforcement limitation: the workflow and this extension can
  record and inspect decisions, but they cannot authenticate an owner or block
  every tool path outside the governed workflow.
