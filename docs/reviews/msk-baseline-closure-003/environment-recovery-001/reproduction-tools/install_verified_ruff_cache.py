"""Finish integrity verification from already downloaded authorized wheel only."""
from recover_environment import ROOT,LOCAL,REPORT,PYTHON,UV,dump,sha
from pathlib import PureWindowsPath
from datetime import datetime,timezone
import base64
import csv
import hashlib
import io
import json
import os
import subprocess
import zipfile

def main():
    report=REPORT/'lint-authorized-002'
    selected=json.loads((report/'pypi-selected-artifact.json').read_text())
    wheel=LOCAL/'ruff-wheelhouse'/selected['filename']
    assert sha(wheel)==selected['sha256']
    state={'request_id':'MSK-BASELINE-CLOSURE-003','started_at_utc':datetime.now(timezone.utc).isoformat(),
        'artifact':selected,'network_in_this_resume':False,'pytest_environment_unchanged':True,'commands':[],
        'prior_attempt':'Downloaded exact authorized wheel and verified advertised SHA; helper assumed POSIX RECORD names and raised KeyError on Windows backslashes before installation. Original artifact/metadata retained; no redownload.'}
    with zipfile.ZipFile(wheel) as z:
        assert z.testzip() is None
        metadata=z.read('ruff-0.15.0.dist-info/METADATA').decode()
        assert '\nName: ruff\n' in '\n'+metadata and '\nVersion: 0.15.0\n' in '\n'+metadata
        assert '\nRequires-Dist:' not in metadata
        verified=[]
        for name,encoded,size in csv.reader(io.StringIO(z.read('ruff-0.15.0.dist-info/RECORD').decode())):
            path=PureWindowsPath(name)
            assert not path.is_absolute() and not path.drive and '..' not in path.parts
            canonical=path.as_posix()
            if encoded:
                algorithm,expected=encoded.split('=',1)
                data=z.read(canonical)
                assert int(size)==len(data)
                assert base64.urlsafe_b64encode(hashlib.new(algorithm,data).digest()).decode().rstrip('=')==expected
                verified.append({'RECORD_path':name,'archive_path':canonical})
    state['verified_wheel_RECORD_entries']=verified
    lock=report/'requirements.txt'
    with lock.open('x',encoding='utf-8') as f:f.write('ruff==0.15.0 --hash=sha256:'+selected['sha256']+'\n')
    venv=LOCAL/'lint-authorized-venv'
    assert not venv.exists()
    env={k:v for k,v in os.environ.items() if not(k.startswith(('UV_','PIP_','PYTHON')) or k=='VIRTUAL_ENV')}
    env.update(UV_OFFLINE='1',UV_PYTHON_DOWNLOADS='never',UV_NO_CONFIG='1',UV_KEYRING_PROVIDER='disabled')
    def run(label,argv):
        r=subprocess.run([str(a) for a in argv],cwd=ROOT,env=env,capture_output=True)
        (report/(label+'.stdout.txt')).write_bytes(r.stdout)
        (report/(label+'.stderr.txt')).write_bytes(r.stderr)
        state['commands'].append({'label':label,'argv':[str(a) for a in argv],'exit_code':r.returncode})
        dump(report/'receipt.json',state)
        return r.returncode
    assert run('venv',[PYTHON,'-I','-m','venv','--without-pip',venv])==0
    assert run('install',[UV,'--offline','--no-config','--no-python-downloads','pip','install','--python',venv/'Scripts/python.exe',
        '--no-index','--find-links',wheel.parent,'--require-hashes','--only-binary',':all:','--strict','--link-mode','copy','-r',lock])==0
    assert run('version',[venv/'Scripts/ruff.exe','--version'])==0
    code=run('check',[venv/'Scripts/ruff.exe','check','src','tests'])
    state.update(result='PASSED' if code==0 else 'FAILED',finished_at_utc=datetime.now(timezone.utc).isoformat(),
                 executable_sha256=sha(venv/'Scripts/ruff.exe'))
    dump(report/'receipt.json',state)
    print(json.dumps({'result':state['result'],'artifact_sha256':selected['sha256'],'verified_RECORD_entries':len(verified),'exit_code':code}))

if __name__=='__main__':main()
