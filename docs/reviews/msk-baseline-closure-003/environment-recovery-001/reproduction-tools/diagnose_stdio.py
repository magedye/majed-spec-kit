"""Bounded native stdio reproduction retaining the server stderr lost by test."""
from pathlib import Path
from datetime import datetime,timezone
import asyncio
import json
import os
import sys
import traceback

ROOT=Path(r'D:\APP\maged-spec-kit\majed-spec-kit\specs\003-msk-baseline-closure\execution-worktree')
REPORT=ROOT/'docs/reviews/msk-baseline-closure-003/environment-recovery-001/stdio-diagnostic-001'

async def main():
    REPORT.mkdir(exist_ok=False)
    profile=Path(r'D:\APP\maged-spec-kit\msk003-qualification-temp-20261107-001')/'stdio-diagnostic-profile'
    profile.mkdir(exist_ok=False)
    os.environ['HOME']=str(profile);os.environ['USERPROFILE']=str(profile)
    for name in ['GH_TOKEN','GITHUB_TOKEN','OPENAI_API_KEY','ANTHROPIC_API_KEY']:os.environ.pop(name,None)
    from mcp import ClientSession,StdioServerParameters,stdio_client
    parameters=StdioServerParameters(command=sys.executable,args=['-c','from specify_cli import main; main()','mcp'],cwd=ROOT)
    state={'started_at_utc':datetime.now(timezone.utc).isoformat(),'interpreter':sys.executable,
           'server_argv':[sys.executable,*parameters.args],'timeout_seconds':12,
           'profile':str(profile),'scope':'Single local initialize request; no model/provider/service deployment'}
    try:
        with (REPORT/'server.stderr.txt').open('w',encoding='utf-8') as errlog:
            async with asyncio.timeout(12):
                async with stdio_client(parameters,errlog=errlog) as (read,write):
                    async with ClientSession(read,write,read_timeout_seconds=10) as session:
                        value=await session.initialize()
                        state['initialized']=value.model_dump(mode='json')
        state['result']='INITIALIZE_PASSED_DIAGNOSTIC_ONLY'
    except BaseException:
        (REPORT/'client.error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        state['result']='INITIALIZE_FAILED_OR_TIMED_OUT'
    state['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    (REPORT/'receipt.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state))

if __name__=='__main__':asyncio.run(main())
