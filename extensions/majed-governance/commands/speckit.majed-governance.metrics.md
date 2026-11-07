---
description: "Report deterministic governance record metrics"
---

# Governance Metrics

Report deterministic counts from a governance record: requirement coverage,
evidence provenance, stale/self-asserted evidence, authorization gaps, review
independence, control coverage, acceptance, and budget status.

## User Input

```text
$ARGUMENTS
```

Resolve the record path.

## Execution

```bash
python .specify/extensions/majed-governance/scripts/python/governance_core.py metrics \
  --record .specify/governance/record.json --json
```

## Rules

- These are local record metrics, not host behavior or comparative effectiveness.
- A high count is not an approval; a low count is not proof of failure.
- Report the record revision with the metrics.
- Do not use these counts to claim overall product superiority.
