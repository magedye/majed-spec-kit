# Majed Spec Kit Core

Majed Core is an **extension-first, upstream-preserving** delivery on top of
GitHub Spec Kit. It adds behavior through native Presets, Extensions,
Workflows, and Bundles. It does not modify `src/specify_cli/`, replace upstream
templates globally, or introduce a second workflow/approval engine.

## Delivery status

`CORE_PARTIAL` — the four components are implemented and locally qualified, but
not every `CORE_REQUIRED` capability is complete and no comparative
effectiveness evaluation was performed.

This is a candidate, not an accepted or released product:

- Owner acceptance: `NOT_GRANTED`
- Policy activation: `NOT_AUTHORIZED`
- Release authorization: `NO`
- Host-wide enforcement: `NOT_IMPLEMENTED`
- Effectiveness: `EFFECTIVENESS_NOT_VERIFIED`

## Components

| Component | Native kind | Purpose |
|---|---|---|
| `majed-adeq` | Preset | ADEQ outcome, obligation, alternatives, impact, confidence, and evidence guidance |
| `majed-governance` | Extension | Deterministic governance record validation, trace view, and owner decision brief |
| `majed-controlled` | Workflow | Quick/standard/controlled routes, preflight, evidence capture, review gates, resume, and acceptance boundary |
| `majed-governed` | Bundle | Installs the three components as one local Core candidate |

## Install in an isolated consumer project

```bash
# From the Majed Spec Kit checkout:
specify bundle install ./bundles/majed-governed/bundle.yml --integration claude --offline

specify bundle list --json
specify preset info majed-adeq
specify extension info majed-governance
specify workflow info majed-controlled
```

`bundle install` initializes a clean project if needed. The local path uses the
source checkout's components and does not require an external catalog or
network access.

## Use the governance record

Copy the template and fill it with the actual revision and evidence:

```bash
cp .specify/extensions/majed-governance/templates/governance-record.json \
   .specify/governance/record.json
python .specify/extensions/majed-governance/scripts/python/governance_core.py \
  check --record .specify/governance/record.json --root . --json
```

Exit `0` is a local `PASS`; it is not owner acceptance, independent review, or
host enforcement.

## Use the controlled workflow

```bash
specify workflow run majed-controlled \
  --input task="Describe the change" \
  --input profile=controlled \
  --input mode=assess \
  --input evidence_path=.specify/governance/record.json \
  --input review_verdict=approve \
  --input accept_verdict=pending
```

`mode=assess` is executable without an agent integration. `mode=execute`
dispatches the native `speckit.specify`, `speckit.clarify`, `speckit.plan`,
`speckit.tasks`, `speckit.analyze`, and `speckit.implement` commands and
therefore requires a configured integration.

## Upgrade and removal

```bash
specify bundle install ./bundles/majed-governed/bundle.yml --refresh --offline
specify bundle remove majed-governed
```

Repeating an unchanged install preserves existing components and user edits.
Removal is ownership-aware; independently installed components and unrelated
user files remain.

## Authoritative inputs and limitations

The owner request for `MSK-EXTENSION-CORE-001` is the task authorization. The
`Majed_Spec_Kit_Execution_Pack_v1.0`, `MSK_Execution_Governance_Addendum_v1.1`,
and RCCA v1.4.0 were inspected as design references. `MSK-CORE-IMPLEMENT-002`
was **not found** in the available repository, specs, or evidence locations;
its detailed approved scope is therefore `NOT_VERIFIED`. This delivery uses the
owner request's explicit scope and the prior baseline review as the available
basis.

The branch is based on upstream `f74bdb893dcba23de72069b46ced5baaeb1684ea`.
The previous candidate `ca3233afe5192ba01861098c429effea7e6a4f6c` was inspected
as evidence and is not merged into this branch. Its Windows-only Q-03 test
fixture correction is therefore not present here; the two existing
`test_command_definition.py` composition tests still fail on Windows in this
upstream baseline. They are unrelated to the Majed components and are recorded
as a known baseline limitation.

## Documents

- [Requirements coverage](requirements-matrix.md)
- [Compatibility and limitations](compatibility-and-limitations.md)
- [Qualification evidence](qualification.md)
- [Core-to-Full roadmap](roadmap.md)
- [Engineering report](engineering-report.md)
