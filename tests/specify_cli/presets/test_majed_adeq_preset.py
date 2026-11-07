"""Focused qualification tests for the bundled Majed ADEQ preset."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.presets import PresetManager, PresetResolver
from tests.conftest import strip_ansi

REPO_ROOT = Path(__file__).parents[3]
PRESET_DIR = REPO_ROOT / "presets" / "majed-adeq"


def _seed_core_templates(project_dir: Path) -> None:
    templates = project_dir / ".specify" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    (templates / "tasks-template.md").write_text("# Core Tasks Template\n", encoding="utf-8")
    (templates / "checklist-template.md").write_text(
        "# Core Checklist Template\n", encoding="utf-8"
    )
    commands = templates / "commands"
    commands.mkdir(parents=True, exist_ok=True)
    (commands / "clarify.md").write_text("# CORE CLARIFY BODY\n", encoding="utf-8")


def _install(project_dir: Path):
    manager = PresetManager(project_dir)
    return manager.install_from_directory(PRESET_DIR, "1.3.3.dev0", priority=5)


def _resolve(project_dir: Path, name: str, *, template_type: str = "template"):
    content = PresetResolver(project_dir).resolve_content(name, template_type)
    assert content is not None
    return content


def _cli_resolve(project_dir: Path, name: str):
    with patch.object(Path, "cwd", return_value=project_dir):
        result = CliRunner().invoke(app, ["preset", "resolve", name])
    assert result.exit_code == 0, (result.output, result.exception)
    return strip_ansi(result.output)


def test_manifest_declares_composable_contributions():
    manifest = yaml.safe_load((PRESET_DIR / "preset.yml").read_text(encoding="utf-8"))

    assert manifest["preset"]["id"] == "majed-adeq"
    assert manifest["requires"]["speckit_version"]
    entries = manifest["provides"]["templates"]
    by_name = {entry["name"]: entry for entry in entries}
    assert by_name["spec-template"]["strategy"] == "append"
    assert by_name["plan-template"]["strategy"] == "append"
    assert by_name["tasks-template"]["strategy"] == "append"
    assert by_name["checklist-template"]["strategy"] == "append"
    assert by_name["speckit.clarify"]["strategy"] == "wrap"
    assert "{CORE_TEMPLATE}" in (PRESET_DIR / by_name["speckit.clarify"]["file"]).read_text(
        encoding="utf-8"
    )


def test_install_and_append_spec_and_plan(project_dir):
    _seed_core_templates(project_dir)
    manifest = _install(project_dir)

    assert manifest.id == "majed-adeq"
    assert manifest.version == "1.0.0"

    spec = _resolve(project_dir, "spec-template")
    assert "Core Spec Template" in spec
    assert "ADEQ Decision Quality" in spec
    assert "Obligation Trace" in spec

    plan = _resolve(project_dir, "plan-template")
    assert "ADEQ Alternatives and Trade-offs" in plan
    assert "Impact, Dependencies, and Recovery" in plan
    assert "Confidence and Uncertainty" in plan


def test_install_and_append_tasks_and_checklist(project_dir):
    _seed_core_templates(project_dir)
    _install(project_dir)

    tasks = _resolve(project_dir, "tasks-template")
    assert "ADEQ Verification and Evidence" in tasks

    checklist = _resolve(project_dir, "checklist-template")
    assert "ADEQ Decision-Quality Checklist" in checklist


def test_wrap_clarify_preserves_core_body(project_dir):
    _seed_core_templates(project_dir)
    _install(project_dir)

    resolved = _resolve(project_dir, "speckit.clarify", template_type="command")
    assert "CORE CLARIFY BODY" in resolved
    assert "ADEQ Clarification Guard" in resolved

    path_output = _cli_resolve(project_dir, "speckit.clarify")
    assert "speckit.clarify" in "".join(path_output.split())
