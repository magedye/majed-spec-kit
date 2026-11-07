"""Local pytest evidence plugin, not a product gate or replacement oracle."""
import json
import os
import pytest
from pathlib import Path
from collections import Counter

items=[]
reports=[]
collection_errors=[]

def pytest_collection_finish(session):
    items.extend(item.nodeid for item in session.items)

@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node, ids):
    if not items:
        items.extend(ids)
        result_path=Path(os.environ['MSK_EVIDENCE_RESULT'])
        result_path.with_name('collected-nodeids.json').write_text(json.dumps(ids),encoding='utf-8')
    elif items != ids:
        collection_errors.append({'nodeid':'XDIST_COLLECTION','error':'Worker collections differ'})

def pytest_collectreport(report):
    if report.failed:
        collection_errors.append({'nodeid':report.nodeid,'error':str(report.longrepr)})

def pytest_runtest_logreport(report):
    row={'nodeid':report.nodeid,'phase':report.when,'outcome':report.outcome,
        'duration':report.duration,'detail':str(report.longrepr) if report.failed or report.skipped else None}
    reports.append(row)
    if not os.environ.get('PYTEST_XDIST_WORKER') and os.environ.get('MSK_PROGRESS_LOG'):
        with Path(os.environ['MSK_PROGRESS_LOG']).open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row)+'\n')

def pytest_sessionfinish(session,exitstatus):
    if hasattr(session.config,'workerinput'):
        return
    states=[]
    for nodeid in items:
        phases=[r for r in reports if r['nodeid']==nodeid]
        if session.config.option.collectonly: outcome='NOT_RUN'
        elif any(r['outcome']=='failed' for r in phases): outcome='FAILED'
        elif any(r['outcome']=='skipped' for r in phases): outcome='SKIPPED'
        elif any(r['phase']=='call' and r['outcome']=='passed' for r in phases): outcome='PASSED'
        else: outcome='NOT_RUN'
        states.append({'nodeid':nodeid,'result':outcome})
    value={'exit_code':int(exitstatus),'collect_only':session.config.option.collectonly,
        'collected_nodeids':items,'unique_count':len(set(items)),'duplicate_nodeids':len(items)-len(set(items)),
        'counts':dict(Counter(r['result'] for r in states)), 'cases':states,
        'reports':reports,'collection_errors':collection_errors,
        'source_import':str(__import__('specify_cli').__file__),
        'interpreter':__import__('sys').executable}
    Path(os.environ['MSK_EVIDENCE_RESULT']).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
