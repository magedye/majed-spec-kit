---
description: "Validate source authority, revision, and content hashes"
---

# Governance Source Validation

Validate a source manifest's authority, revision, and content hashes. A source
with `UNVERIFIED` authority is reported as a limitation, not promoted.

## User Input

```text
$ARGUMENTS
```

Resolve the manifest path and project root.

## Execution

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py sources \
  --manifest .specify/governance/sources.json --root . --json
```

## Rules

- Trusted authorities (`OWNER_APPROVED`, `PROJECT_POLICY`, `REFERENCE`) need a
  64-hex SHA-256 and a non-empty revision.
- A hash mismatch or missing path is an error.
- `supersedes` must name an existing source and cannot self-reference.
- `UNVERIFIED` is a warning; do not silently treat it as approved.
