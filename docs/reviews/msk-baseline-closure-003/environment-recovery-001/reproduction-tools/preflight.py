"""Local execution annex for existing MSK003; no registry or policy engine."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

ORIGINAL = Path(r'D:\APP\maged-spec-kit\majed-spec-kit')
ROOT = ORIGINAL / 'specs/003-msk-baseline-closure/execution-worktree'
HERE = ROOT / 'specs/003-msk-baseline-closure/execution'
REPORT = ROOT / 'docs/reviews/msk-baseline-closure-003'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    assert ROOT.resolve().is_relative_to(ORIGINAL.resolve())
    actual = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip()
    assert Path(actual).resolve() == ROOT.resolve()
    REPORT.mkdir(parents=True, exist_ok=True)
    allowed = ['src/specify_cli/events/__init__.py', 'tests/specify_cli/events/test_events.py',
               'tests/integrations/test_integration_generic.py', 'tests/specify_cli/workflows/test_command_definition.py']
    write(REPORT / 'write-set.json', {
        'request_id': 'MSK-BASELINE-CLOSURE-003',
        'authority': 'Final owner directive830cd907 sections3/5/13; existing plan is primary, this is its execution annex',
        'worktree': str(ROOT), 'source_baseline': 'f74bdb893dcba23de72069b46ced5baaeb1684ea',
        'existing_candidate_preserved': 'ca3233afe5192ba01861098c429effea7e6a4f6c on fix/msk-baseline-closure-003',
        'source_paths_conditionally_authorized': allowed,
        'source_change_gate': 'Reproducible finding and before/after/affected verification; do not checkpoint unverified product changes',
        'report_prefix': 'docs/reviews/msk-baseline-closure-003/',
        'report_location_basis': 'CONTRIBUTING docs/ change evidence and owner section14; no parallel authority register',
        'local_evidence_prefix': str(HERE), 'local_fixture_prefix': str(HERE / 'fixtures'),
        'local_environment': 'Own .venv via stdlib venv without pip/downloads; existing packages only, exact constraints must be verified',
        'protected': ['AGENTS.md', '.gitignore', '.specify/memory/constitution.md', 'all other source/test files',
                      'remote CI/global settings', 'original candidate', 'unrelated primary worktree'],
        'main_merge': False, 'remote_push': False, 'core_implementation': False, 'new_policy_engine': False})
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    snapshot = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths if p and (ROOT / p).is_file()}
    write(HERE / 'BASELINE_FILE_IDENTITIES.json', snapshot)
    inventory, definitions = [], []
    for path in paths:
        if not (path and path.startswith('tests/') and path.endswith('.py')):
            continue
        module = Path(path).name.startswith('test_')
        inventory.append({'path': path, 'sha256': snapshot[path], 'test_module': module})
        if not module:
            continue
        tree = ast.parse((ROOT / path).read_text(encoding='utf-8-sig'), filename=path)

        def visit(nodes, parents=()):
            for node in nodes:
                if isinstance(node, ast.ClassDef):
                    visit(node.body, parents + (node.name,))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                    definitions.append({'static_definition': path + '::' + '::'.join((*parents, node.name)),
                        'line': node.lineno, 'parametrized_or_decorated': bool(node.decorator_list),
                        'node_id_expansion': 'REQUIRES_SUCCESSFUL_PYTEST_COLLECTION', 'result': 'NOT_RUN'})
        visit(tree.body)
    write(REPORT / 'qualification-inventory.json', {
        'scope': 'All tracked baseline test modules mandatory collection population; affected3 modules require execution in qualified environment. Full suite cannot pass before collection and mandatory results. CI OS/Python/security obligations separate.',
        'candidate_revision': 'f74bdb893dcba23de72069b46ced5baaeb1684ea',
        'tracked_test_support_files': inventory, 'static_definitions': definitions,
        'unique_runtime_test_denominator': None, 'runtime_collection_status': 'PENDING',
        'static_definitions_are_not_unique_parametrized_test_cases': True,
        'reported_history': 'HISTORICAL_EVIDENCE_UNAVAILABLE; unverified counts not summed'})
    (REPORT / 'OWNER_EXECUTION_DIRECTIVE.md').write_bytes((HERE / 'OWNER_EXECUTION_DIRECTIVE.md').read_bytes())
    write(HERE / 'SETUP_ATTEMPT_001.json', {'result': 'SETUP_PATH_ERROR_CORRECTED',
        'actual_error': 'FileNotFoundError: D:\\APP\\maged-spec-kit\\specs\\003-msk-baseline-closure\\execution\\BASELINE_FILE_IDENTITIES.json',
        'cause': 'Initial inline parent index selected parent directory instead of repository',
        'correction': 'Explicit repository path and resolved Git root assertions; corrected report write-set before any tests or source changes',
        'product_files_changed': False, 'failed_test_claim': False})
    print(json.dumps({'worktree': str(ROOT), 'local_evidence': str(HERE), 'tracked_files': len(snapshot),
        'test_support_files': len(inventory), 'test_modules': sum(r['test_module'] for r in inventory),
        'static_definitions': len(definitions), 'source_files_changed': 0}))


if __name__ == '__main__':
    main()
