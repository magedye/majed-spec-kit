"""Task-local offline-only environment recovery; no dependency/spec edits."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import tomllib

ROOT = Path(r'D:\APP\maged-spec-kit\majed-spec-kit\specs\003-msk-baseline-closure\execution-worktree')
LOCAL = ROOT / 'specs/003-msk-baseline-closure/execution/environment-recovery-001'
REPORT = ROOT / 'docs/reviews/msk-baseline-closure-003/environment-recovery-001'
PYTHON = Path(r'C:\Users\Majed\AppData\Local\Programs\Python\Python312\python.exe')
UV = Path(r'C:\Users\Majed\.local\bin\uv.exe')
OWNER = Path(r'C:\Users\Majed\.codex\attachments\406eb7d1-9944-45a8-8c8c-7f29326219b5\Pasted text.txt')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    git = lambda *a: subprocess.check_output(['git', *a], cwd=ROOT, text=True).strip()
    assert git('branch', '--show-current') == 'fix/msk-baseline-closure-003-qualified'
    assert git('rev-parse', 'HEAD') == '98e6269f4112b9627f78e154cf17760d5f86f43d'
    assert not git('status', '--porcelain')
    LOCAL.mkdir(exist_ok=False)
    REPORT.mkdir(exist_ok=False)
    raw = OWNER.read_bytes()
    (REPORT / 'OWNER_ENVIRONMENT_RECOVERY_AUTHORIZATION.txt').write_bytes(raw)
    spec = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    state = {'request_id': 'MSK-BASELINE-CLOSURE-003', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
             'candidate': git('rev-parse', 'HEAD'), 'source_baseline': git('rev-parse', 'main'),
             'preserved_old_candidate': git('rev-parse', 'fix/msk-baseline-closure-003'),
             'branch': git('branch', '--show-current'),
             'authorization_sha256': hashlib.sha256(raw).hexdigest(),
             'write_set': [str(LOCAL), str(REPORT), 'existing task report/state summaries only'],
             'protected': ['all product/tests/constitution/AGENTS/dependency specifications', 'other worktree', 'earlier environments/evidence/backups'],
             'sources': {p: sha(ROOT/p) for p in ['pyproject.toml', 'AGENTS.md', 'CONTRIBUTING.md', 'SUPPORT.md', '.github/workflows/test.yml']},
             'python_constraint': spec['project']['requires-python'], 'dependencies': spec['project']['dependencies'],
             'test_dependencies': spec['project']['optional-dependencies']['test'], 'python_lockfiles': [],
             'network_authorized': False, 'installation_authorized': 'OFFLINE_VERIFIED_LOCAL_RESOURCES_ONLY',
             'qualified_environment': False, 'commands': []}
    env = {k:v for k,v in os.environ.items() if not (k.startswith(('UV_', 'PIP_', 'PYTHON')) or k in ['VIRTUAL_ENV','CONDA_PREFIX'])}
    env.update({'UV_OFFLINE':'1', 'UV_PYTHON_DOWNLOADS':'never', 'UV_NO_CONFIG':'1',
                'UV_DEFAULT_INDEX':'https://pypi.org/simple', 'UV_KEYRING_PROVIDER':'disabled',
                'PIP_NO_INDEX':'1', 'PIP_DISABLE_PIP_VERSION_CHECK':'1', 'PYTHONDONTWRITEBYTECODE':'1'})
    def run(label, args, timeout=90):
        start = datetime.now(timezone.utc).isoformat()
        r = subprocess.run([str(a) for a in args], cwd=ROOT, env=env, capture_output=True, timeout=timeout)
        for kind, data in [('stdout',r.stdout),('stderr',r.stderr)]:
            (REPORT/(label+'.'+kind+'.txt')).write_bytes(data)
        state['commands'].append({'label':label, 'argv':[str(a) for a in args], 'started_at_utc':start,
                                  'exit_code':r.returncode, 'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),
                                  'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})
        dump(REPORT/'recovery-state.json',state)
        return r
    run('python-version',[PYTHON,'-I','-c','import sys,json;print(json.dumps({"version":sys.version,"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix}))'])
    run('uv-version',[UV,'--version'])
    state['uv_executable_sha256'] = sha(UV)
    state['python_executable_sha256'] = sha(PYTHON)
    state['environment'] = str(LOCAL/'venv')
    state['previous_nonqualified_environment_preserved'] = {'path':str(ROOT/'.venv'), 'config_sha256':sha(ROOT/'.venv/pyvenv.cfg')}
    created = run('create-isolated-venv',[PYTHON,'-I','-m','venv','--without-pip',LOCAL/'venv'])
    if created.returncode:
        state['result']='ENVIRONMENT_CREATION_BLOCKED'
    else:
        vpython = LOCAL/'venv/Scripts/python.exe'
        run('isolated-python-probe',[vpython,'-I','-c','import sys,site,json;print(json.dumps({"version":sys.version,"executable":sys.executable,"prefix":sys.prefix,"base_prefix":sys.base_prefix,"enable_user_site":site.ENABLE_USER_SITE,"sys_path":sys.path}))'])
        cfg = (LOCAL/'venv/pyvenv.cfg').read_text()
        assert 'include-system-site-packages = false' in cfg
        state['isolated_venv_config_sha256']=sha(LOCAL/'venv/pyvenv.cfg')
        lock = REPORT/'requirements-offline.txt'
        result=run('offline-resolution',[UV,'--offline','--no-config','--no-python-downloads','pip','compile','pyproject.toml',
                    '--extra','test','--python',vpython,'--default-index','https://pypi.org/simple',
                    '--generate-hashes','--output-file',lock])
        state['result']='OFFLINE_RESOLUTION_SUCCEEDED_INSTALL_PENDING_VERIFICATION' if result.returncode==0 else 'OFFLINE_DEPENDENCIES_UNAVAILABLE'
        state['installation_performed']=False
        if lock.is_file():
            state['offline_requirements_sha256']=sha(lock)
    state['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    dump(REPORT/'recovery-state.json',state)
    print(json.dumps({'result':state['result'],'report':str(REPORT),'environment':state.get('environment'),'commands':state['commands']},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
