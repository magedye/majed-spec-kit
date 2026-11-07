"""Bounded stdlib-dispatcher and shell/display diagnostics, not CLI qualification."""
from pathlib import Path
from unittest.mock import patch
import ast
import hashlib
import io
import json
import os
import subprocess
import sys

from preflight import ROOT, HERE, REPORT, write


def source(revision, path):
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=ROOT).decode('utf-8')


def main():
    path = 'src/specify_cli/events/__init__.py'
    original = source('f74bdb8', path)
    candidate = source('ca3233a', path)

    def literal(text):
        return next(ast.literal_eval(n.value) for n in ast.parse(text).body
                    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_EVENTS_DISPATCHER_TEMPLATE' for t in n.targets))

    script = literal(original)
    assert script == literal(candidate)
    fixture = HERE / 'fixtures/dispatcher-001'
    fixture.mkdir(parents=True, exist_ok=False)
    assert fixture.resolve().is_relative_to(HERE.resolve())
    (fixture / 'events.py').write_text(script, encoding='utf-8')
    ns = {'__name__': 'msk_generated_dispatcher_diagnostic', '__file__': str(fixture / 'events.py')}
    exec(compile(script, str(fixture / 'events.py'), 'exec'), ns)
    rows = []

    def project(name, token='scripts/bash/boot.sh'):
        root = fixture / name
        commands = root / '.specify/templates/commands'
        commands.mkdir(parents=True)
        sh = root / '.specify/scripts/bash/boot.sh'
        sh.parent.mkdir(parents=True)
        sh.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
        cmd = commands / 'boot.md'
        cmd.write_text('---\nscripts:\n  sh: ' + token + '\n---\nBody\n', encoding='utf-8')
        return root, cmd, sh

    for name, available, expected in [
        ('no-launcher', {}, None),
        ('bash-selected', {'bash': r'C:\fixture\bash.exe'}, r'C:\fixture\bash.exe'),
        ('sh-fallback', {'sh': r'C:\fixture\sh.exe'}, r'C:\fixture\sh.exe')]:
        root, cmd, sh = project(name)
        with patch('shutil.which', side_effect=lambda n: available.get(n)):
            actual = ns['_resolve_argv'](cmd, root, None)
        assert actual is None if expected is None else actual == [expected, str(sh)]
        rows.append({'case': name, 'result': 'PASSED', 'expected_first_argv': expected,
                     'observed': actual, 'boundary': 'EXISTING_GENERATED_STDLIB_ARGV_SELECTION_ONLY'})
    for name, token in [('absolute-rejected', 'C:/outside/forbidden.sh'), ('traversal-rejected', '../../outside.sh'), ('malformed-quote', '"unterminated')]:
        root, cmd, _ = project(name, token)
        actual = ns['_resolve_argv'](cmd, root, None)
        assert actual is None
        rows.append({'case': name, 'result': 'PASSED', 'observed': actual, 'boundary': 'EXISTING_GENERATED_STDLIB_RESOLVER_ONLY'})
    root, cmd, _ = project('python-inline')
    py = root / '.specify/scripts/handler.py'
    py.write_text('from pathlib import Path\nPath("handled.txt").write_text("fixture only",encoding="utf-8")\n', encoding='utf-8')
    cmd.write_text('---\nscripts:\n  py: scripts/handler.py\n---\nBody\n', encoding='utf-8')
    actual = ns['_run_inline']('speckit.boot', '', root, 10)
    assert actual == 0 and (root / 'handled.txt').read_text(encoding='utf-8') == 'fixture only'
    rows.append({'case': 'python-inline-executes-owned-handler', 'result': 'PASSED', 'exit_code': actual,
                 'boundary': 'ACTUAL_GENERATED_STDLIB_HANDLER_EXECUTION; not SpecKit workflow or package qualification'})
    shell_runs = []
    for name, command in [('posix-true-on-windows', [os.environ.get('COMSPEC', r'C:\Windows\System32\cmd.exe'), '/d', '/c', 'true']),
                          ('portable-echo-on-windows', [os.environ.get('COMSPEC', r'C:\Windows\System32\cmd.exe'), '/d', '/c', 'echo noop'])]:
        r = subprocess.run(command, cwd=fixture, capture_output=True, timeout=10)
        (fixture / (name + '.stdout.txt')).write_bytes(r.stdout)
        (fixture / (name + '.stderr.txt')).write_bytes(r.stderr)
        shell_runs.append({'case': name, 'command': command, 'exit_code': r.returncode,
                           'boundary': 'ACTUAL_LOCAL_CMD_COMMAND_ONLY; workflow regression remains BLOCKED'})
    from rich.console import Console
    output = io.StringIO()
    Console(file=output, width=20, force_terminal=False, color_system=None).print('Error: artifact modified or is not owned')
    raw = output.getvalue()
    assert 'modified or is not owned' not in raw
    assert 'modified or is not owned' in ' '.join(raw.split())
    # The existing candidate retains exit code, user-file and registry-state
    # assertions; compare all other AST of this complete test function.
    test = 'tests/integrations/test_integration_generic.py'
    def statements(rev):
        fn = next(n for n in ast.parse(source(rev, test)).body if isinstance(n, ast.FunctionDef) and n.name == 'test_generic_extension_rejects_modified_artifact_on_disable')
        return [ast.dump(n, include_attributes=False) for n in fn.body
                if not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'normalized_output' for t in n.targets))
                and not (isinstance(n, ast.Assert) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Constant) and n.test.left.value == 'modified or is not owned')]
    assert statements('f74bdb8') == statements('ca3233a')
    write(REPORT / 'bounded-diagnostics.json', {'source_revisions': ['f74bdb893dcba23de72069b46ced5baaeb1684ea', 'ca3233afe5192ba01861098c429effea7e6a4f6c'],
        'generated_script_sha256': hashlib.sha256(script.encode()).hexdigest(), 'generated_cases': rows,
        'shell_runs': shell_runs, 'rich_wrap': {'raw': raw, 'raw_phrase_present': False, 'normalized_phrase_present': True,
            'other_semantic_assertions_unchanged_by_ast': True},
        'limits': ['Generated mirror is existing stdlib functionality, not a new policy engine.',
                   'Primary package import, event resolver integration and workflow test suites are blocked by missing dependencies.',
                   'No actual Bash/WSL runtime compatibility, source fix qualification, governance scenario or host-wide enforcement inferred.'],
        'product_files_changed': False, 'runtime_qualification': 'BLOCKED'})
    print(json.dumps({'generated_boundary_cases_passed': len(rows), 'shell_diagnostics': shell_runs,
        'rich_wrap_reproduced': True, 'full_package_qualification': 'BLOCKED'}))


if __name__ == '__main__':
    main()
