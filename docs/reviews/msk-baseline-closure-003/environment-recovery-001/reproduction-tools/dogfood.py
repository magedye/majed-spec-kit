"""Synthetic SDD script-profile exercise; no parallel governance engine.

The CLI/engine profile and seven policy negatives remain explicitly blocked.
The fixture's owner/reviewer values are test data, never real authorization.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from preflight import ROOT, HERE, REPORT, ORIGINAL, write


def main():
    base = HERE / 'fixtures/dogfood-001'
    base.mkdir(parents=True, exist_ok=False)
    assert base.resolve().is_relative_to(HERE.resolve())
    matrix = json.loads((ORIGINAL / 'specs/003-msk-baseline-closure/planning-matrices.json').read_text(encoding='utf-8'))
    cases = matrix['dogfooding_test_plan']
    # Freeze the whole declared population and oracles before executing cases.
    write(base / 'PREDECLARED_CASES.json', {
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(), 'cases': cases,
        'additional_profile': 'Source Python setup_plan/check_prerequisites SDD route, not import-blocked CLI/WorkflowEngine',
        'positive_oracle': 'Native plan setup and required-artifact check succeed; allowed message change passes a real stdlib unittest; review and real acceptance remain distinct/PENDING.',
        'failure_gate_oracle': 'Missing tasks makes native check_prerequisites exit nonzero and check=True prevents the subsequent fixture marker.'})
    project = base / 'project'
    feature = project / 'specs/003-message'
    feature.mkdir(parents=True)
    templates = project / '.specify/templates'
    templates.mkdir(parents=True)
    for name in ['plan-template.md', 'spec-template.md', 'tasks-template.md']:
        (templates / name).write_bytes((ROOT / 'templates' / name).read_bytes())
    write(project / 'SYNTHETIC_AUTHORIZATION.json', {
        'kind': 'SYNTHETIC_TEST_DATA_NOT_REAL_AUTHORITY', 'owner': 'fixture-owner',
        'scope': ['message.py', 'test_message.py', 'specs/003-message/'],
        'real_owner_acceptance': 'NOT_GRANTED', 'independent_review': 'PENDING'})
    (feature / 'spec.md').write_text('# Fixture message\n\nFR001: message() returns after rather than before.\nSC001: stdlib unittest verifies exact result.\nNo network or project policy changes.\n', encoding='utf-8')
    write(project / '.specify/feature.json', {'feature_directory': 'specs/003-message'})
    commands = []

    def run(label, argv, check=True):
        env = dict(os.environ)
        env.update({'SPECIFY_INIT_DIR': str(project), 'SPECIFY_FEATURE_DIRECTORY': 'specs/003-message',
                    'SPECIFY_FEATURE': '003-message', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1'})
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(argv, cwd=project, env=env, capture_output=True, timeout=30)
        (base / (label + '.stdout.txt')).write_bytes(result.stdout)
        (base / (label + '.stderr.txt')).write_bytes(result.stderr)
        commands.append({'label': label, 'command': argv, 'cwd': str(project), 'exit_code': result.returncode,
                         'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat()})
        if check and result.returncode:
            raise subprocess.CalledProcessError(result.returncode, argv)
        return result

    run('native-plan-setup', [sys.executable, '-B', str(ROOT / 'scripts/python/setup_plan.py'), '--json'])
    assert (feature / 'plan.md').is_file()
    with (feature / 'plan.md').open('a', encoding='utf-8') as f:
        f.write('\n## Fixture execution binding\nFR001 -> message.py -> test_message.py. Only the listed fixture files may change. Review is pending; tests do not grant acceptance.\n')
    (feature / 'tasks.md').write_text('# Fixture tasks\n\nT001 implement FR001 only in message.py.\nT002 verify exact output via test_message.py.\nT003 preserve separate review/acceptance status.\n', encoding='utf-8')
    run('native-artifact-check', [sys.executable, '-B', str(ROOT / 'scripts/python/check_prerequisites.py'),
                                '--json', '--require-spec', '--require-tasks', '--include-tasks'])
    (project / 'message.py').write_text('def message():\n    return "before"\n', encoding='utf-8')
    (project / 'test_message.py').write_text('import unittest\nfrom message import message\n\nclass MessageTest(unittest.TestCase):\n    def test_exact_output(self):\n        self.assertEqual(message(), "after")\n', encoding='utf-8')
    before = run('fixture-regression-before', [sys.executable, '-B', '-m', 'unittest', 'test_message', '-v'], check=False)
    assert before.returncode == 1
    (project / 'message.py').write_text('def message():\n    return "after"\n', encoding='utf-8')
    run('fixture-regression-after', [sys.executable, '-B', '-m', 'unittest', 'test_message', '-v'])
    # A negative on the same supported native script profile: prerequisite
    # failure blocks this caller's next action. No claim about every shell.
    tasks = (feature / 'tasks.md').read_bytes()
    (feature / 'tasks.md').rename(feature / 'tasks-withheld.md')
    marker = project / 'must-not-run.txt'
    blocked = False
    try:
        run('native-missing-tasks-gate', [sys.executable, '-B', str(ROOT / 'scripts/python/check_prerequisites.py'),
                                        '--json', '--require-spec', '--require-tasks'])
        marker.write_text('incorrect continuation', encoding='utf-8')
    except subprocess.CalledProcessError:
        blocked = True
    assert blocked and not marker.exists()
    (feature / 'tasks-withheld.md').rename(feature / 'tasks.md')
    assert (feature / 'tasks.md').read_bytes() == tasks
    results = []
    for c in cases:
        positive = c['case_id'] == 'DF-POS'
        gate = c['case_id'] == 'DF-N08'
        results.append({'CASE_ID': c['case_id'], 'INPUT': c,
            'EXPECTED': c['oracle_ar'],
            'OBSERVED': 'Native SDD script setup/check plus actual fixture regression fail-before/pass-after; real review/acceptance PENDING.' if positive else
                        'Native missing-task prerequisite exited nonzero; caller skipped subsequent marker.' if gate else
                        'CLI/WorkflowEngine could not be imported; no runtime governance result fabricated or policy engine substituted.',
            'RESULT': 'PASSED_IN_SOURCE_SCRIPT_PROFILE' if positive or gate else 'BLOCKED',
            'EVIDENCE': str(base), 'CANDIDATE': 'f74bdb893dcba23de72069b46ced5baaeb1684ea',
            'ENFORCEMENT_LEVEL': 'BEHAVIORAL_COMPLIANCE' if positive else 'PRE_EXECUTION_ENFORCEMENT' if gate else 'NOT_VERIFIED',
            'LIMIT': 'Source-script SDD route only; WorkflowEngine profile remains BLOCKED. No host-wide scope/role/owner authentication or independent acceptance proof.'})
    write(REPORT / 'dogfooding-results.json', {'status': 'PARTIAL_WITH_BLOCKERS',
        'profile': 'CONTROLLED_SOURCE_SCRIPT_SDD_NOT_CLI_WORKFLOW_ENGINE',
        'predeclared_cases': str(base / 'PREDECLARED_CASES.json'), 'cases': results, 'actual_commands': commands,
        'fixture_result': 'one stdlib unittest failed before intended fixture change and passed after; not a SpecKit baseline test result',
        'actual_fixture_manifest': {p.relative_to(project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in project.rglob('*') if p.is_file()},
        'real_review': 'PENDING', 'real_owner_acceptance': 'NOT_GRANTED', 'import_blocker': 'collection-001/stderr.txt'})
    print(json.dumps({'source_script_positive': 'PASSED', 'local_failure_gate': 'PASSED',
                      'remaining_negative_cases': '7_BLOCKED', 'full_self_governance_qualification': 'NOT_GRANTED'}))


if __name__ == '__main__':
    main()
