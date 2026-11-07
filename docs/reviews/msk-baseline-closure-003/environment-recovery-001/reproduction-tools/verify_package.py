"""Documentation/preservation gate only; never turns blocked pytest into PASS."""
import csv
import hashlib
import json
import re
import subprocess

from preflight import ROOT, HERE, REPORT, ORIGINAL, write


def main():
    errors, counts = [], {}
    git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    if git('rev-parse', '--show-toplevel').replace('\\', '/') != ROOT.as_posix():
        errors.append('WRONG_WORKTREE')
    baseline = json.loads((HERE / 'BASELINE_FILE_IDENTITIES.json').read_text(encoding='utf-8'))
    for path, expected in baseline.items():
        if not (ROOT / path).is_file() or hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            errors.append('PROTECTED_SOURCE_CHANGED:' + path)
    counts['unchanged_preexisting_files'] = len(baseline)
    for path in git('diff', '--name-only', 'f74bdb8').splitlines():
        if not path.startswith('docs/reviews/msk-baseline-closure-003/'):
            errors.append('OUT_OF_DOCUMENTARY_CANDIDATE_SCOPE:' + path)
    if git('rev-parse', 'fix/msk-baseline-closure-003') != 'ca3233afe5192ba01861098c429effea7e6a4f6c':
        errors.append('ORIGINAL_CANDIDATE_CHANGED')
    # main/other active branches are observed, never written or reset by this gate.
    counts['main_current'] = git('rev-parse', 'main')
    backup = json.loads((HERE / 'PREFLIGHT.json').read_text(encoding='utf-8'))
    for row in backup['planning_files']:
        for key in ['path', 'backup']:
            if hashlib.sha256(__import__('pathlib').Path(row[key]).read_bytes()).hexdigest() != row['sha256']:
                errors.append('PLANNING_IDENTITY_CHANGED:' + key + ':' + row['path'])
    counts['planning_original_and_backup_files_verified'] = len(backup['planning_files']) * 2
    parsed = {p.name: json.loads(p.read_text(encoding='utf-8-sig')) for p in REPORT.glob('*.json')}
    identity = parsed['directive-identity.json']
    if hashlib.sha256((REPORT / identity['tracked_readable_text']).read_bytes()).hexdigest() != identity['tracked_text_sha256']:
        errors.append('TRACKED_DIRECTIVE_VIEW_HASH')
    raw = __import__('pathlib').Path(identity['raw_original']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != identity['raw_sha256']:
        errors.append('RAW_DIRECTIVE_ORIGINAL_HASH')
    source_lines = raw.decode('utf-8-sig').splitlines()
    traces = parsed['scenario-traceability.json']['records']
    if len(traces) != 24 or len({r['REQUIREMENT_ID'] for r in traces}) != 24:
        errors.append('SCENARIO_REQUIREMENT_DENOMINATOR')
    for row in traces:
        source = row['source']
        if source['exact_source_line'] != source_lines[source['line'] - 1] or source['raw_sha256'] != identity['raw_sha256']:
            errors.append('SCENARIO_SOURCE_ANCHOR:' + row['REQUIREMENT_ID'])
        if len(row['chain']) != 9 or not row['acceptance'] or not row['conditions_exceptions']:
            errors.append('INCOMPLETE_TRACE:' + row['REQUIREMENT_ID'])
        filename, pointer = row['chain']['Execution Evidence'].split('#', 1)
        value = parsed[filename]
        for part in pointer.lstrip('/').split('/'):
            value = value[int(part)] if isinstance(value, list) else value[part]
        if value['CASE_ID'] != row['case_id']:
            errors.append('WRONG_CASE_ASSOCIATION:' + row['REQUIREMENT_ID'])
    cases = parsed['dogfooding-results.json']['cases']
    if len(cases) != 9 or sum(c['RESULT'] == 'BLOCKED' for c in cases) != 7:
        errors.append('DOGFOOD_POPULATION_OR_FALSE_PASS')
    if {c['CASE_ID'] for c in cases} != {'DF-POS', *['DF-N0' + str(i) for i in range(1, 9)]}:
        errors.append('DOGFOOD_CASE_IDENTITY')
    counts['scenario_obligations'] = len(traces)
    source_checklist = parsed.get('scenario-source-coverage-checklist.json')
    if source_checklist:
        if source_checklist['unresolved_source_lines'] or len(source_checklist['units']) != 50:
            errors.append('P4_P5_SOURCE_COVERAGE_GAP')
        identifiers = {r['REQUIREMENT_ID'] for r in traces}
        for unit in source_checklist['units']:
            if unit['exact_text'] != source_lines[unit['line'] - 1] or not set(unit['requirement_refs']) <= identifiers:
                errors.append('P4_P5_SOURCE_ASSOCIATION')
        commit_boundary = next(r for r in traces if r['REQUIREMENT_ID'] == 'SG-13')
        if 'Git commit' not in commit_boundary['source']['exact_source_line'] or 'commit' not in commit_boundary['acceptance']:
            errors.append('COMMIT_NOT_ACCEPTANCE_OBLIGATION_MISSING')
        counts['P4_P5_source_nonblank_lines_accounted'] = len(source_checklist['units'])
    counts['dogfood_cases'] = {'total': len(cases), 'blocked': 7, 'limited_script_profile_passes': 2}
    qualification = parsed['qualification-results.json']
    if qualification['status'] != 'BLOCKED' or qualification['unique_case_denominator'] is not None or qualification['collection_exit_code'] != 4:
        errors.append('FALSE_QUALIFICATION_OR_DENOMINATOR')
    env = parsed['environment.json']
    counts['unmet_dependency_requirements'] = sum(not r['satisfied'] for r in env['requirements'])
    if counts['unmet_dependency_requirements'] != 8 or env['all_declared_requirements_satisfied']:
        errors.append('ENVIRONMENT_CLAIM_DRIFT')
    inventory = parsed['qualification-inventory.json']
    counts['test_module_files'] = sum(r['test_module'] for r in inventory['tracked_test_support_files'])
    counts['static_test_definitions_not_runtime_cases'] = len(inventory['static_definitions'])
    if counts['test_module_files'] != 315 or counts['static_test_definitions_not_runtime_cases'] != 7359:
        errors.append('STATIC_INVENTORY_DRIFT')
    with (REPORT / 'OWNER_DECISIONS_AR.csv').open(encoding='utf-8-sig', newline='') as f:
        decisions = list(csv.DictReader(f))
    if len(decisions) != 6 or any(r['OWNER_STATUS'] != 'PENDING' for r in decisions):
        errors.append('OWNER_ACCEPTANCE_INVENTED')
    if parsed['readiness.json']['engineering_status'] != 'PARTIAL_WITH_BLOCKERS':
        errors.append('FALSE_CLOSURE_STATUS')
    counts['pending_owner_decisions'] = len(decisions)
    for path in REPORT.glob('*.md'):
        for ref in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' not in ref and not ref.startswith('#') and not (path.parent / ref.split('#', 1)[0]).is_file():
                errors.append('BROKEN_REPORT_LINK:' + ref)
    for path in REPORT.rglob('*'):
        if path.is_file() and re.search(rb'(?:sk-[A-Za-z0-9]{24,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)', path.read_bytes()):
            errors.append('POTENTIAL_SECRET:' + str(path))
    # User wording/opaque patch bytes preserve source whitespace; their hashes
    # and patch applicability are checked separately rather than normalized.
    for cached in [False, True]:
        cmd = ['git', '-c', 'core.whitespace=cr-at-eol', 'diff', *(['--cached'] if cached else []),
               '--check', '--', '.', ':(exclude)docs/reviews/msk-baseline-closure-003/OWNER_EXECUTION_DIRECTIVE.md',
               ':(exclude)docs/reviews/msk-baseline-closure-003/AGENTS_CANDIDATE_UNAPPLIED.patch']
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True)
        if run.returncode:
            errors.append('STAGED_WHITESPACE' if cached else 'UNSTAGED_WHITESPACE')
    patch_check = subprocess.run(['git', 'apply', '--check', str(REPORT / 'AGENTS_CANDIDATE_UNAPPLIED.patch')], cwd=ROOT, capture_output=True)
    if patch_check.returncode:
        errors.append('PROTECTED_UNAPPLIED_PROPOSAL_NOT_APPLICABLE')
    counts['json_artifacts'] = len(parsed)
    result = {'result': 'PASS_IN_DOCUMENTARY_SCOPE' if not errors else 'FAIL', 'checks': counts, 'errors': errors,
        'qualification_granted': False, 'independent_review_granted': False, 'owner_acceptance': False,
        'scope': 'Preservation, declared documentary accounting/links and safe save only. All primary qualification blockers remain.'}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
