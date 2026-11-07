"""Explicit recovered interpreter and candidate-pinned raw capture, no network."""
from recover_environment import ROOT,LOCAL,REPORT,dump,sha
from pathlib import Path
from datetime import datetime,timezone
import json
import os
import subprocess
import sys
import time

def main():
    run_id,*pytest_args=sys.argv[1:]
    assert __import__('re').fullmatch('[a-z0-9-]+',run_id)
    folder=REPORT/run_id
    folder.mkdir(exist_ok=False)
    verified=json.loads((REPORT/'environment-verified.json').read_text())
    assert verified['dependency_scope_verified']
    python=LOCAL/'venv/Scripts/python.exe'
    profile=LOCAL/'profiles'/run_id
    profile.mkdir(parents=True,exist_ok=False)
    external=Path(r'D:\APP\maged-spec-kit\msk003-qualification-temp-20261107-001')
    assert external.is_dir() and (external/'TASK_OWNER.json').is_file()
    probe=subprocess.run(['git','-C',str(external),'rev-parse','--show-toplevel'],capture_output=True)
    assert probe.returncode!=0,'Temporary fixtures must have no Git repository ancestor'
    temp=external/run_id
    temp.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if not(k.startswith(('UV_','PIP_','PYTHON','SPECIFY_','SPECKIT_')) or
          k in ['VIRTUAL_ENV','CONDA_PREFIX','GH_TOKEN','GITHUB_TOKEN','OPENAI_API_KEY','ANTHROPIC_API_KEY'])}
    env.update({'UV_OFFLINE':'1','UV_PYTHON_DOWNLOADS':'never','UV_NO_CONFIG':'1', 'PIP_NO_INDEX':'1',
        'PIP_DISABLE_PIP_VERSION_CHECK':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1',
        'PYTHONPATH':os.pathsep.join([str(LOCAL/'guard'),str(ROOT/'src'),str(ROOT/'specs/003-msk-baseline-closure/execution')]),
        'MSK_EVIDENCE_RESULT':str(folder/'pytest-results.json'),'MSK_PROGRESS_LOG':str(temp/'progress.jsonl'),
        'PYTHONUNBUFFERED':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1',
        'HOME':str(profile),'USERPROFILE':str(profile),'XDG_CONFIG_HOME':str(profile/'config'),
        'TEMP':str(temp),'TMP':str(temp),'GIT_CONFIG_GLOBAL':str(profile/'gitconfig'),
        'GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0',
        'PATH':str(python.parent)+os.pathsep+os.environ.get('PATH','')})
    argv=[str(python),'-B','-m','pytest','-p','qualification_capture','-p','no:cacheprovider',
          '--basetemp',str(temp/'pytest'),*pytest_args]
    receipt={'run_id':run_id,'started_at_utc':datetime.now(timezone.utc).isoformat(), 'argv':argv,
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_import_profile':'Owned source root via explicit PYTHONPATH; no other project editable install',
        'isolation':'Task-local profile/temp; external Python sockets blocked, loopback allowed; no OS sandbox claim',
        'process_only_PATH_prefix':str(python.parent),'network_downloads':False,
        'temp_root':str(temp),'temp_has_git_ancestor':False,
        'source_files':{p:sha(ROOT/p) for p in ['src/specify_cli/events/__init__.py','tests/specify_cli/events/test_events.py',
                    'tests/integrations/test_integration_generic.py','tests/specify_cli/workflows/test_command_definition.py']}}
    dump(folder/'receipt.json',receipt)
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err)
        proc.stdin.close()
        receipt['process_id']=proc.pid
        dump(folder/'receipt.json',receipt)
        while proc.poll() is None:
            time.sleep(2)
            observed=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
            if observed!='fix/msk-baseline-closure-003-qualified':
                receipt['safety_stop']={'reason':'Unexpected task branch transition','observed_branch':observed}
                subprocess.run(['taskkill.exe','/PID',str(proc.pid),'/T','/F'],capture_output=True,check=True)
                break
        code=proc.wait()
    receipt.update(exit_code=code,finished_at_utc=datetime.now(timezone.utc).isoformat(),
        stdout_sha256=sha(folder/'stdout.txt'),stderr_sha256=sha(folder/'stderr.txt'))
    dump(folder/'receipt.json',receipt)
    value=json.loads((folder/'pytest-results.json').read_text()) if (folder/'pytest-results.json').exists() else {}
    print(json.dumps({'run_id':run_id,'exit_code':code,'unique_count':value.get('unique_count'),
        'counts':value.get('counts'),'collection_errors':value.get('collection_errors'), 'report':str(folder)}))
    return 0

if __name__=='__main__':
    main()
