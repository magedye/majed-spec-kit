"""Install only hash-pinned wheels, offline, into the authorized isolated env."""
from recover_environment import ROOT, LOCAL, REPORT, UV, dump, sha
from datetime import datetime, timezone
import json
import os
import subprocess

def main():
    state=json.loads((REPORT/'recovery-state.json').read_text(encoding='utf-8'))
    assert state['result']=='OFFLINE_RESOLUTION_SUCCEEDED_INSTALL_PENDING_VERIFICATION'
    lock=REPORT/'requirements-offline.txt'
    assert sha(lock)==state['offline_requirements_sha256']
    python=LOCAL/'venv/Scripts/python.exe'
    env={k:v for k,v in os.environ.items() if not(k.startswith(('UV_','PIP_','PYTHON')) or k in ['VIRTUAL_ENV','CONDA_PREFIX'])}
    env.update({'UV_OFFLINE':'1','UV_PYTHON_DOWNLOADS':'never','UV_NO_CONFIG':'1',
        'UV_DEFAULT_INDEX':'https://pypi.org/simple','UV_KEYRING_PROVIDER':'disabled',
        'PIP_NO_INDEX':'1','PYTHONDONTWRITEBYTECODE':'1'})
    argv=[str(UV),'--offline','--no-config','--no-python-downloads','pip','install',
          '--python',str(python),'--default-index','https://pypi.org/simple','--require-hashes',
          '--only-binary',':all:','--link-mode','copy','--strict','-r',str(lock)]
    receipt={'started_at_utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'network_allowed':False}
    r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=120)
    for label,data in [('stdout',r.stdout),('stderr',r.stderr)]:
        (REPORT/('offline-install.'+label+'.txt')).write_bytes(data)
        receipt[label+'_sha256']=__import__('hashlib').sha256(data).hexdigest()
    receipt.update(exit_code=r.returncode,finished_at_utc=datetime.now(timezone.utc).isoformat())
    state.update(installation_performed=r.returncode==0,qualified_environment=False,
                 result='INSTALLED_PENDING_DEPENDENCY_AND_RECORD_VERIFICATION' if r.returncode==0 else 'OFFLINE_INSTALL_BLOCKED')
    dump(REPORT/'offline-install.json',receipt)
    dump(REPORT/'recovery-state.json',state)
    print(json.dumps({'result':state['result'],'exit_code':r.returncode,'stderr':r.stderr.decode(errors='replace')}))

if __name__=='__main__':
    main()
