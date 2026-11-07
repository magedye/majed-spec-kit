# majed-adeq preset

The `majed-adeq` preset adds ADEQ decision-quality guidance to the native Spec
Kit specification, plan, task, checklist, and clarification workflows. It does
not replace those commands or introduce a second workflow engine.

## Contributions

| Native artifact | Strategy | Purpose |
|---|---|---|
| `spec-template` | append | Outcome, non-goals, assumptions, alternatives, obligation trace, evidence plan |
| `plan-template` | append | Alternatives, trade-offs, impact, recovery, confidence, evidence |
| `tasks-template` | append | Verification and evidence requirements |
| `checklist-template` | append | Decision-quality and evidence checklist |
| `speckit.clarify` | wrap | Decision-changing clarification guard around the native command |

The wrapper contains `{CORE_TEMPLATE}` so the native clarification body remains
present and authoritative. Template contributions use `append`, preserving the
upstream templates.

## Local installation

```bash
specify preset add --dev ./presets/majed-adeq --priority 5
specify preset info majed-adeq
specify preset resolve spec-template
specify preset resolve speckit.clarify
```

## Boundaries

- This preset improves instructions and document structure. It does not enforce
  tool permissions, authenticate approvals, or prove completion.
- It does not modify `src/specify_cli/` or the upstream templates.
- A rendered section is guidance, not evidence; completion still requires the
  verification described in the generated artifacts.
