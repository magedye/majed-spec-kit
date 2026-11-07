---
description: "Map changed files to components and require rollback for risky changes"
---

# Governance Impact Check

Map a changed-file set to Majed components using a project-owned impact map.
High-risk or non-reversible changes require an explicit rollback/recovery
statement.

## User Input

```text
$ARGUMENTS
```

Resolve the changed files and the rollback statement. Use `git diff --name-only`
for the affected revision when appropriate.

## Execution

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py impact \
  --map .specify/extensions/majed-governance/templates/impact-map.json \
  --files "presets/majed-adeq/preset.yml,tests/extensions/test_majed_governance.py" \
  --rollback "revert the commit and reinstall the previous bundle" \
  --json
```

## Rules

- An unmatched path is an error, not an assumed low-risk change.
- A high-risk or non-reversible change without rollback is an error.
- Multiple affected components need dependency/order notes.
- The output is derived and non-authoritative; it does not approve the change.
