---
description: "Render a derived requirement-to-evidence traceability view"
---

# Governance Trace View

Render a derived traceability table from a project-owned JSON governance
record. The output is **DERIVED / NON-AUTHORITATIVE**; it is not a new source
of truth and does not grant approval.

## User Input

```text
$ARGUMENTS
```

Resolve the record path from the user input. If no path is supplied, use
`.specify/governance/record.json`.

## Execution

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py trace --record <record.json>
```

Use `python3`/`py -3` when `python` is not on `PATH`.

## Reporting rules

- Preserve the `DERIVED / NON-AUTHORITATIVE` label.
- Keep missing, partial, pending, and unverified items visible in the table.
- Do not infer completion from the presence of a table row.
- If an input source or revision changes, mark the affected evidence stale
  rather than presenting the view as current.
