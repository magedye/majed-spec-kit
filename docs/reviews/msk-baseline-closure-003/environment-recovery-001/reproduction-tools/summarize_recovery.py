"""Candidate-bound assessment from completed receipts; preserve historical evidence."""
from recover_environment import ROOT,LOCAL,REPORT,dump,sha
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timezone
import json
import subprocess

def main():
    load=lambda p:json.loads((REPORT/p).read_text(encoding='utf-8'))
    full=load('remaining-windows-002/pytest-results.json')
    receipt=load('remaining-windows-002/receipt.json')
    assert 'finished_at_utc' in receipt and receipt['exit_code']==full['exit_code']
    env=load('environment-verified.json')
    assert env['dependency_scope_verified']
    baseline=load('collection-002/pytest-results.json')
    focused=load('focused-after-001/pytest-results.json')
    safety=load('safety-nogit-001/pytest-results.json')
    before=load('focused-baseline-001/pytest-results.json')
    regression=load('regression-before-001/pytest-results.json')
    before_ids=set(baseline['collected_nodeids'])
    populations=[set(p['collected_nodeids']) for p in [full,focused,safety]]
    assert not populations[0]&populations[1] and not populations[0]&populations[2] and not populations[1]&populations[2]
    final_ids=set.union(*populations)
    all_cases=full['cases']+focused['cases']+safety['cases']
    all_reports=full['reports']+focused['reports']+safety['reports']
    original_counts=dict(Counter(c['result'] for c in all_cases))
    differential=load('final-differential-001/pytest-results.json')
    serial=load('stdio-serial-001/pytest-results.json')
    assert set(differential['collected_nodeids'])<=final_ids and set(serial['collected_nodeids'])<=final_ids
    current_cases={r['nodeid']:{**r,'attempt':'initial-disjoint-population','environment':'50 thirdparty deps; source import, before own editable install'} for r in all_cases}
    for attempt,record in [('final-differential-001',differential),('stdio-serial-001',serial)]:
        for row in record['cases']:current_cases[row['nodeid']]={**row,'attempt':attempt,'environment':'Final51distributions: same50deps plus owned editable specify-cli'}
        all_reports.extend({**row,'attempt':attempt} for row in record['reports'])
    final_counts=dict(Counter(r['result'] for r in current_cases.values()))
    dump(REPORT/'case-accounting.json',{'unique_denominator':len(final_ids),'original_counts':original_counts,
        'current_observation_counts':final_counts,'cases':[current_cases[k] for k in sorted(current_cases)],
        'validity':'Older unaffected observations retain exact earlier50dep scope;285metadata/entrypoint impacted cases revalidated on final51env, plus serialMCP. No single-final-environment Full Suite PASS claim.',
        'parallel_stdio_failure_remains_material':True,'serial_stdio_counts':serial['counts']})
    missing=sorted(before_ids-final_ids)
    new=sorted(final_ids-before_ids)
    assert full['duplicate_nodeids']==0
    expected='tests/specify_cli/events/test_events.py::TestCommandRunner::test_sh_variant_without_launcher_returns_none'
    assert not missing and new==[expected],(len(missing),new)
    assert set(focused['collected_nodeids'])<=final_ids
    definition_inventory=json.loads((ROOT/'docs/reviews/msk-baseline-closure-003/qualification-inventory.json').read_text(encoding='utf-8'))
    expected_defs={r['static_definition'] for r in definition_inventory['static_definitions']}
    mapped=defaultdict(list)
    for node in final_ids:
        mapped[node.split('[',1)[0]].append(node)
    # Some test templates are abstract bases or helpers and do not collect;
    # discrepancies are explicit, not force-matched or excluded silently.
    definition_rows=[{'static_definition':d,'collected_nodeids':sorted(mapped.get(d,[])),
                     'disposition':'COLLECTED' if d in mapped else 'NO_EXACT_RUNTIME_MATCH_REQUIRES_INTERPRETATION'}
                    for d in sorted(expected_defs)]
    dump(REPORT/'collection-reconciliation.json',{
        'baseline_collection':{'count':len(before_ids),'evidence':'collection-002/pytest-results.json'},
        'current_candidate_collection':{'count':len(final_ids),'evidence':['remaining-windows-002/pytest-results.json','focused-after-001/pytest-results.json','safety-nogit-001/pytest-results.json']},
        'partition_policy':'Three disjoint ID sets cover all cases; reuse516 passing affected checks and2 safety checks; execute only remaining13884 cases. Mandatory full-population accounting, not a single Full Suite invocation PASS claim.',
        'added':new,'missing':missing,'duplicate_ids':full['duplicate_nodeids'],
        'definitions_pre_patch':len(expected_defs),'definitions_after_patch':len(expected_defs)+1,
        'unmatched_static_count':sum(d['disposition']!='COLLECTED' for d in definition_rows),
        'unmatched_runtime_definitions':sorted(set(mapped)-expected_defs),
        'inventory_modules_not_directly_collecting_cases':sorted({r['path'] for r in definition_inventory['tracked_test_support_files'] if r['test_module']}-{n.split('::')[0] for n in final_ids}),
        'inventory_module_interpretation':'Four integration_base Markdown/skills/TOML/YAML modules are reusable mixins exercised through subclasses; not four missing test populations',
        'static_definition_mapping':definition_rows,
        'historical_QUAL002':'Original raw history still unavailable; old counts not summed or proven by this replacement run',
        'counts_are_parameter_expanded_runtime_ids_not_static_definitions':True})
    groups=defaultdict(Counter)
    for row in current_cases.values():groups[row['nodeid'].split('::')[0]][row['result']]+=1
    failures=[]
    skipped=[]
    for row in all_reports:
        if row['outcome']=='skipped':skipped.append(row)
        if row['outcome']!='failed':continue
        text=row['detail'] or ''
        display_cases=['test_non_windows_uv_tool_dry_run_still_previews_installer',
            'test_archive_cleanup_failure_preserves_primary_install_error','test_catalog_cleanup_failure_adds_note_to_primary_error',
            'test_archive_temp_directory_cleanup_failure_warns_after_commit']
        if 'test_installed_adapters.py::' in row['nodeid'] and 'WinError 2' in text:
            category='ENVIRONMENT_DEFECT_MISSING_OWN_PROJECT_ENTRYPOINT_RESOLVED_BY_EDITABLE_INSTALL'
        elif 'mcp_server/test_stdio.py::' in row['nodeid']:
            category='UNVERIFIED_STDIO_PARALLEL_INIT_OR_CONNECTION; serialPASS does not explain parallel timeout root cause'
        elif any(row['nodeid'].endswith('::'+name) for name in display_cases):
            category='TEST_DEFECT_RICH_HARD_WRAP_LONG_PATH_ASSERTION'
        elif any(row['nodeid'].endswith('::'+name) for name in ['test_community_step_is_not_treated_as_bundled','test_unknown_reference_errors_online','test_validate_rejects_broken_reference']):
            category='EXTERNAL_DEPENDENCY_AND_TEST_ASSUMPTION_UNMOCKED_CATALOG'
        elif 'MSK qualification external' in text:category='ENVIRONMENT_DEFECT_OFFLINE_BOUNDARY'
        elif 'WinError 206' in text or 'Filename too long' in text:category='ENVIRONMENT_DEFECT_PATH_LENGTH'
        elif 'PermissionError' in text or 'WinError 5' in text or 'WinError 1314' in text:category='ENVIRONMENT_OR_PRODUCT_UNRESOLVED_PERMISSION'
        elif 'FileNotFoundError' in text or 'not recognized' in text:category='UNVERIFIED_MISSING_PATH_OR_TOOL'
        else:category='UNVERIFIED_REQUIRES_REPRODUCTION_AND_ROOT_CAUSE'
        failures.append({**row,'initial_classification':category,
                         'latest_observation':current_cases[row['nodeid']],
                         'root_cause_evidence':'Observed wrapped path token in raw Rich output; contiguous-string assertion fails. Prior assertions reached passed, later assertions not reached remain unverified; independent source review. No requirement/assertion weakened.' if 'RICH_HARD_WRAP' in category else
                             'Observed external DNS denial and source-dependent catalog resolution before intended assertion' if 'OFFLINE_BOUNDARY' in category else
                             'Source-supported inference: references.py203-206 returnsNone on CatalogUnavailable and248-264 warns unchecked; three tests have no catalog mock. Actual per-call warning values were not captured; assertion None does not demonstrate community registry leakage' if 'UNMOCKED_CATALOG' in category else 'Raw failure retained; no proven product root cause asserted',
                         'classification_is_not_proven_product_defect':True,
                         'scope_disposition':'REQUIRED_FOR_CURRENT_ACCEPTANCE; correction not authorized outside existing four-file write-set'})
    dump(REPORT/'qualification-outcomes.json',{
        'result':'PASSED_IN_LOCAL_PROFILE' if full['exit_code']==0 else 'FAILED_LOCAL_PROFILE',
        'candidate_source':load('fix-checkpoint.json')['after'],'run_started_on_parent_plus_exact_recorded_patch':receipt['git_head'],
        'source_file_hashes':receipt['source_files'],'environment_fingerprint':sha(REPORT/'environment-verified.json'),
        'profile':'Windows native Python3.12.10; initial50dependency/source-import disjoint population, final51distribution metadata/entrypoint differential and serialMCP. Explicit environment/fixture ancestry limits; no uniform-final-env Full Suite PASS.',
        'full_population_partitioned_exit_codes':{'remaining':full['exit_code'],'focused':focused['exit_code'],'safety':safety['exit_code']},
        'unique_denominator':len(final_ids),'counts':final_counts,
        'original_partitioned_counts_before_editable_project':original_counts,
        'final_environment_differential':{'unique_cases':differential['unique_count'],'counts':differential['counts'],'serial_stdio':serial['counts']},
        'current_case_provenance':'case-accounting.json; no claim all cases rerun in final51env. Parallel stdio timeout remains unresolved despite serialPASS.',
        'full_windows001':'INCONCLUSIVE / SAFETY_INTERRUPTED after ancestor Git traversal changed task branch; no case counts inferred from dots; original receipt/logs preserved',
        'baseline_focused_counts':before['counts'],'before_regression_counts':regression['counts'],
        'after_focused_counts':focused['counts'],
        'not_aggregate_sum':'Baseline/before/interrupted attempts are excluded. Remaining+focused-after+safety IDs are asserted disjoint and unioned; no overlapping outcomes summed.',
        'module_results':{k:dict(v) for k,v in sorted(groups.items())},
        'failure_phase_records':failures,'skipped_phase_records':skipped,
        'historical_results':'UNVERIFIED, original missing; never equated to these new replacement attempts',
        'CI_OS_PYTHON_MATRIX':'NOT_RUN, local profile does not replace Linux/macOS/other Python/CodeQL gates'})
    dogfood=load('engine-dogfood-004-results.json')
    correction=load('dogfood-classification-correction.json')
    dogrows=[]
    for row in dogfood['results']:
        effective=correction['corrected_assessment'] if row['CASE_ID']=='DF-N08' else row['RESULT']
        dogrows.append({'case':row['CASE_ID'],'variant':row['variant'],'assessment':effective,
                        'enforcement_level':row['ENFORCEMENT_LEVEL'],'limit':row['LIMIT'],
                        'actual_runtime':'EXECUTED','raw_result_preserved':row['RESULT']})
    dump(REPORT/'dogfooding-assessment.json',{'status':'PARTIAL_WITH_CONTROL_GAPS',
        'all_seven_previously_dependency_blocked_cases_executed':True,'original_positive_evidence':'../dogfooding-results.json#cases/0',
        'no_original_positive_rerun':'SDD source scripts/fixture behavior unaffected by event resolver patch or new third-party environment',
        'raw':'engine-dogfood-004-results.json','classification_correction':'dogfood-classification-correction.json',
        'variants':dogrows,'enforcement_not_inferred':'Native supplied-verdict workflow control is not authenticated owner/reviewer/scope/evidence authority',
        'no_parallel_policy_engine_or_Core_implementation':True})
    # Preserve original preparation receipt; current assessment closes its unfinished status.
    dump(REPORT/'environment-resolution-current.json',{
        'original_preparation_receipt':'recovery-state.json','original_receipt_preserved':True,
        'result':'OFFLINE_ENVIRONMENT_VERIFIED','qualified_environment':True,
        'qualified_scope':'Dependency compatibility and RECORD integrity for Windows Python3.12.10 only; not baseline acceptance',
        'evidence':['environment-verified.json','offline-install.json','environment-final-verified.json','project-install-003/receipt.json','project-install-verification/receipt.json']})
    current={'request_id':'MSK-BASELINE-CLOSURE-003','engineering_status':'PARTIAL_WITH_BLOCKERS',
        'environment':'ISOLATED_DEPENDENCIES_AND_OWNED_EDITABLE_INSTALL_VERIFIED',
        'BASELINE_TECHNICAL_QUALIFICATION':{'status':'PARTIAL_WITH_BLOCKERS','local_result':final_counts,'remaining_partition_exit_code':full['exit_code'],
             'remaining':'11actual unresolved catalog/Rich cases; parallelMCP timeout not explained by serialPASS; matrix/CodeQL and historical evidence gaps remain'},
        'SELF_GOVERNANCE_QUALIFICATION':{'status':'PARTIAL_WITH_CONTROL_GAPS','evidence':'dogfooding-assessment.json'},
        'CORE_IMPLEMENTATION_READINESS':{'status':'UNRESOLVED_NOT_APPROVED','reason':'No approved complete Core slice/authority; host-trust controls not supplied by baseline native gate'},
        'OWNER_APPROVAL_STATUS':{'bounded_execution':'GRANTED','candidate_acceptance':'NOT_GRANTED','Core':'NOT_GRANTED','merge':'PROHIBITED','push':'PROHIBITED'},
        'independent_technical_review':'PENDING_FIXED_PACKAGE_REVIEW',
        'previous_documentary_review':'../INDEPENDENT_REVIEW_002.md remains documentary only, no substitution',
        'updated_at_utc':datetime.now(timezone.utc).isoformat()}
    dump(REPORT/'readiness-current.json',current)
    dump(REPORT/'differential-revalidation.json',{
        'source_candidate':load('fix-checkpoint.json')['after'],'changed_sources':load('fix-checkpoint.json')['sources'],
        'source_reuse':'Byte-identical four existing ca3233a source/test files; AGENTS excluded',
        'environment_change':'50offline hash-pinned thirdparty packages; after initialpopulation completed, canonical offline owned editable install adds1distribution and CLI entrypoint;50versions fixed, final51RECORD checked. Earlier env/evidence retained.',
        'environment_differential':'final-differential-plan.json;285impacted cases275pass8skip2fail; standalone actualMCPtest1PASS, paralleltimeout remains material/not root-caused.',
        'reruns_justified':'Dependency conditions changed; before/after focused regression and mandatory full Windows profile now feasible',
        'preserved_valid':'Original source-script positive, prior semantic/authority analysis and documentary review retain only exact scopes',
        'invalid_for_final_qualification':'Historical unverified counts; earlier readchar blocked collection; generated mirror cases do not replace primary package tests',
        're_review':'Code/runtime/env assessment requires new independent technical review; no automatic transfer from documentary review'})
    print(json.dumps({'status':current['engineering_status'],'unique_count':len(final_ids),'counts':final_counts,
                      'failure_phase_records':len(failures),'static_unmatched':sum(d['disposition']!='COLLECTED' for d in definition_rows)}))

if __name__=='__main__':main()
