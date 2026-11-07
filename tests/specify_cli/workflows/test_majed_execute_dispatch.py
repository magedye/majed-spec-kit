"""Native command-dispatch qualification for majed-controlled execute mode.

The test installs a disposable stub CLI named ``claude`` on PATH. This exercises
the real integration dispatch path without invoking a real model or external
service. Actual agent behavior remains EXECUTE_NOT_VERIFIED.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

REPO_ROOT = Path(__file__).parents[3]
WORKFLOW_DIR = REPO_ROOT / "workflows" / "majed-controlled"


def _install(project: Path) -> None:
    shutil.copytree(
        REPO_ROOT / "extensions" / "majed-governance",
        project / ".specify" / "extensions" / "majed-governance",
    )
    shutil.copytree(
        WORKFLOW_DIR,
        project / ".specify" / "workflows" / "majed-controlled",
    )


def _make_stub(bin_dir: Path, log: Path) -> None:
    if os.name == "nt":
        csc = (
            Path(os.environ.get("WINDIR", r"C:\Windows"))
            / "Microsoft.NET"
            / "Framework64"
            / "v4.0.30319"
            / "csc.exe"
        )
        if not csc.is_file():
            pytest.skip("csc.exe unavailable; EXECUTE_NOT_VERIFIED")
        source = bin_dir / "stub.cs"
        source.write_text(
            "using System;\nusing System.IO;\n"
            "class Stub {\n"
            "  static int Main(string[] args) {\n"
            "    var log = Environment.GetEnvironmentVariable(\"STUB_LOG\");\n"
            "    if (!String.IsNullOrEmpty(log)) {\n"
            "      File.AppendAllText(log, String.Join(\" \", args) + Environment.NewLine);\n"
            "    }\n"
            "    return 0;\n"
            "  }\n"
            "}\n",
            encoding="utf-8",
        )
        subprocess.run(
            [str(csc), "/nologo", f"/out:{bin_dir / 'claude.exe'}", str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        stub = bin_dir / "claude"
        stub.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$STUB_LOG\"\nexit 0\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)


def test_quick_execute_dispatches_native_commands(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    _install(project)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "stub.log"
    _make_stub(bin_dir, log)

    scripts = str(Path(sys.executable).parent)
    monkeypatch.setenv(
        "PATH",
        str(bin_dir) + os.pathsep + scripts + os.pathsep + os.environ.get("PATH", ""),
    )
    monkeypatch.setenv("STUB_LOG", str(log))

    definition = WorkflowDefinition.from_yaml(WORKFLOW_DIR / "workflow.yml")
    engine = WorkflowEngine(project)
    state = engine.execute(
        definition,
        inputs={
            "task": "dispatch a disposable fixture",
            "profile": "quick",
            "mode": "execute",
            "integration": "claude",
            "review_verdict": "approve",
            "accept_verdict": "pending",
        },
    )

    assert state.status == RunStatus.COMPLETED, state.error
    assert state.step_results["quick-specify"]["output"]["dispatched"] is True
    assert state.step_results["quick-implement"]["output"]["dispatched"] is True

    calls = log.read_text(encoding="utf-8").splitlines()
    assert len(calls) >= 2
    joined = " ".join(calls).lower()
    assert "speckit-specify" in joined or "speckit.specify" in joined
    assert "speckit-implement" in joined or "speckit.implement" in joined


def test_standard_and_controlled_execute_routes_dispatch(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    _install(project)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "stub.log"
    _make_stub(bin_dir, log)
    scripts = str(Path(sys.executable).parent)
    monkeypatch.setenv(
        "PATH",
        str(bin_dir) + os.pathsep + scripts + os.pathsep + os.environ.get("PATH", ""),
    )
    monkeypatch.setenv("STUB_LOG", str(log))

    record = {
        "schema_version": "1.0",
        "record_id": "MSK-EXECUTE-DEMO",
        "revision": "rev-1",
        "requirements": [
            {
                "id": "MSK-01",
                "source": "docs/request.md",
                "obligation": "Preserve the request.",
                "acceptance_criteria": [],
                "status": "PENDING",
                "evidence": [],
                "authorization": {"status": "NOT_REQUIRED"},
                "review": {"status": "PENDING", "independent": False},
            }
        ],
        "controls": [],
        "acceptance": {"status": "PENDING", "owner": "", "source": ""},
        "budget": {"status": "NO_TELEMETRY", "limits": {}},
    }
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")

    definition = WorkflowDefinition.from_yaml(WORKFLOW_DIR / "workflow.yml")
    for profile, expected in (("standard", 4), ("controlled", 6)):
        log.write_text("", encoding="utf-8")
        engine = WorkflowEngine(project)
        inputs = {
            "task": f"dispatch {profile} fixture",
            "profile": profile,
            "mode": "execute",
            "integration": "claude",
            "review_verdict": "approve",
            "accept_verdict": "pending",
        }
        if profile == "controlled":
            inputs["evidence_path"] = str(record_path)
        state = engine.execute(definition, inputs=inputs)
        assert state.status == RunStatus.COMPLETED, (profile, state.error)
        calls = log.read_text(encoding="utf-8").splitlines()
        assert len(calls) == expected, (profile, calls)
        joined = " ".join(calls).lower()
        assert "speckit-specify" in joined or "speckit.specify" in joined
        assert "speckit-implement" in joined or "speckit.implement" in joined
