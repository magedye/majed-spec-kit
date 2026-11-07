"""Evidence-linked P0-P9 dispositions for the existing bounded task.

No source fixes, independent approval or accepted requirements are invented.
"""
from pathlib import Path
import hashlib
import json
import subprocess

from preflight import ROOT, HERE, REPORT, ORIGINAL, write


def main():
    owner = (HERE / 'OWNER_EXECUTION_DIRECTIVE.md').read_bytes()
    policy_paths = ['AGENTS.md', 'CONTRIBUTING.md', 'SUPPORT.md', '.github/workflows/test.yml',
                    'templates/commands/plan.md', 'templates/commands/analyze.md', 'templates/commands/tasks.md',
                    'templates/tasks-template.md', 'templates/plan-template.md', 'pyproject.toml']
    source_map = [{'path': p, 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest(),
                   'revision': 'f74bdb893dcba23de72069b46ced5baaeb1684ea'} for p in policy_paths]
    constitution = ORIGINAL / '.specify/memory/constitution.md'
    source_map.append({'path': str(constitution), 'sha256': hashlib.sha256(constitution.read_bytes()).hexdigest(),
                       'role': 'OWNER_DESIGNATED_PROTECTED_CONSTITUTION; local ignored original, adoption history not inferred'})
    conflicts = [
        {'id': 'C-01', 'classification': 'APPLICATION_GAP', 'claim_kind': 'FACT_WITH_EXPLICIT_UNVERIFIED_RUNTIME',
         'sources': ['templates/commands/plan.md:64-72', 'templates/commands/analyze.md:60,102-104', str(constitution)],
         'finding': 'Planning/analyze command guidance explicitly loads and applies the constitution. No general-session automatic startup loader is established. setup_plan.py copies a template, not an LLM context or constitutional decision.',
         'runtime_status': 'NOT_VERIFIED', 'authority_conflict': 'Not proven: absence of global auto-load alone is not REAL_CONFLICT.',
         'disposition': 'Preserve constitution; qualify actual agent workflow once environment permits. Current source-script exercise does not certify all agent instruction loading.'},
        {'id': 'C-08', 'classification': 'SCOPE_DIFFERENCE', 'claim_kind': 'FACT_AND_BOUNDED_INFERENCE',
         'sources': ['templates/tasks-template.md:12', 'templates/commands/tasks.md:147', 'CONTRIBUTING.md:229-250', str(constitution)],
         'finding': 'Consumer-template optional test tasks do not waive SpecKit development positive/negative/regression requirements.',
         'runtime_status': 'NOT_VERIFIED',
         'condition': 'If a consumer constitution itself mandates tests, optional template wording cannot silently override it; actual resolution at the agent decision boundary remains unverified.',
         'disposition': 'Do not weaken development tests or amend constitution. Record conditional consumer application gap; proposed clarification only.'},
        {'id': 'C-MATRIX', 'classification': 'REAL_CONFLICT', 'claim_kind': 'FACT_OF_TEXTUAL_INCONSISTENCY_NOT_AUTHORITY_REORDER',
         'sources': [str(constitution), '.github/workflows/test.yml:29-34', 'SUPPORT.md:16-43'],
         'finding': 'Constitution declares ubuntu/windows x3.11/3.12/3.13 mandatory; CI routine selects3.13/3.14/3.15 across3OS plusUbuntu3.11, manual3.11-3.15; SUPPORT describes rolling coverage. Neither source establishes approval to waive the other.',
         'runtime_status': 'NOT_RUN', 'disposition': 'Owner/maintainer reconciliation required. No CI/config/constitution edits or matrix reduction.'},
        {'id': 'C-AGENTS', 'classification': 'DOCUMENTATION_DRIFT', 'claim_kind': 'FACT',
         'sources': ['AGENTS.md:73-76', 'CONTRIBUTING.md:280-289', 'ca3233a:AGENTS.md'],
         'finding': 'Existing candidate adds Windows virtualenv path spelling only; no authority or permission change observed in the diff.',
         'disposition': 'Protected file still excluded from this execution candidate; preserve original candidate and present separate owner proposal.'}]
    write(REPORT / 'authority-reconciliation.json', {'sources': source_map, 'cases': conflicts,
        'precedence': ['Current explicit owner bounded directive', 'Applicable repository instructions and protected constitution in their domains',
                       'Contracts and approved decisions', 'Existing plan', 'Implementation/tests/evidence', 'summaries/assumptions'],
        'no_new_authority_framework': True, 'protected_sources_changed': False,
        'runtime_gate_identity_limit': 'GateStep verdict_input is supplied data, not authenticated owner/reviewer identity; CLI process permissions are not a host PEP.'})
    findings = [
        {'FINDING_ID': 'F-WIN-LAUNCH', 'REPRODUCTION': 'bounded-diagnostics generated no-launcher/bash/sh cases; exact baseline/candidate function diff; package regression BLOCKED',
         'ROOT_CAUSE': 'On Windows baseline primary resolver returns a bare .sh path when neither bash nor sh exists; candidate returns None, matching the unchanged stdlib dispatcher.',
         'DEFECT_TYPE': 'PRODUCT_DEFECT', 'ROOT_CAUSE_EVIDENCE_LEVEL': 'SOURCE_CONFIRMED_AND_GENERATED_MIRROR_TESTED; primary package execution blocked',
         'EXISTING_PATCH': 'ca3233a:src/specify_cli/events/__init__.py', 'PROPOSED_FIX': 'Reuse existing minimal None fallback after primary positive/negative regression qualification.',
         'WRITE_SET': ['src/specify_cli/events/__init__.py', 'tests/specify_cli/events/test_events.py'],
         'ACCEPTANCE_TEST': 'Actual primary resolver with bash, only sh, neither; confinement regressions and generated parity; distinguish argv from WSL/Bash runtime.',
         'ROLLBACK': 'No patch applied here; old ca3233a branch preserved. Future reversal scoped to exact four-file change only.', 'status': 'REUSE_PENDING_QUALIFIED_ENVIRONMENT'},
        {'FINDING_ID': 'F-RICH-WRAP', 'REPRODUCTION': 'Rich14.2 Console width20 reproduces phrase split; normalized phrase preserved; other complete-test AST statements identical.',
         'ROOT_CAUSE': 'A display-width line break splits a literal substring assertion without changing the semantic error.', 'DEFECT_TYPE': 'TEST_DEFECT',
         'EXISTING_PATCH': 'ca3233a:tests/integrations/test_integration_generic.py', 'PROPOSED_FIX': 'Reuse whitespace-normalized complete message assertion; retain exit1, exact user edit and enabled registry assertions.',
         'WRITE_SET': ['tests/integrations/test_integration_generic.py'], 'ACCEPTANCE_TEST': 'Run both skills parametrizations on qualified CLI environment; no weaker assertion.',
         'ROLLBACK': 'Existing original candidate retained; no test file changed in this branch.', 'status': 'DISPLAY_CAUSE_REPRODUCED_INTEGRATION_BLOCKED'},
        {'FINDING_ID': 'F-WIN-NOOP', 'REPRODUCTION': 'Actual cmd /d /c true ->exit1; echo noop ->exit0 on this host.',
         'ROOT_CAUSE': 'POSIX-only true command is used by otherwise platform-neutral nested-workflow fixtures.', 'DEFECT_TYPE': 'TEST_DEFECT',
         'EXISTING_PATCH': 'ca3233a:tests/specify_cli/workflows/test_command_definition.py', 'PROPOSED_FIX': 'Reuse existing echo noop fixture after nested-definition regression execution.',
         'WRITE_SET': ['tests/specify_cli/workflows/test_command_definition.py'], 'ACCEPTANCE_TEST': 'Both fan-out/loop bound-call path assertions unchanged and pass; actual WorkflowEngine currently blocked.',
         'ROLLBACK': 'No source/test patch applied; preserve original candidate.', 'status': 'COMMAND_CAUSE_REPRODUCED_WORKFLOW_BLOCKED'},
        {'FINDING_ID': 'F-WIN-WSL', 'REPRODUCTION': 'No real WSL compatibility trial performed; generated tests prove selection only.',
         'ROOT_CAUSE': 'UNVERIFIED; finding a bash executable is not evidence it accepts native Windows paths.', 'DEFECT_TYPE': 'UNVERIFIED',
         'EXISTING_PATCH': 'ca3233a does not establish WSL/native Bash execution qualification.', 'PROPOSED_FIX': 'First reproduce supported launch behavior; no speculative product change or host configuration change.',
         'WRITE_SET': [], 'ACCEPTANCE_TEST': 'Separately identified native Bash/WSL runtime and path behavior under unchanged host settings.',
         'ROLLBACK': 'No changes', 'status': 'UNVERIFIED_RUNTIME_BOUNDARY'},
        {'FINDING_ID': 'F-ENV', 'REPRODUCTION': 'collection-001 exit4, actual ModuleNotFoundError readchar; environment.json lists8 unsatisfied declared requirements.',
         'ROOT_CAUSE': 'The available existing Python package set does not meet the repository package/test declaration.', 'DEFECT_TYPE': 'ENVIRONMENT_LIMITATION',
         'EXISTING_PATCH': None, 'PROPOSED_FIX': 'Verified pre-existing compliant environment, or separate explicit provisioning authorization; no stubs or requirement reductions.',
         'WRITE_SET': [], 'ACCEPTANCE_TEST': 'All declared requirements satisfied; source import rooted in this worktree; successful complete collection before suite outcomes.',
         'ROLLBACK': 'Own .venv may be retained; no global settings/dependencies modified.', 'status': 'BLOCKS_PRIMARY_QUALIFICATION'},
        {'FINDING_ID': 'F-CI-DOC', 'REPRODUCTION': 'authority C-MATRIX source comparison.', 'ROOT_CAUSE': 'No supersession/adoption evidence resolving differing matrix mandates.',
         'DEFECT_TYPE': 'DOCUMENTATION_DEFECT', 'EXISTING_PATCH': None, 'PROPOSED_FIX': 'Owner-reviewable governance/CI options only; do not change protected files.',
         'WRITE_SET': [], 'ACCEPTANCE_TEST': 'Explicit approved coverage policy with matching CI/docs and future actual evidence.', 'ROLLBACK': 'No changes', 'status': 'OWNER_DECISION_REQUIRED'}]
    write(REPORT / 'findings.json', {'findings': findings, 'new_product_corrections_implemented': 0,
        'why_not_duplicate_existing_fixes': 'ca3233a already contains corrections; missing primary regressions prevent claiming their qualification or committing another implementation.',
        'candidate_file_dispositions': [{'path': p, 'disposition': 'OWNER_DECISION_REQUIRED' if p == 'AGENTS.md' else 'REUSE',
            'applied_to_this_candidate': False, 'qualification': 'PROTECTED_PROPOSAL_ONLY' if p == 'AGENTS.md' else 'CONDITIONAL_ON_REQUIRED_PRIMARY_REGRESSIONS'}
            for p in ['AGENTS.md', 'src/specify_cli/events/__init__.py', 'tests/specify_cli/events/test_events.py',
                      'tests/integrations/test_integration_generic.py', 'tests/specify_cli/workflows/test_command_definition.py']]})
    dogfood = json.loads((REPORT / 'dogfooding-results.json').read_text(encoding='utf-8'))
    requirements = [
        ('Isolated non-destructive synthetic fixture', 'DF-POS'), ('Existing SpecKit mechanisms rather than new policy engine', 'DF-POS'),
        ('Explicit synthetic scope and authorization; no transfer to real authority', 'DF-POS'), ('Requirement to plan traceability', 'DF-POS'),
        ('Small controlled change within declared fixture scope', 'DF-POS'), ('Actual verification and separate review status', 'DF-POS'),
        ('Real owner acceptance remains separate from synthetic fixture or test success', 'DF-N06'),
        ('Missing or expired authorization prevents affected authorized transition', 'DF-N01'),
        ('Out-of-write-set operation rejected or actual detection level disclosed', 'DF-N02'),
        ('Unresolved authority conflict holds affected decision', 'DF-N03'),
        ('No role/permission acquired from executor-supplied values', 'DF-N04'),
        ('Implementer cannot self-grant independent review', 'DF-N05'),
        ('A passing test is not final acceptance', 'DF-N06'),
        ('Different-candidate evidence cannot qualify current candidate', 'DF-N07'),
        ('Failed mandatory gate stops subsequent save/close fixture action', 'DF-N08'),
        ('Expected oracle declared before testing each case', 'DF-POS'),
        ('Record actual input/expected/observed/result/evidence/candidate/strength', 'DF-POS'),
        ('State behavioral/detection/prevention/unknown scope honestly', 'DF-N08'),
        ('No host-wide shell/filesystem/network enforcement inferred', 'DF-N08'),
        ('Preserve all mandatory scenario obligations, conditions and unknowns', 'DF-POS'),
        ('Initial trace-method sample precedes full-population accounting without generalization', 'DF-POS'),
        ('Source authority, component, acceptance and execution evidence linked', 'DF-POS'),
        ('Do not treat model-supplied identity or approval as authenticated', 'DF-N04'),
        ('No whole-project qualification from one fixture', 'DF-POS')]
    by_id = {c['CASE_ID']: c for c in dogfood['cases']}
    traces = []
    for i, (meaning, case) in enumerate(requirements, 1):
        observed = by_id[case]
        traces.append({'REQUIREMENT_ID': f'SG-{i:02d}', 'source': 'OWNER_EXECUTION_DIRECTIVE.md#7-8',
            'source_sha256': hashlib.sha256(owner).hexdigest(), 'meaning': meaning,
            'conditions_exceptions': 'Synthetic source-script profile only; CLI/engine dependency blocker, unknown technical identity/isolation and real acceptance remain explicit.',
            'component': 'scripts/python/setup_plan.py + check_prerequisites.py and agent procedure' if case in ['DF-POS', 'DF-N08'] else 'workflows/engine.py + step/gate and agent authority procedure; runtime blocked',
            'acceptance': observed['EXPECTED'],
            'chain': {'Owner Instruction': 'OWNER_EXECUTION_DIRECTIVE.md sections7/8', 'Requirement': f'SG-{i:02d}',
                'Scope': 'write-set.json + synthetic fixture manifests only', 'Authorization': 'Final owner bounded directive; fixture identity does not grant real authority',
                'Plan': str(ORIGINAL / 'specs/003-msk-baseline-closure/plan.md'),
                'Execution Evidence': 'dogfooding-results.json#' + case,
                'Verification': 'Source-script observations only' if observed['RESULT'].startswith('PASSED') else 'BLOCKED; collection-001 exit4',
                'Review': 'PENDING_FIXED_CANDIDATE_REVIEW', 'Acceptance Status': 'NOT_GRANTED'},
            'case_id': case, 'execution_result': observed['RESULT'], 'technical_strength': observed['ENFORCEMENT_LEVEL'],
            'execution_or_acceptance_not_inferred_from_links': True})
    write(REPORT / 'scenario-traceability.json', {'population': 'All24 manually enumerated scenario obligations from owner sections7/8 in declared source-script/engine comparison scope; not allMSK requirements.',
        'denominator': len(traces), 'initial_method_sample': ['DF-N01', 'DF-N02', 'DF-N03', 'DF-N07', 'DF-N06'],
        'method_sample_execution': 'BLOCKED; method structure can be checked but no successful runtime pilot claimed',
        'full_population_accounted_after_declared_sample': True, 'records': traces, 'actual_scenario_qualification': 'PARTIAL_WITH_BLOCKERS'})
    fit = [
        ('FG01', 'Specifications/clarification/planning/tasks/analyze', 'REUSE_EXISTING', 'templates/commands and scripts/python; actual source-script setup/check exercised, LLM context/CLI not qualified'),
        ('FG02', 'Workflow pause/resume and gates', 'REUSE_EXISTING', 'Existing workflows engine/step/gate contracts; actual engine profile BLOCKED, verdict_input not authenticated authority'),
        ('FG03', 'Presets/extensions/bundles integration', 'INTEGRATE_EXISTING', 'Existing registries and package managers; no reinstall, current compliant environment needed for runtime qualification'),
        ('FG04', 'Semantic traceability and candidate evidence validity', 'UNRESOLVED', 'Scenario24 audit rows preserve gaps; no project-wide automatic fulfillment or authority engine proven'),
        ('FG05', 'Host-wide authenticated identity/authorization/enforcement', 'INTERFACE_ONLY', 'No technical boundary established by user-supplied gate verdicts or a source-script fixture'),
        ('FG06', 'Optional Full UI', 'DEFER', 'Existing planning/reference separation retained as proposal; no implementation authority'),
        ('FG07', 'Concurrent Majed governance/Core work on another branch', 'UNRESOLVED', 'Only branch/path metadata observed; outside frozen baseline source scope, not read, imported, modified, or qualified. Do not infer a need to rebuild it.')]
    write(REPORT / 'fit-gap.json', {'scope': 'f74bdb8 source baseline and historical ca3233a patch; no adoption of concurrent Core work',
        'capabilities': [{'id': i, 'capability': c, 'classification': category, 'evidence_and_limit': note,
                          'qualification': 'SCOPED_STATIC_OR_SCRIPT_EVIDENCE; no full runtime/owner acceptance'} for i, c, category, note in fit],
        'implement_required': [], 'no_unproven_redevelopment_recommended': True})
    write(REPORT / 'readiness.json', {
        'engineering_status': 'PARTIAL_WITH_BLOCKERS',
        'BASELINE_TECHNICAL_QUALIFICATION': {'status': 'BLOCKED', 'evidence': ['environment.json', 'qualification-results.json'],
            'reason': 'Primary collection blocked, unique case denominator unresolved; full matrix/CodeQL not executed; old counts unverified.'},
        'SELF_GOVERNANCE_QUALIFICATION': {'status': 'PARTIAL_WITH_BLOCKERS', 'evidence': ['dogfooding-results.json', 'scenario-traceability.json'],
            'reason': 'Actual source-script positive and local failed-prerequisite caller guard only;7negative engine/policy cases blocked. No host-wide identity/enforcement proof.'},
        'CORE_IMPLEMENTATION_READINESS': {'status': 'UNRESOLVED_NOT_APPROVED', 'evidence': ['fit-gap.json', 'authority-reconciliation.json'],
            'reason': 'No approved complete Core slice requirements/authority and qualified dependencies established; unrelated concurrent work not adopted.'},
        'OWNER_APPROVAL_STATUS': {'execution_authorization': 'GRANTED_FOR_THIS_BOUNDED_TASK', 'candidate_acceptance': 'NOT_GRANTED',
            'core_implementation': 'NOT_GRANTED', 'main_merge': 'PROHIBITED', 'push': 'PROHIBITED'},
        'independent_review': 'PENDING_FIXED_DOCUMENTARY_CANDIDATE; full qualification review blocked by missing runtime results'})
    write(REPORT / 'phase-status.json', {'request_id': 'MSK-BASELINE-CLOSURE-003', 'original_plan_preserved': True,
        'phase_dispositions': {
            'P0': 'SCOPED_CUSTODY_BACKUP_WRITESET_ESTABLISHED', 'P1': 'HISTORY_UNAVAILABLE_REPLACEMENT_COLLECTION_BLOCKED',
            'P2': 'EXISTING_PATCH_REVIEWED_BOUNDED_CAUSES_REPRODUCED_PRIMARY_REGRESSIONS_BLOCKED',
            'P3': 'STATIC_AUTHORITY_RECONCILIATION_COMPLETE_PROTECTED_DECISIONS_PENDING',
            'P4': '24OBLIGATIONS_ACCOUNTED_RUNTIME_SAMPLE_BLOCKED_NO_FULL_EXECUTION_CLAIM',
            'P5': 'SOURCE_SCRIPT_POSITIVE_AND_LOCAL_FAILURE_GATE_OBSERVED_7NEGATIVES_BLOCKED',
            'P6': 'EXACT_DOCUMENTARY_REVIEW_PENDING_FULL_TECHNICAL_REVIEW_CANNOT_CLOSE',
            'P7': 'NO_PRODUCT_SOURCE_CHANGE; source-byte validity and documentary differences recorded separately',
            'P8': 'FOUR_INDEPENDENT_JUDGMENTS_RECORDED_NO_OWNER_ACCEPTANCE',
            'P9': 'SOURCE_SCOPED_FIT_GAP_RECONCILED_NO_CORE_IMPLEMENTATION'},
        'next_action': 'Qualified MSK environment needed for primary collection/regressions and7blocked cases; continue only within current authorized bounds. No installs/main merge/push.'})
    # Retain exact known raw source proposal, without applying it.
    (REPORT / 'AGENTS_CANDIDATE_UNAPPLIED.patch').write_bytes(subprocess.check_output(
        ['git', 'diff', 'f74bdb8', 'ca3233a', '--', 'AGENTS.md'], cwd=ROOT))
    print(json.dumps({'source_dispositions': 5, 'findings': len(findings), 'authority_cases': len(conflicts),
                      'scenario_obligations': len(traces), 'fit_gap_capabilities': len(fit), 'status': 'PARTIAL_WITH_BLOCKERS'}))


if __name__ == '__main__':
    main()
