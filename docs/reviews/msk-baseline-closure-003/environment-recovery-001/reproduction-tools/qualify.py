"""Actual local qualification attempts; no installs, waivers or fake node IDs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import tomllib

from preflight import ROOT, HERE, REPORT, write


def capture(name, argv, timeout=60):
    folder = HERE / name
    folder.mkdir(exist_ok=False)
    env = dict(os.environ)
    env.update({'PYTHONPATH': str(ROOT / 'src') + os.pathsep + str(ROOT),
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1',
                'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'})
    started = datetime.now(timezone.utc).isoformat()
    try:
        run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
        code, stdout, stderr = run.returncode, run.stdout, run.stderr
        process_status = 'FINISHED'
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = None, exc.stdout or b'', exc.stderr or b''
        process_status = 'TIMED_OUT'
    (folder / 'stdout.txt').write_bytes(stdout)
    (folder / 'stderr.txt').write_bytes(stderr)
    result = {'run_id': name, 'command': argv, 'started_at_utc': started,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'exit_code': code,
        'process_status': process_status, 'candidate': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'cwd': str(ROOT), 'stdout': str(folder / 'stdout.txt'), 'stderr': str(folder / 'stderr.txt'),
        'pythonpath': env['PYTHONPATH'], 'plugin_autoload': 'DISABLED_TO_AVOID_UNRELATED_HOST_PLUGINS',
        'source_files_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in ['pyproject.toml', 'src/specify_cli/events/__init__.py', 'tests/conftest.py']}}
    write(folder / 'RESULT.json', result)
    print(json.dumps({'run': name, 'exit_code': code, 'process_status': process_status}))
    return result


def main():
    py = str(ROOT / '.venv/Scripts/python.exe')
    assert Path(py).is_file() and Path(py).resolve().is_relative_to(ROOT.resolve())
    probe = '''import sys,json,importlib.metadata,tomllib
from packaging.requirements import Requirement
from pathlib import Path
requirements=tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
rows=[]
for raw in requirements["project"]["dependencies"]+requirements["project"]["optional-dependencies"]["test"]:
 r=Requirement(raw)
 try:observed=importlib.metadata.version(r.name)
 except importlib.metadata.PackageNotFoundError:observed=None
 rows.append({"requirement":raw,"observed":observed,"satisfied":observed is not None and r.specifier.contains(observed)})
print(json.dumps({"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,"version":sys.version,"requirements":rows,"all_declared_requirements_satisfied":all(r["satisfied"] for r in rows)}))
'''
    environment = capture('environment-001', [py, '-B', '-c', probe])
    assert environment['exit_code'] == 0
    observed = json.loads((HERE / 'environment-001/stdout.txt').read_text(encoding='utf-8'))
    write(REPORT / 'environment.json', observed)
    collection = capture('collection-001', [py, '-B', '-m', 'pytest', 'tests', '--collect-only', '-q', '-p', 'no:cacheprovider'])
    inventory = json.loads((REPORT / 'qualification-inventory.json').read_text(encoding='utf-8'))
    inventory['runtime_collection_status'] = 'BLOCKED' if collection['exit_code'] else 'COLLECTED_REQUIRES_NODE_ID_EXTRACTION'
    inventory['collection_attempt'] = collection
    inventory['environment_qualified'] = observed['all_declared_requirements_satisfied']
    inventory['blocked_reason'] = 'Missing readchar prevents actual specify_cli import; missing/older declared packages independently invalidate qualification environment. Do not stub imports, weaken requirements or install from external services.'
    write(REPORT / 'qualification-inventory.json', inventory)
    write(REPORT / 'qualification-results.json', {
        'status': 'BLOCKED', 'historical': 'HISTORICAL_EVIDENCE_UNAVAILABLE',
        'candidate': collection['candidate'], 'environment': observed,
        'mandatory_test_files': sum(r['test_module'] for r in inventory['tracked_test_support_files']),
        'unique_collected_test_ids': None, 'unique_case_denominator': None,
        'passed': None, 'failed_product_tests': None, 'skipped': None,
        'collection_exit_code': collection['exit_code'], 'execution_results_not_fabricated': True,
        'affected_suites': ['tests/specify_cli/events/test_events.py', 'tests/integrations/test_integration_generic.py',
                            'tests/specify_cli/workflows/test_command_definition.py'],
        'action': 'Use a verified existing compliant MSK environment or separately authorize dependency provisioning; then collect and run the mandatory/affected population. No full-suite PASS.'})


if __name__ == '__main__':
    main()
