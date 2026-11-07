"""Owner-authorized single-package download with exact sources and SHA256."""
from recover_environment import ROOT,LOCAL,REPORT,PYTHON,UV,dump,sha
from datetime import datetime,timezone
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlsplit
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
    report.mkdir(exist_ok=False)
    package=LOCAL/'ruff-wheelhouse'
    package.mkdir(exist_ok=False)
    authorization='Owner reply: السماح بالتنزيل المحدد لـRuff; response to explicit request for Ruff==0.15.0 from pypi.org/simple/ruff and files.pythonhosted.org only. Available chat wording, no invented submission timestamp.'
    (report/'OWNER_DOWNLOAD_AUTHORIZATION.txt').write_text(authorization+'\n',encoding='utf-8')
    state={'request_id':'MSK-BASELINE-CLOSURE-003','started_at_utc':datetime.now(timezone.utc).isoformat(),
        'authorization':authorization,'allowed_package':'ruff==0.15.0','allowed_sources':['pypi.org','files.pythonhosted.org'],
        'pytest_environment_unchanged':True,'commands':[]}
    class Redirect(HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            parsed=urlsplit(newurl)
            if parsed.scheme!='https' or parsed.hostname not in state['allowed_sources'] or parsed.username or parsed.password:
                raise ValueError('Unapproved redirect destination')
            return super().redirect_request(req,fp,code,msg,headers,newurl)
    opener=build_opener(Redirect())
    index='https://pypi.org/simple/ruff/'
    with opener.open(Request(index,headers={'Accept':'application/vnd.pypi.simple.v1+json'}),timeout=45) as response:
        raw=response.read(40_000_001)
        assert len(raw)<40_000_001
    metadata=json.loads(raw)
    filename='ruff-0.15.0-py3-none-win_amd64.whl'
    selected=[r for r in metadata['files'] if r['filename']==filename]
    assert len(selected)==1,'Exact authorized wheel not found; no version substitution'
    entry=selected[0]
    assert not entry.get('yanked')
    url=entry['url']; parsed=urlsplit(url)
    assert parsed.scheme=='https' and parsed.hostname=='files.pythonhosted.org' and not parsed.username and not parsed.password
    digest=entry['hashes']['sha256']
    assert __import__('re').fullmatch('[0-9a-f]{64}',digest)
    dump(report/'pypi-selected-artifact.json',{'index':index,'index_response_sha256':hashlib.sha256(raw).hexdigest(),
        'filename':filename,'url':url,'sha256':digest,'yanked':entry.get('yanked',False),'requires_python':entry.get('requires-python')})
    with opener.open(url,timeout=60) as response:
        wheel=response.read(40_000_001)
        assert len(wheel)<40_000_001
    assert hashlib.sha256(wheel).hexdigest()==digest,'Artifact SHA mismatch; refusing installation'
    wheelpath=package/filename
    with wheelpath.open('xb') as out:out.write(wheel)
    with zipfile.ZipFile(io.BytesIO(wheel)) as archive:
        assert archive.testzip() is None
        meta=archive.read('ruff-0.15.0.dist-info/METADATA').decode()
        assert '\nName: ruff\n' in '\n'+meta and '\nVersion: 0.15.0\n' in '\n'+meta
        assert '\nRequires-Dist:' not in meta,'Additional dependencies not authorized by single-package grant'
        verified=0
        for path,encoded,size in csv.reader(io.StringIO(archive.read('ruff-0.15.0.dist-info/RECORD').decode())):
            if encoded:
                algorithm,expected=encoded.split('=',1)
                actual=base64.urlsafe_b64encode(hashlib.new(algorithm,archive.read(path)).digest()).decode().rstrip('=')
                assert actual==expected,path
                verified+=1
    state.update(artifact_sha256=digest,download_bytes=len(wheel),wheel_RECORD_entries_verified=verified,
                 tls_default_verification=True,artifact_path=str(wheelpath))
    lock=report/'requirements.txt'
    lock.write_text('ruff==0.15.0 --hash=sha256:'+digest+'\n',encoding='utf-8')
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
        '--no-index','--find-links',package,'--require-hashes','--only-binary',':all:','--strict','--link-mode','copy','-r',lock])==0
    assert run('version',[venv/'Scripts/ruff.exe','--version'])==0
    code=run('check',[venv/'Scripts/ruff.exe','check','src','tests'])
    state.update(result='PASSED' if code==0 else 'FAILED',finished_at_utc=datetime.now(timezone.utc).isoformat(),
                 executable_sha256=sha(venv/'Scripts/ruff.exe'))
    dump(report/'receipt.json',state)
    print(json.dumps(state))

if __name__=='__main__':main()
