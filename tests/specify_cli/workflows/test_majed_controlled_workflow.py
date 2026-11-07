"""Focused qualification tests for the Majed controlled workflow."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.engine import (
    WorkflowDefinition,
    WorkflowEngine,
    validate_workflow,
)

REPO_ROOT = Path(__file__).parents[3]
WORKFLOW_DIR = REPO_ROOT / "workflows" / "majed-controlled"
WORKFLOW_FILE = WORKFLOW_DIR / "workflow.yml"


def _install_workflow(project: Path) -> Path:
    extension = project / ".specify" / "extensions" / "majed-governance"
    shutil.copytree(REPO_ROOT / "extensions" / "majed-governance", extension)
    destination = project / ".specify" / "workflows" / "majed-controlled"
    shutil.copytree(WORKFLOW_DIR, destination)
    return destination / "workflow.yml"


def _definition() -> WorkflowDefinition:
    return WorkflowDefinition.from_yaml(WORKFLOW_FILE)


def _env_path(monkeypatch) -> None:
    scripts = str(Path(sys.executable).parent)
    monkeypatch.setenv("PATH", scripts + os.pathsep + os.environ.get("PATH", ""))


def _record() -> dict:
    return {
        "schema_version": "1.0",
        "record_id": "MSK-GOV-REC-WF",
        "revision": "rev-1",
        "requirements": [
            {
                "id": "MSK-01",
                "source": "request",
                "obligation": "Preserve the request.",
                "acceptance_criteria": ["Recorded."],
                "status": "PENDING",
                "evidence": [],
            }
        ],
    }


def test_definition_is_valid_and_declares_expected_routes():
    definition = _definition()
    assert definition.id == "majed-controlled"
    assert validate_workflow(definition) == []

    data = definition.data
    step_ids = {step["id"] for step in data["steps"]}
    assert "preflight" in step_ids
    assert "route" in step_ids
    assert "close" in step_ids

    route = next(step for step in data["steps"] if step["id"] == "route")
    assert route["type"] == "switch"
    assert set(route["cases"]) == {"assess", "execute"}


def test_controlled_assess_without_evidence_fails_safely(tmp_path, monkeypatch):
    _env_path(monkeypatch)
    project = tmp_path / "project"
    project.mkdir()
    _install_workflow(project)

    engine = WorkflowEngine(project)
    state = engine.execute(
        _definition(),
        inputs={
            "task": "demonstrate governed change",
            "profile": "controlled",
            "mode": "assess",
            "evidence_path": "",
            "review_verdict": "approve",
            "accept_verdict": "pending",
        },
    )

    assert state.status == RunStatus.FAILED
    preflight = state.step_results["preflight"]["output"]
    assert '"status": "BLOCKED"' in preflight["stdout"]
    assert "controlled" in preflight["stdout"]


def test_quick_assess_without_evidence_completes(tmp_path, monkeypatch):
    _env_path(monkeypatch)
    project = tmp_path / "project"
    project.mkdir()
    _install_workflow(project)

    engine = WorkflowEngine(project)
    state = engine.execute(
        _definition(),
        inputs={
            "task": "small reversible change",
            "profile": "quick",
            "mode": "assess",
            "evidence_path": "",
            "review_verdict": "approve",
            "accept_verdict": "pending",
        },
    )

    assert state.status == RunStatus.COMPLETED
    evidence = (
        project
        / ".specify"
        / "workflows"
        / "majed-controlled"
        / "evidence"
        / f"{state.run_id}.json"
    )
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    assert payload["derived"] is True
    assert payload["owner_acceptance"] == "NOT_GRANTED"
    assert payload["close"]["acceptance_status"] == "PENDING"


def test_controlled_assess_with_evidence_completes(tmp_path, monkeypatch):
    _env_path(monkeypatch)
    project = tmp_path / "project"
    project.mkdir()
    _install_workflow(project)
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(_record()), encoding="utf-8")

    engine = WorkflowEngine(project)
    state = engine.execute(
        _definition(),
        inputs={
            "task": "governed change with a record",
            "profile": "controlled",
            "mode": "assess",
            "evidence_path": str(record_path),
            "review_verdict": "approve",
            "accept_verdict": "pending",
        },
    )

    assert state.status == RunStatus.COMPLETED
    evidence = (
        project
        / ".specify"
        / "workflows"
        / "majed-controlled"
        / "evidence"
        / f"{state.run_id}.json"
    )
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    assert payload["profile"] == "controlled"
    assert payload["preflight"]["status"] == "PASS"


def test_pause_then_resume_at_review_gate(tmp_path, monkeypatch):
    _env_path(monkeypatch)
    project = tmp_path / "project"
    project.mkdir()
    _install_workflow(project)

    engine = WorkflowEngine(project)
    paused = engine.execute(
        _definition(),
        inputs={
            "task": "pause and resume",
            "profile": "standard",
            "mode": "assess",
            "evidence_path": "",
            "review_verdict": "",
            "accept_verdict": "",
        },
    )
    assert paused.status == RunStatus.PAUSED
    assert paused.current_step_id == "review-gate"

    resumed = engine.resume(
        paused.run_id,
        inputs={"review_verdict": "approve", "accept_verdict": "pending"},
    )
    assert resumed.status == RunStatus.COMPLETED


def test_execute_branch_contains_existing_commands():
    definition = _definition()
    route = next(step for step in definition.data["steps"] if step["id"] == "route")
    execute_steps = route["cases"]["execute"]
    profiles = next(
        step for step in execute_steps if step["id"] == "delivery"
    )["cases"]
    controlled = profiles["controlled"]
    commands = {
        step.get("command") for step in controlled if isinstance(step, dict)
    }
    assert {"speckit.specify", "speckit.clarify", "speckit.plan", "speckit.tasks"}.issubset(
        commands
    )
    assert "speckit.implement" in commands
