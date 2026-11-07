---
description: "Produce a bounded remediation plan for open requirements"
---

# Bounded Convergence

Produce one bounded remediation item per open requirement. This is a derived
view, not a task store and not a completion claim.

## User Input

```text
$ARGUMENTS
```

Resolve the governance record path.

## Execution

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py converge \
  --record .specify/governance/record.json --json
```

Add `--check` when the caller should receive exit `2` for open items.

## Rules

- Keep one item per requirement; do not inflate the plan.
- Use the listed bounded actions: add/refresh evidence, add trusted evidence,
  obtain authorization, obtain independent review, define acceptance criteria,
  link a component, or link tests.
- Do not mark an item complete from the existence of a remediation row.
