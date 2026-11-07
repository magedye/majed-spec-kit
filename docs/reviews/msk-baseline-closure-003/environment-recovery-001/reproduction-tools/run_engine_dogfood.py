"""Native engine observations in synthetic fixtures; no policy engine added."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import os
import sys
import yaml
from specify_cli.workflows.engine import WorkflowDefinition,WorkflowEngine

ROOT=Path(r'D:\APP\maged-spec-kit\majed-spec-kit\specs\003-msk-baseline-closure\execution-worktree')
LOCAL=ROOT/'specs/003-msk-baseline-closure/execution/environment-recovery-001'
REPORT=ROOT/'docs/reviews/msk-baseline-closure-003/environment-recovery-001'
ATTEMPT='engine-dogfood-004'
FIXTURE=LOCAL/ATTEMPT

def dump(path,value): path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert sys.prefix==str(LOCAL/'venv')
    assert not sys.stdin.isatty(), 'Headless fixture requires a real stdin pipe, not Windows NUL'
    FIXTURE.mkdir(exist_ok=False)
    old=json.loads((ROOT/'docs/reviews/msk-baseline-closure-003/dogfooding-results.json').read_text(encoding='utf-8'))
    cases=[{'case_id':c['CASE_ID'],'original_expected':c['EXPECTED'],'desired_control':c['INPUT']['oracle_ar']}
           for c in old['cases'] if c['CASE_ID']!='DF-POS']
    # Expected control and variants fixed before any engine execution.
    predeclared={'started_at_utc':datetime.now(timezone.utc).isoformat(),'cases':cases,
      'variants':{'DF-N01':['missing verdict must pause','expired grant + self approve must not count as authorization'],
                  'DF-N02':['out-of-declared-fixture-write-set shell effect must be prevented or its after-the-fact detection disclosed'],
                  'DF-N03':['unresolved source conflict represented by unbound gate must pause; no automatic conflict detection inferred'],
                  'DF-N04':['self role owner + supplied approve is not authenticated permission'],
                  'DF-N05':['same implementer/reviewer approval is not independent review'],
                  'DF-N06':['successful check must leave separate approval pending; self verdict acceptance remains untrusted'],
                  'DF-N07':['mismatched candidate evidence must not become valid merely by supplied approve'],
                  'DF-N08':['reject abort must prevent later fixture save marker']},
      'scope':'Actual native WorkflowEngine/GateStep/ShellStep, synthetic local effects only; no product wrapper, guard or policy engine added'}
    dump(REPORT/(ATTEMPT+'-predeclared.json'),predeclared)
    original_digest=sha(REPORT/(ATTEMPT+'-predeclared.json'))
    results=[]

    def gate(): return {'id':'review','type':'gate','message':'Synthetic owner review; source metadata is not authenticated',
                        'verdict_input':'verdict','on_reject':'abort'}
    def marker(name='effect.txt'): return {'id':'effect','type':'shell','run':f'echo synthetic>{name}','timeout':10}
    def execute(case,variant,steps,inputs,metadata):
        project=FIXTURE/(case.lower()+'-'+variant)
        project.mkdir()
        (project/'.specify').mkdir()
        dump(project/'DECLARED_SCOPE_AND_SOURCES.json',metadata)
        definition=WorkflowDefinition({'schema_version':'1.0','workflow':{'id':'synthetic-boundary','name':'Synthetic boundary'},
            'inputs':{'verdict':{'type':'string','default':''}},'steps':steps})
        engine=WorkflowEngine(project)
        errors=engine.validate(definition)
        if errors: raise ValueError(errors)
        state=engine.execute(definition,inputs=inputs,run_id='case')
        files={str(p.relative_to(project)):sha(p) for p in project.rglob('*') if p.is_file()}
        record={'CASE_ID':case,'variant':variant,'fixture':str(project),'inputs':inputs,'metadata':metadata,
                'run_status':state.status.value,'steps':state.step_results,'effect_exists':(project/'effect.txt').exists(),
                'out_of_declared_scope_exists':(project/'outside.txt').exists(),'files':files,
                'original_expected':next(c['original_expected'] for c in cases if c['case_id']==case)}
        results.append(record)
        return record

    a=execute('DF-N01','missing',[gate(),marker()],{}, {'grant':None})
    a.update(RESULT='PASS_CONFIGURED_GATE_ONLY' if a['run_status']=='paused' and not a['effect_exists'] else 'FAIL',
             ENFORCEMENT_LEVEL='PRE_EXECUTION_ENFORCEMENT',LIMIT='No missing-grant semantic check; this is absence of gate choice')
    a=execute('DF-N01','expired',[gate(),marker()],{'verdict':'approve'}, {'grant':{'expires_at':'2000-01-01T00:00:00Z'},'supplied_by':'executor'})
    a.update(RESULT='CONTROL_NOT_PROVIDED' if a['effect_exists'] else 'UNEXPECTED',ENFORCEMENT_LEVEL='NOT_VERIFIED',
             LIMIT='Native gate does not validate expiry; supplied choice cannot establish real authorization')
    a=execute('DF-N02','outside',[marker('outside.txt')],{}, {'declared_fixture_write_set':['allowed.txt'],'safe_parent':str(FIXTURE)})
    a.update(RESULT='CONTROL_NOT_PROVIDED' if a['out_of_declared_scope_exists'] else 'UNEXPECTED',
             ENFORCEMENT_LEVEL='POST_EXECUTION_DETECTION',LIMIT='Harness observes fixture effect afterwards; product has no write-set sandbox. Effect stayed inside authorized synthetic parent')
    a=execute('DF-N03','conflict',[gate(),marker()],{}, {'sources':[{'id':'synthetic-A','decision':'allow'},{'id':'synthetic-B','decision':'deny'}],'resolution':None})
    a.update(RESULT='PASS_CONFIGURED_HOLD_ONLY' if a['run_status']=='paused' and not a['effect_exists'] else 'FAIL',
             ENFORCEMENT_LEVEL='BEHAVIORAL_COMPLIANCE',LIMIT='Operator represented unresolved conflict by withholding choice; engine did not interpret/detect source authority')
    a=execute('DF-N04','self-role',[gate(),marker()],{'verdict':'approve'}, {'actor':'executor','claimed_role':'owner','verified_grant':None})
    a.update(RESULT='CONTROL_NOT_PROVIDED' if a['effect_exists'] else 'UNEXPECTED',ENFORCEMENT_LEVEL='NOT_VERIFIED',
             LIMIT='Supplied role/verdict unauthenticated; engine completion is not a permission grant')
    a=execute('DF-N05','self-review',[gate(),marker()],{'verdict':'approve'}, {'implementer':'synthetic-executor','reviewer':'synthetic-executor'})
    a.update(RESULT='CONTROL_NOT_PROVIDED' if a['effect_exists'] else 'UNEXPECTED',ENFORCEMENT_LEVEL='NOT_VERIFIED',
             LIMIT='No independent identity check; actual independent review remains separate')
    a=execute('DF-N06','test-pass',[{'id':'check','type':'shell','run':'echo passed','timeout':10},gate(),marker()],{}, {'test_result':'PASSED','real_owner_acceptance':'NOT_GRANTED'})
    a.update(RESULT='PASS_SEPARATE_CONFIGURED_GATE' if a['run_status']=='paused' and not a['effect_exists'] else 'FAIL',
             ENFORCEMENT_LEVEL='PRE_EXECUTION_ENFORCEMENT',LIMIT='Explicit pending gate separates check from choice; passing check itself does not authenticate acceptance')
    a=execute('DF-N07','stale-evidence',[gate(),marker()],{'verdict':'approve'}, {'evidence_candidate':'synthetic-old','current_candidate':'synthetic-new'})
    a.update(RESULT='CONTROL_NOT_PROVIDED' if a['effect_exists'] else 'UNEXPECTED',ENFORCEMENT_LEVEL='POST_EXECUTION_DETECTION',
             LIMIT='Mismatch explicitly detected by assessment after observation; engine does not bind evidence candidate. Never imported as current-candidate PASS')
    a=execute('DF-N08','reject',[gate(),marker()],{'verdict':'reject'}, {'mandatory_gate':True,'next_marker_is_not_real_commit':True})
    a.update(RESULT='PASS_NATIVE_ABORT' if a['run_status']=='failed' and not a['effect_exists'] else 'FAIL',
             ENFORCEMENT_LEVEL='PRE_EXECUTION_ENFORCEMENT',LIMIT='Actual configured native engine abort only; no global Shell/host enforcement claimed')
    assert sha(REPORT/(ATTEMPT+'-predeclared.json'))==original_digest
    value={'status':'PARTIAL_WITH_CONTROL_GAPS','synthetic_only':True,'interpreter':sys.executable,
           'source_import':__import__('specify_cli').__file__,'predeclared_sha256':original_digest,
           'original_cases_completed':8,'newly_unblocked_original_cases':7,'variant_runs':len(results),
           'results':results,'original_positive_evidence_preserved':True,
           'real_owner_acceptance':'NOT_GRANTED','independent_review':'PENDING_FIXED_TECHNICAL_CANDIDATE',
           'classification':'Missing controls are capability/interface limitations, not contract violations established merely by these owner-desired scenarios',
           'finished_at_utc':datetime.now(timezone.utc).isoformat()}
    dump(REPORT/(ATTEMPT+'-results.json'),value)
    print(json.dumps({'status':value['status'],'variants':[(r['CASE_ID'],r['variant'],r['RESULT'],r['run_status']) for r in results]}))

if __name__=='__main__': main()
