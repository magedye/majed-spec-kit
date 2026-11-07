"""Prepare a genuine project editable wheel using isolated offline build tools."""
from recover_environment import ROOT,LOCAL,REPORT,PYTHON,UV,dump,sha
from datetime import datetime,timezone
import json
import os
import subprocess
import tomllib

def main():
    report=REPORT/'project-install-001'
    report.mkdir(exist_ok=False)
    spec=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))
    assert spec['build-system']['build-backend']=='hatchling.build'
    requirements=report/'build-requirements.in'
    requirements.write_text('\n'.join(spec['build-system']['requires'])+'\n',encoding='utf-8')
    state={'started_at_utc':datetime.now(timezone.utc).isoformat(),'basis':'Declared pyproject hatchling backend; required public CLI entrypoint missing in fresh-process tests',
        'spec_sha256':sha(ROOT/'pyproject.toml'),'source_candidate':'10b5862f6905e62eaef0983418cb9567b1b8a8d6',
        'commands':[],'network':False,'pytest_environment_modified':False}
    env={k:v for k,v in os.environ.items() if not(k.startswith(('UV_','PIP_','PYTHON')) or k in ['VIRTUAL_ENV','CONDA_PREFIX'])}
    env.update(UV_OFFLINE='1',UV_PYTHON_DOWNLOADS='never',UV_NO_CONFIG='1',UV_DEFAULT_INDEX='https://pypi.org/simple',UV_KEYRING_PROVIDER='disabled',PYTHONDONTWRITEBYTECODE='1')
    def run(label,argv):
        r=subprocess.run([str(a) for a in argv],cwd=ROOT,env=env,capture_output=True)
        (report/(label+'.stdout.txt')).write_bytes(r.stdout)
        (report/(label+'.stderr.txt')).write_bytes(r.stderr)
        state['commands'].append({'label':label,'argv':[str(a) for a in argv],'exit_code':r.returncode})
        dump(report/'receipt.json',state)
        return r.returncode
    lock=report/'build-requirements.txt'
    base=[UV,'--offline','--no-config','--no-python-downloads']
    if run('compile',[*base,'pip','compile',requirements,'--python',PYTHON,'--default-index','https://pypi.org/simple','--generate-hashes','--output-file',lock]):
        state['result']='OFFLINE_BUILD_DEPENDENCY_UNAVAILABLE'
    else:
        venv=LOCAL/'project-build-venv'
        assert not venv.exists()
        if run('venv',[PYTHON,'-I','-m','venv','--without-pip',venv]):state['result']='BUILD_ENV_CREATION_BLOCKED'
        elif run('install-build-tools',[*base,'pip','install','--python',venv/'Scripts/python.exe','--default-index','https://pypi.org/simple',
                    '--require-hashes','--only-binary',':all:','--strict','--link-mode','copy','-r',lock]):state['result']='OFFLINE_BUILD_DEPENDENCY_UNAVAILABLE'
        else:
            wheels=LOCAL/'project-editable-wheel'
            wheels.mkdir(exist_ok=False)
            code='from hatchling.build import build_editable; print(build_editable('+repr(str(wheels))+'))'
            if run('build-editable',[venv/'Scripts/python.exe','-I','-B','-c',code]):state['result']='EDITABLE_BUILD_BLOCKED'
            else:
                artifacts=list(wheels.glob('*.whl'))
                assert len(artifacts)==1
                state.update(result='EDITABLE_WHEEL_READY_INSTALL_AFTER_ACTIVE_TESTS_FINISH',artifact=str(artifacts[0]),artifact_sha256=sha(artifacts[0]))
    state['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    dump(report/'receipt.json',state)
    print(json.dumps(state))

if __name__=='__main__':main()
