# majed-governance extension

The `majed-governance` extension provides deterministic, read-only checks over a
project-owned governance record. It is a lightweight assurance layer over Spec
Kit status; it is not a second requirements, approval, or policy engine.

## Commands

| Command | Purpose |
|---|---|
| `speckit.majed-governance.check` | Validate a record; report unsupported completion, stale evidence, authorization, review, control, and budget findings |
| `speckit.majed-governance.trace` | Render a derived requirement-to-evidence traceability view |
| `speckit.majed-governance.decide` | Prepare an owner decision brief without granting acceptance |

The commands invoke `scripts/python/governance_core.py`, which uses only the
Python standard library.

## Record model

The record is a JSON document with:

- `schema_version`, `record_id`, `revision`;
- `requirements[]` with source, obligation, acceptance criteria, status,
  evidence, authorization, and review;
- `controls[]` mapped to domains D1..D6 with separate
  `enforcement_type` and `verification_status`;
- `acceptance` and `budget` status.

The template is `templates/governance-record.json`; the JSON Schema is
`schemas/governance-record.schema.json`.

## Checker exit codes

- `0` — `PASS` (warnings are allowed)
- `2` — `FINDINGS` (one or more errors)
- `3` — `INVALID` (unreadable or unsupported record)

## What the checks actually prove

The checker proves that a local record is internally consistent with the rules
implemented here. It does **not** prove:

- that a human owner authored or approved a decision;
- that a reviewer was independent in an organizational sense;
- that a host tool, shell, or network path is mediated;
- that a workflow gate is an authenticated approval;
- that a local JSON file is tamper-proof.

`PASS` is not owner acceptance, release authorization, or host-wide enforcement.

## RCCA v1.4.0 reuse decision

RCCA v1.4.0 is an `IMPLEMENTED_CANDIDATE / NOT_ACTIVE` package with
`runtime_enforcement: NOT_IMPLEMENTED`, no independent review, and no owner
acceptance. This extension reuses the **concepts** of evidence freshness,
control records, and four evidence levels. It does not vendor RCCA code, activate
its policies, or claim its tests qualify Spec Kit.

## Local installation

```bash
specify extension add --dev ./extensions/majed-governance
specify extension list
```
