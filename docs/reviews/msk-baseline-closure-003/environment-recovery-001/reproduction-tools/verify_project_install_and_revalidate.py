"""Fresh installed-package smoke and proportional metadata/entrypoint rerun."""
from recover_environment import ROOT,LOCAL,REPORT,dump,sha
from pathlib import Path
import json
import os
import subprocess
import sys

def main():
    folder=REPORT/'project-install-verification'
    folder.mkdir(exist_ok=False)
    python=LOCAL/'venv/Scripts/python.exe'
    cwd=Path(r'D:\APP\maged-spec-kit\msk003-qualification-temp-20261107-001')/'installed-smoke'
    cwd.mkdir(exist_ok=False)
    env={k:v for k,v in os.environ.items() if not(k.startswith(('PYTHON','SPECIFY_','SPECKIT_','UV_','PIP_')) or
        k in ['GH_TOKEN','GITHUB_TOKEN','VIRTUAL_ENV','CONDA_PREFIX'])}
    env.update(HOME=str(cwd),USERPROFILE=str(cwd),UV_OFFLINE='1',PIP_NO_INDEX='1',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
    code='''import sys,json,importlib.metadata as m,site,specify_cli
d=m.distribution("specify-cli")
print(json.dumps({"version":d.version,"origin":specify_cli.__file__,"executable":sys.executable,"user_site":site.ENABLE_USER_SITE,"direct_url":json.loads(d.read_text("direct_url.json")),"entry_points":[{"name":e.name,"value":e.value,"group":e.group} for e in d.entry_points],"packages":{x.metadata["Name"].lower():x.version for x in m.distributions()}}))'''
    commands=[]
    for label,argv in [('isolated-import',[str(python),'-I','-B','-c',code]),
        ('cli-help',[str(python.parent/'specify.exe'),'--help']),('cli-version',[str(python.parent/'specify.exe'),'--version'])]:
        r=subprocess.run(argv,cwd=cwd,env=env,input=b'',capture_output=True)
        (folder/(label+'.stdout.txt')).write_bytes(r.stdout);(folder/(label+'.stderr.txt')).write_bytes(r.stderr)
        commands.append({'label':label,'argv':argv,'cwd':str(cwd),'exit_code':r.returncode})
        assert r.returncode==0,(label,r.stderr)
    installed=json.loads((folder/'isolated-import.stdout.txt').read_text())
    assert Path(installed['origin']).resolve()==(ROOT/'src/specify_cli/__init__.py').resolve()
    assert installed['version']=='1.3.3.dev0' and installed['direct_url']['dir_info']['editable'] is True
    assert installed['direct_url']['url']==ROOT.as_uri()
    assert any(e['name']=='specify' and e['value']=='specify_cli:main' for e in installed['entry_points'])
    initial=json.loads((REPORT/'environment-verified.json').read_text())
    initial_versions={r['name'].lower():r['version'] for r in initial['installed_distributions']}
    assert all(installed['packages'].get(name)==version for name,version in initial_versions.items())
    assert set(installed['packages'])-set(initial_versions)=={'specify-cli'}
    final=json.loads((REPORT/'environment-final-verified.json').read_text())
    assert final['dependency_scope_verified'] and len(final['installed_distributions'])==51
    dump(folder/'receipt.json',{'commands':commands,'no_PYTHONPATH':True,'isolated_outside_repo_import':True,
        'actual_editable_directory_provenance':installed['direct_url'],'third_party_versions_unchanged':50,
        'third_party_integrity':'Final all-distribution RECORD check passed; install --no-deps did not request thirdparty modifications. No invented old per-file snapshot comparison.',
        'new_distribution':'specify-cli1.3.3.dev0 only','final_environment_evidence':'../environment-final-verified.json'})
    old=json.loads((REPORT/'remaining-windows-002/pytest-results.json').read_text())
    affected=sorted({r['nodeid'] for r in old['reports'] if r['outcome']=='failed' and 'WinError 2' in (r['detail'] or '') and 'test_installed_adapters.py::' in r['nodeid']})
    assert affected
    version_files=['tests/test_utils_assets_imports.py']+['tests/specify_cli/test_version_'+n+'.py' for n in ['imports','release','detection','guidance','execution','verification']]+['tests/specify_cli/test_'+n+'.py' for n in ['command_version','root_version_callback','operation_version','mcp_version']]
    assert all((ROOT/p).is_file() for p in version_files)
    selectors=version_files+affected+['tests/specify_cli/mcp_server/test_stdio.py']
    dump(REPORT/'final-differential-plan.json',{'reason':'Install owned editable distribution changes metadata/directURL/PATH/entrypoint only;50thirdparty versions/source hashes remain fixed',
        'selectors':selectors,'previously_missing_entrypoint_failed_IDs':affected,
        'additional_boundaries':'Installed-version/source-checkout/install-method/PATH,CLI/API/MCP/publicstdio; actual .pth and editable directory metadata verified outsideROOT/PYTHONPATH',
        'reuse':'Preserve unaffected earlier results with env50 scope; do not claim all cases rerun in final51env. Never sum overlapping attempts.'})
    argv=[sys.executable,'-B',str(ROOT/'specs/003-msk-baseline-closure/execution/run_recovered_checks.py'),
        'final-differential-001',*selectors,'-p','xdist.plugin','-n','4','-q']
    print(json.dumps({'smoke':'PASS','missing_entrypoint_cases':len(affected),'differential_argv':argv}),flush=True)
    raise SystemExit(subprocess.run(argv,cwd=ROOT).returncode)

if __name__=='__main__':main()
