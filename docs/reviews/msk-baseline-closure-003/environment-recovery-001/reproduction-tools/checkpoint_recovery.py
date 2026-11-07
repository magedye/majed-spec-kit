"""Gated partial evidence checkpoint only; failed qualification remains explicit."""
from recover_environment import ROOT,LOCAL,REPORT,dump,sha
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import subprocess
import sys

def main():
    run_id,message=sys.argv[1:]
    assert __import__('re').fullmatch('[a-z0-9-]+',run_id)
    folder=LOCAL/run_id;folder.mkdir(exist_ok=False)
    git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
    assert git('branch','--show-current')=='fix/msk-baseline-closure-003-qualified'
    assert not git('diff','--cached','--name-only')
    state={'started_at_utc':datetime.now(timezone.utc).isoformat(),'before':git('rev-parse','HEAD'),
        'checkpoint':'LOCAL_PARTIAL_EVIDENCE_ONLY','not_a_full_qualification_or_acceptance_gate':True,'commands':[]}
    def run(label,argv):
        r=subprocess.run(argv,cwd=ROOT,capture_output=True)
        (folder/(label+'.stdout.txt')).write_bytes(r.stdout);(folder/(label+'.stderr.txt')).write_bytes(r.stderr)
        state['commands'].append({'label':label,'argv':argv,'exit_code':r.returncode})
        if r.returncode:raise subprocess.CalledProcessError(r.returncode,argv)
    try:
        checker=[sys.executable,'-B',str(ROOT/'specs/003-msk-baseline-closure/execution/verify_recovery_package.py')]
        run('pre-stage',checker)
        run('stage',['git','add','--','docs/reviews/msk-baseline-closure-003/'])
        assert all(p.startswith('docs/reviews/msk-baseline-closure-003/') for p in git('diff','--cached','--name-only').splitlines())
        run('staged',checker)
        run('commit',['git','commit','-m',message,'-m',
            'MSK-BASELINE-CLOSURE-003: partial evidence checkpoint; unresolved qualification failures/control gaps remain. No merge, push or Core authorization.\n\nAssisted-by: Codex (model: GPT-6, autonomous)'])
        state['result']='SAVED_PARTIAL_LOCAL_CHECKPOINT'
    except (subprocess.CalledProcessError,AssertionError) as error:
        state['result']='CHECKPOINT_BLOCKED';state['error']=repr(error)
    state.update(after=git('rev-parse','HEAD'),finished_at_utc=datetime.now(timezone.utc).isoformat(),merge=False,push=False)
    dump(folder/'receipt.json',state);print(json.dumps(state))
    raise SystemExit(state['result']!='SAVED_PARTIAL_LOCAL_CHECKPOINT')

if __name__=='__main__':main()
