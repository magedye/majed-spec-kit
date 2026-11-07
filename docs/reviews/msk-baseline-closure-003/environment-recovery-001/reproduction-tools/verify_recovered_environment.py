"""Run with recovered interpreter; inspect all dependency metadata and RECORDs."""
from pathlib import Path
import base64
import csv
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import site
import sys
import tomllib
from packaging.requirements import Requirement
from packaging.markers import default_environment
from packaging.specifiers import SpecifierSet

ROOT=Path(r'D:\APP\maged-spec-kit\majed-spec-kit\specs\003-msk-baseline-closure\execution-worktree')
REPORT=ROOT/'docs/reviews/msk-baseline-closure-003/environment-recovery-001'
result={'interpreter':sys.executable,'version':sys.version,'prefix':sys.prefix,'base_prefix':sys.base_prefix,
        'user_site_enabled':site.ENABLE_USER_SITE,'sys_path':sys.path,'requirements':[],
        'installed_distributions':[],'integrity_errors':[],'transitive_errors':[],'modules':{}}
spec=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))
assert Path(sys.prefix).resolve()==(ROOT/'specs/003-msk-baseline-closure/execution/environment-recovery-001/venv').resolve()
assert sys.prefix!=sys.base_prefix and not site.ENABLE_USER_SITE
assert SpecifierSet(spec['project']['requires-python']).contains('.'.join(map(str,sys.version_info[:3])))
for text in spec['project']['dependencies']+spec['project']['optional-dependencies']['test']:
    req=Requirement(text)
    try: version=metadata.version(req.name)
    except metadata.PackageNotFoundError: version=None
    result['requirements'].append({'declared':text,'version':version,'satisfied':version is not None and req.specifier.contains(version)})
for dist in sorted(metadata.distributions(),key=lambda d:d.metadata['Name'].lower()):
    name=dist.metadata['Name']
    files=dist.files or []
    verified,unhashed=0,[]
    for f in files:
        p=Path(dist.locate_file(f))
        if f.hash:
            value=base64.urlsafe_b64encode(hashlib.new(f.hash.mode,p.read_bytes()).digest()).decode().rstrip('=') if p.is_file() else None
            if value!=f.hash.value: result['integrity_errors'].append(str(p))
            else: verified+=1
        else: unhashed.append(str(f))
    result['installed_distributions'].append({'name':name,'version':dist.version,'metadata_path':str(dist._path),
                                             'RECORD_hashes_verified':verified,'unhashed_RECORD_entries':unhashed})
    for text in dist.requires or []:
        req=Requirement(text)
        if req.marker and not req.marker.evaluate({**default_environment(),'extra':''}): continue
        try: v=metadata.version(req.name)
        except metadata.PackageNotFoundError: v=None
        if v is None or not req.specifier.contains(v): result['transitive_errors'].append({'distribution':name,'requirement':text,'installed':v})
for name in ['pytest','pydantic','typer','rich','mcp','readchar','pathspec','specify_cli']:
    module=importlib.util.find_spec(name)
    result['modules'][name]=module.origin if module else None
result['all_declared_satisfied']=all(r['satisfied'] for r in result['requirements'])
result['dependency_scope_verified']=result['all_declared_satisfied'] and not result['integrity_errors'] and not result['transitive_errors']
output=sys.argv[1] if len(sys.argv)>1 else 'environment-verified.json'
assert output in ['environment-verified.json','environment-final-verified.json']
(REPORT/output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['version','all_declared_satisfied','dependency_scope_verified','integrity_errors','transitive_errors','modules']}))
raise SystemExit(not result['dependency_scope_verified'])
