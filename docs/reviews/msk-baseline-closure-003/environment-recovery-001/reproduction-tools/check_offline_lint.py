"""Exact CI-pinned Ruff in a separate, hash-verified, task-owned tool env."""
from recover_environment import ROOT,LOCAL,REPORT,PYTHON,UV,dump,sha
import os
import subprocess
import json

def main():
    report=REPORT/'lint-001'
    report.mkdir(exist_ok=False)
    inputs=report/'requirements.in'
    inputs.write_text('ruff==0.15.0\n',encoding='utf-8')
    state={'basis':'.github/workflows/test.yml exact ruff@0.15.0 CI gate',
        'first_empty_stdin_attempt':'Local lint-requirements.txt contains no dependencies, never installed or treated as a check',
        'commands':[],'network':False,'test_environment_changed':False}
    env={k:v for k,v in os.environ.items() if not(k.startswith(('UV_','PIP_','PYTHON')) or k=='VIRTUAL_ENV')}
    env.update(UV_OFFLINE='1',UV_PYTHON_DOWNLOADS='never',UV_NO_CONFIG='1',UV_DEFAULT_INDEX='https://pypi.org/simple',UV_KEYRING_PROVIDER='disabled')
    def run(label,argv):
        r=subprocess.run([str(a) for a in argv],cwd=ROOT,env=env,capture_output=True)
        (report/(label+'.stdout.txt')).write_bytes(r.stdout)
        (report/(label+'.stderr.txt')).write_bytes(r.stderr)
        state['commands'].append({'label':label,'argv':[str(a) for a in argv],'exit_code':r.returncode})
        dump(report/'receipt.json',state)
        return r.returncode
    lock=report/'requirements.txt'
    base=[UV,'--offline','--no-config','--no-python-downloads']
    if run('compile',[*base,'pip','compile',inputs,'--python',PYTHON,'--default-index','https://pypi.org/simple','--generate-hashes','--output-file',lock]):
        state['result']='OFFLINE_LINT_TOOL_UNAVAILABLE'
    else:
        state['lock_sha256']=sha(lock)
        venv=LOCAL/'lint-venv'
        assert not venv.exists()
        if run('venv',[PYTHON,'-I','-m','venv','--without-pip',venv]):state['result']='LINT_ENV_CREATION_BLOCKED'
        elif run('install',[*base,'pip','install','--python',venv/'Scripts/python.exe','--default-index','https://pypi.org/simple',
                            '--require-hashes','--only-binary',':all:','--strict','--link-mode','copy','-r',lock]):state['result']='OFFLINE_LINT_INSTALL_BLOCKED'
        else:
            run('version',[venv/'Scripts/ruff.exe','--version'])
            code=run('check',[venv/'Scripts/ruff.exe','check','src','tests'])
            state['result']='PASSED' if code==0 else 'FAILED'
            state['ruff_executable_sha256']=sha(venv/'Scripts/ruff.exe')
    dump(report/'receipt.json',state)
    print(json.dumps(state))

if __name__=='__main__':main()
