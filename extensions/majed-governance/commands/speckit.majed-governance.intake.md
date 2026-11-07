---
description: "Extract traceable candidate obligations from a request document"
---

# Governance Requirement Intake

Extract candidate obligations from a source request without claiming semantic
completeness. The output is a governance-record skeleton with exact source line
spans and `PENDING` candidates.

## User Input

```text
$ARGUMENTS
```

Resolve the source path and the current revision from the user input. Do not
invent a revision; use `git rev-parse HEAD` or the owner-supplied revision.

## Execution

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py intake \
  --source <request.md> \
  --revision <revision> \
  --record-id MSK-INTAKE-001 \
  --output .specify/governance/record.json --json
```

Use `python3`/`py -3` when `python` is not on `PATH`.

## Reporting rules

- Report the candidate count and the exact source file/revision.
- Treat every candidate as `PENDING`; extraction is not requirement approval.
- Add acceptance criteria, component/test links, and evidence before claiming
  completion.
- If no normative candidates are found, report `NO_CANDIDATES`; do not invent
  requirements to make the record non-empty.
