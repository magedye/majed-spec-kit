"""Install only genuine owned editable wheel after active qualification ends."""
from recover_environment import ROOT,LOCAL,REPORT,UV,dump,sha
from pathlib import Path
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
    previous=json.loads((REPORT/'remaining-windows-002/receipt.json').read_text())
    assert 'finished_at_utc' in previous,'Never change tested environment while the suite runs'
    built=json.loads((REPORT/'project-install-002/receipt.json').read_text())
    assert built['result']=='EDITABLE_WHEEL_READY_INSTALL_AFTER_ACTIVE_TESTS_FINISH'
    wheel=Path(built['artifact']);assert sha(wheel)==built['artifact_sha256']
    report=REPORT/'project-install-003';report.mkdir(exist_ok=False)
    with zipfile.ZipFile(wheel) as z:
        assert z.testzip() is None
        pth=[p for p in z.namelist() if p.endswith('.pth')];assert len(pth)==1
        pth_text=z.read(pth[0]).decode().strip()
        assert Path(pth_text).resolve()==(ROOT/'src').resolve(),'Editable path must reference only owned source'
        record=next(p for p in z.namelist() if p.endswith('.dist-info/RECORD'))
        checked=0
        for name,encoded,size in csv.reader(io.StringIO(z.read(record).decode())):
            if encoded:
                algorithm,digest=encoded.split('=',1);data=z.read(name.replace('\\','/'))
                assert base64.urlsafe_b64encode(hashlib.new(algorithm,data).digest()).decode().rstrip('=')==digest
                assert len(data)==int(size);checked+=1
    state={'started_at_utc':datetime.now(timezone.utc).isoformat(),'network':False,'independent_prepared_wheel_sha256':sha(wheel),
        'artifact_RECORD_entries_verified':checked,'editable_source_path':pth_text,'third_party_dependencies_changed':False,'commands':[]}
    state['installation_method']='Canonical uv editable local source install, no runtime dependency resolution; hash-pinned build constraints. Prepared wheel is independent build evidence, not falsely claimed installed artifact.'
    state['local_source_authority']='Exact owned Git source10b5862; original1017files+fourca source identities independently checked. Local source is not an unverified third-party sdist.'
    constraints=report/'build-constraints.txt'
    constraints.write_text((REPORT/'project-install-001/build-requirements.txt').read_text()+
                           '\n'+(REPORT/'project-install-002/requirements.txt').read_text(),encoding='utf-8')
    env={k:v for k,v in os.environ.items() if not(k.startswith(('UV_','PIP_','PYTHON')) or k in ['VIRTUAL_ENV','CONDA_PREFIX'])}
    env.update(UV_OFFLINE='1',UV_PYTHON_DOWNLOADS='never',UV_NO_CONFIG='1',UV_KEYRING_PROVIDER='disabled',PYTHONDONTWRITEBYTECODE='1')
    argv=[str(UV),'--offline','--no-config','--no-python-downloads','pip','install','--python',str(LOCAL/'venv/Scripts/python.exe'),
        '--no-deps','--default-index','https://pypi.org/simple','--build-constraints',str(constraints),
        '--strict','--editable',str(ROOT)]
    r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True)
    (report/'install.stdout.txt').write_bytes(r.stdout);(report/'install.stderr.txt').write_bytes(r.stderr)
    state['commands'].append({'argv':argv,'exit_code':r.returncode})
    state.update(result='INSTALLED_OWNED_EDITABLE_PROJECT' if r.returncode==0 else 'PROJECT_INSTALL_BLOCKED',
        finished_at_utc=datetime.now(timezone.utc).isoformat(),entrypoint_exists=(LOCAL/'venv/Scripts/specify.exe').exists())
    dump(report/'receipt.json',state);print(json.dumps(state))
    raise SystemExit(r.returncode)

if __name__=='__main__':main()
