"""Scoped verified fix checkpoint; never merge or claim full qualification."""
from recover_environment import ROOT,LOCAL,REPORT,dump,sha
from pathlib import Path
import hashlib
import json
import subprocess

FILES=['src/specify_cli/events/__init__.py','tests/specify_cli/events/test_events.py',
       'tests/integrations/test_integration_generic.py','tests/specify_cli/workflows/test_command_definition.py']

def main():
    git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')=='98e6269f4112b9627f78e154cf17760d5f86f43d'
    assert git('branch','--show-current')=='fix/msk-baseline-closure-003-qualified'
    assert git('rev-parse','fix/msk-baseline-closure-003')=='ca3233afe5192ba01861098c429effea7e6a4f6c'
    baseline=json.loads((ROOT/'specs/003-msk-baseline-closure/execution/BASELINE_FILE_IDENTITIES.json').read_text())
    for p,digest in baseline.items():
        if p not in FILES: assert sha(ROOT/p)==digest,p
    for p in FILES: assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show','ca3233a:'+p],cwd=ROOT),p
    after=json.loads((REPORT/'focused-after-001/pytest-results.json').read_text())
    before=json.loads((REPORT/'regression-before-001/pytest-results.json').read_text())
    assert after['exit_code']==0 and after['counts']=={'PASSED':516} and after['duplicate_nodeids']==0
    assert before['exit_code']==1 and before['counts']=={'FAILED':1}
    assert not git('diff','--cached','--name-only')
    receipt={'scope':'Four original ca3233a nonprotected files, byte-identical reuse',
             'mandatory_checkpoint_gate':'516 affected tests PASS; actual regression fails before product fix',
             'full_suite':'RUNNING; not a closure gate pass or review/owner acceptance',
             'sources':{p:sha(ROOT/p) for p in FILES},'before':git('rev-parse','HEAD')}
    subprocess.run(['git','diff','--check','--',*FILES],cwd=ROOT,check=True)
    subprocess.run(['git','add','--',*FILES],cwd=ROOT,check=True)
    assert set(git('diff','--cached','--name-only').splitlines())==set(FILES)
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    r=subprocess.run(['git','commit','-m','fix: reuse verified Windows baseline corrections',
        '-m','MSK-BASELINE-CLOSURE-003: reuse four ca3233a source/test files; keep protected AGENTS proposal unapplied. Focused regression verified; full qualification remains pending.\n\nAssisted-by: Codex (model: GPT-6, autonomous)'],cwd=ROOT,capture_output=True)
    (REPORT/'fix-checkpoint.stdout.txt').write_bytes(r.stdout)
    (REPORT/'fix-checkpoint.stderr.txt').write_bytes(r.stderr)
    receipt.update(exit_code=r.returncode,after=git('rev-parse','HEAD'),merge=False,push=False)
    dump(REPORT/'fix-checkpoint.json',receipt)
    print(json.dumps(receipt))
    raise SystemExit(r.returncode)

if __name__=='__main__':main()
