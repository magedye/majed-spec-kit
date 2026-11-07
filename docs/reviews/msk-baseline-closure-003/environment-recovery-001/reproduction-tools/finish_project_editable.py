"""Resolve backend-declared editable requirements offline; build owned wheel."""
from recover_environment import ROOT,LOCAL,REPORT,UV,dump,sha
from datetime import datetime,timezone
import json
import os
import subprocess

def main():
    report=REPORT/'project-install-002'
    report.mkdir(exist_ok=False)
    builder=LOCAL/'project-build-venv/Scripts/python.exe'
    state={'started_at_utc':datetime.now(timezone.utc).isoformat(),'commands':[],
       'prior_attempt':'project-install-001 backend imported editables, missing; preserve failed build and pinned build tools',
       'network':False,'pytest_environment_modified':False}
    env={k:v for k,v in os.environ.items() if not(k.startswith(('UV_','PIP_','PYTHON')) or k in ['VIRTUAL_ENV','CONDA_PREFIX'])}
    env.update(UV_OFFLINE='1',UV_PYTHON_DOWNLOADS='never',UV_NO_CONFIG='1',UV_DEFAULT_INDEX='https://pypi.org/simple',UV_KEYRING_PROVIDER='disabled',PYTHONDONTWRITEBYTECODE='1')
    def run(label,argv):
        r=subprocess.run([str(a) for a in argv],cwd=ROOT,env=env,capture_output=True)
        (report/(label+'.stdout.txt')).write_bytes(r.stdout)
        (report/(label+'.stderr.txt')).write_bytes(r.stderr)
        state['commands'].append({'label':label,'argv':[str(a) for a in argv],'exit_code':r.returncode})
        dump(report/'receipt.json',state)
        return r
    r=run('backend-declared-requires',[builder,'-I','-B','-c','import json;from hatchling.build import get_requires_for_build_editable;print(json.dumps(get_requires_for_build_editable()))'])
    assert r.returncode==0
    required=json.loads(r.stdout)
    assert required and all('editables' in text for text in required),required
    req=report/'requirements.in';req.write_text('\n'.join(required)+'\n')
    lock=report/'requirements.txt';base=[UV,'--offline','--no-config','--no-python-downloads']
    r=run('compile',[*base,'pip','compile',req,'--python',builder,'--default-index','https://pypi.org/simple','--generate-hashes','--output-file',lock])
    if r.returncode:state['result']='OFFLINE_EDITABLE_BUILD_DEPENDENCY_UNAVAILABLE'
    else:
        r=run('install-builder-requires',[*base,'pip','install','--python',builder,'--default-index','https://pypi.org/simple','--require-hashes','--only-binary',':all:','--strict','--link-mode','copy','-r',lock])
        if r.returncode:state['result']='OFFLINE_EDITABLE_BUILD_DEPENDENCY_UNAVAILABLE'
        else:
            wheels=LOCAL/'project-editable-wheel-002';wheels.mkdir(exist_ok=False)
            r=run('build-editable',[builder,'-I','-B','-c','from hatchling.build import build_editable;print(build_editable('+repr(str(wheels))+'))'])
            if r.returncode:state['result']='EDITABLE_BUILD_BLOCKED'
            else:
                artifacts=list(wheels.glob('*.whl'));assert len(artifacts)==1
                state.update(result='EDITABLE_WHEEL_READY_INSTALL_AFTER_ACTIVE_TESTS_FINISH',artifact=str(artifacts[0]),artifact_sha256=sha(artifacts[0]))
    state['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    dump(report/'receipt.json',state)
    print(json.dumps(state))

if __name__=='__main__':main()
