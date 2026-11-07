"""Fail-fast local documentation checkpoint; no merge/push/qualification grant."""
from datetime import datetime, timezone
import json
import subprocess
import sys

from preflight import ROOT, HERE, write


def main():
    run_id, message = sys.argv[1:]
    if not __import__('re').fullmatch(r'[a-z0-9-]+', run_id):
        raise ValueError('Unsafe evidence run id')
    folder = HERE / run_id
    folder.mkdir(exist_ok=False)
    git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    if git('branch', '--show-current') != 'fix/msk-baseline-closure-003-qualified':
        raise ValueError('Not authorized task branch')
    receipt = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'before': git('rev-parse', 'HEAD'),
               'commands': [], 'result': 'RUNNING', 'commit_scope': 'DOCUMENTARY_EVIDENCE_ONLY; all product qualification blockers retained'}

    def run(label, argv):
        result = subprocess.run(argv, cwd=ROOT, capture_output=True)
        (folder / (label + '.stdout.txt')).write_bytes(result.stdout)
        (folder / (label + '.stderr.txt')).write_bytes(result.stderr)
        receipt['commands'].append({'label': label, 'command': argv, 'exit_code': result.returncode})
        if result.returncode:
            raise subprocess.CalledProcessError(result.returncode, argv)

    try:
        verifier = [sys.executable, '-B', str(HERE / 'verify_package.py')]
        run('pre-stage', verifier)
        run('stage', ['git', 'add', '--', 'docs/reviews/msk-baseline-closure-003/'])
        staged = git('diff', '--cached', '--name-only').splitlines()
        if not staged or any(not p.startswith('docs/reviews/msk-baseline-closure-003/') for p in staged):
            raise ValueError('Staged changes exceed documentary checkpoint scope')
        run('staged-verification', verifier)
        run('commit', ['git', 'commit', '-m', message, '-m',
            'MSK-BASELINE-CLOSURE-003: evidence checkpoint only; primary pytest/engine qualification remains blocked. No merge or push.\n\nAssisted-by: Codex (model: GPT-6, autonomous)'])
        receipt['result'] = 'SAVE_SUCCEEDED'
    except (subprocess.CalledProcessError, ValueError) as exc:
        receipt['result'] = 'SAVE_BLOCKED'
        receipt['error'] = str(exc)
    receipt.update({'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'after': git('rev-parse', 'HEAD'),
                    'branch': git('branch', '--show-current'), 'merge': False, 'push': False})
    write(folder / 'RESULT.json', receipt)
    print(json.dumps(receipt))
    return int(receipt['result'] != 'SAVE_SUCCEEDED')


if __name__ == '__main__':
    raise SystemExit(main())
