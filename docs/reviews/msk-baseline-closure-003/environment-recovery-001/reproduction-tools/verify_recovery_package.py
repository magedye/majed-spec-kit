"""Current-candidate preservation/evidence checkpoint, not qualification acceptance."""
from recover_environment import ROOT,LOCAL,REPORT,dump,sha
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess

FILES=['src/specify_cli/events/__init__.py','tests/specify_cli/events/test_events.py',
       'tests/integrations/test_integration_generic.py','tests/specify_cli/workflows/test_command_definition.py']

def main():
    git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
    assert git('branch','--show-current')=='fix/msk-baseline-closure-003-qualified'
    assert git('rev-parse','main')=='f74bdb893dcba23de72069b46ced5baaeb1684ea'
    assert git('rev-parse','fix/msk-baseline-closure-003')=='ca3233afe5192ba01861098c429effea7e6a4f6c'
    subprocess.run(['git','merge-base','--is-ancestor','98e6269', 'HEAD'],cwd=ROOT,check=True)
    baseline=json.loads((ROOT/'specs/003-msk-baseline-closure/execution/BASELINE_FILE_IDENTITIES.json').read_text())
    for path,digest in baseline.items():
        if path in FILES:
            assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show','ca3233a:'+path],cwd=ROOT),path
        else: assert sha(ROOT/path)==digest,path
    original=json.loads((ROOT/'specs/003-msk-baseline-closure/execution/PREFLIGHT.json').read_text())
    for row in original['planning_files']:
        for key in ['path','backup']:assert sha(Path(row[key]))==row['sha256']
    for p in git('diff','--name-only','f74bdb8').splitlines():
        assert p in FILES or p.startswith('docs/reviews/msk-baseline-closure-003/'),p
    for p in git('diff','--cached','--name-only').splitlines():
        assert p.startswith('docs/reviews/msk-baseline-closure-003/'),p
    parsed={p.relative_to(REPORT).as_posix():json.loads(p.read_text(encoding='utf-8-sig')) for p in REPORT.rglob('*.json')}
    assert parsed['environment-verified.json']['dependency_scope_verified']
    assert len(parsed['environment-verified.json']['installed_distributions'])==50
    assert not parsed['environment-verified.json']['integrity_errors']
    assert parsed['environment-final-verified.json']['dependency_scope_verified']
    assert len(parsed['environment-final-verified.json']['installed_distributions'])==51
    assert parsed['project-install-verification/receipt.json']['actual_editable_directory_provenance']['dir_info']['editable'] is True
    outcome=parsed['qualification-outcomes.json']
    assert outcome['unique_denominator']==14402 and sum(outcome['counts'].values())==14402
    reconciliation=parsed['collection-reconciliation.json']
    assert not reconciliation['missing'] and len(reconciliation['added'])==1
    assert parsed['focused-after-001/pytest-results.json']['counts']=={'PASSED':516}
    assert parsed['regression-before-001/pytest-results.json']['counts']=={'FAILED':1}
    assert parsed['readiness-current.json']['engineering_status']=='PARTIAL_WITH_BLOCKERS'
    for run in ['collection-002','focused-baseline-001','regression-before-001','focused-after-001','full-windows-001','safety-nogit-001','remaining-windows-002','final-differential-001','stdio-serial-001']:
        receipt=parsed[run+'/receipt.json']
        assert 'finished_at_utc' in receipt,run
        for output in ['stdout','stderr']:assert sha(REPORT/run/(output+'.txt'))==receipt[output+'_sha256']
    assert not (REPORT/'full-windows-001/pytest-results.json').exists(),'Interrupted attempt must not fabricate outcomes'
    raw=parsed['engine-dogfood-004-results.json']
    assert raw['newly_unblocked_original_cases']==7 and raw['variant_runs']==9
    assert sha(REPORT/'engine-dogfood-004-predeclared.json')==raw['predeclared_sha256']
    assert sha(REPORT/'engine-dogfood-004-results.json')==parsed['dogfood-classification-correction.json']['raw_sha256']
    assert sum(r['RESULT']=='CONTROL_NOT_PROVIDED' for r in raw['results'])==5
    with (REPORT/'OWNER_DECISIONS_AR.csv').open(encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    assert not any(r['OWNER_STATUS'] in ['OWNER_ACCEPTED','CORE_IMPLEMENTATION_APPROVED','PRODUCTION_READY'] for r in rows)
    for p in REPORT.glob('*.md'):
        for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' not in ref and not ref.startswith('#'): assert (p.parent/ref.split('#')[0]).exists(),ref
    # Opaque stdout/stderr and immutable owner text retain raw whitespace/bytes.
    authored=[str(p.relative_to(ROOT)) for p in REPORT.rglob('*') if p.is_file() and p.suffix in ['.json','.md','.csv','.py']]
    for cached in [False,True]:
        subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff',*(['--cached'] if cached else []),'--check','--',*authored],cwd=ROOT,check=True)
    for p in REPORT.rglob('*'):
        if p.is_file(): assert not re.search(rb'(?:sk-[A-Za-z0-9]{24,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)',p.read_bytes()),str(p)
    print(json.dumps({'result':'PASS_SCOPED_LOCAL_CHECKPOINT_ONLY','preserved_source_files':len(baseline)-4,
      'reused_source_test_files':4,'planning_original_backup_checks':len(original['planning_files'])*2,
      'current_unique_denominator':14402,'actual_results':outcome['counts'],'JSON_artifacts':len(parsed),
      'full_qualification_or_owner_acceptance':False}))

if __name__=='__main__':main()
