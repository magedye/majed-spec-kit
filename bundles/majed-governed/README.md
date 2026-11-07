# majed-governed bundle

Majed Governed Core packages three native Spec Kit components:

| Component | Kind | Version |
|---|---|---|
| `majed-adeq` | preset | 1.0.0 |
| `majed-governance` | extension | 1.0.0 |
| `majed-controlled` | workflow | 1.0.0 |

The bundle does not add runtime behavior of its own. Each component is
installed through its native Spec Kit machinery.

## Install from a local checkout

```bash
# In a disposable consumer project, or let the CLI initialize one:
specify bundle install ./bundles/majed-governed/bundle.yml --integration claude --offline
specify bundle list --json
```

The source-checkout components are resolved from `presets/majed-adeq`,
`extensions/majed-governance`, and `workflows/majed-controlled`. No external
catalog or network access is required for this local path.

The workflow depends on the governance extension's deterministic bridge
(`workflow_bridge.py`). The bundle installs the extension before the workflow;
install the extension first if you install the workflow independently. This is
required because the current bundled-workflow path copies only `workflow.yml`,
not companion files from the workflow package.

## Use

```bash
specify preset info majed-adeq
specify extension info majed-governance
specify workflow info majed-controlled
specify workflow run majed-controlled \
  --input task="Describe the change" \
  --input profile=controlled \
  --input mode=assess \
  --input evidence_path=.specify/governance/record.json
```

The workflow's `assess` mode runs without dispatching agent commands. The
`execute` mode requires an installed agent integration.

## Upgrade and removal

```bash
# Re-apply owned components from a revised local source:
specify bundle install ./bundles/majed-governed/bundle.yml --refresh --offline

# Remove only components contributed by this bundle:
specify bundle remove majed-governed
```

Repeating an unchanged install preserves existing components and user edits.
Removal is ownership-aware and leaves independently installed components and
unrelated user files in place.

## Compatibility and limits

- Requires Spec Kit `>=1.3.0`.
- Local source-checkout installation works without wheel force-include changes.
  A future published wheel must add these paths to the build's force-include
  list before claiming wheel-bundled distribution.
- The bundle records governance decisions and evidence; it does not authenticate
  an owner, activate RCCA policies, or enforce host-wide tool/network permissions.
- `EFFECTIVENESS_NOT_VERIFIED`: no comparative upstream-vs-ADEQ-vs-Core
  measurement was performed in this qualification.
