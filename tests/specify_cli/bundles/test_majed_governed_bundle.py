"""Focused installation and lifecycle tests for the Majed governed bundle."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundles.manifest import BundleManifest
from specify_cli.bundles.resolver import resolve_install_plan

REPO_ROOT = Path(__file__).parents[3]
BUNDLE_DIR = REPO_ROOT / "bundles" / "majed-governed"
BUNDLE_YML = BUNDLE_DIR / "bundle.yml"


def _invoke(project: Path, args: list[str]):
    return CliRunner().invoke(app, args)


def _records(project: Path) -> dict:
    return json.loads(
        (project / ".specify" / "bundle-records.json").read_text(encoding="utf-8")
    )


def test_manifest_is_structurally_valid_and_resolves_components():
    manifest = BundleManifest.from_file(BUNDLE_YML)
    assert manifest.bundle.id == "majed-governed"
    assert manifest.bundle.version == "1.1.0"

    plan = resolve_install_plan(
        manifest,
        speckit_version="1.3.3.dev0",
        active_integration=None,
    )
    assert plan.bundle_id == "majed-governed"
    assert {(c.kind, c.id) for c in plan.components} == {
        ("extensions", "majed-governance"),
        ("presets", "majed-adeq"),
        ("workflows", "majed-controlled"),
    }
    preset = next(c for c in plan.components if c.kind == "presets")
    assert preset.priority == 5
    assert preset.strategy == "append"

    kinds = [component.kind for component in plan.components]
    assert kinds.index("extensions") < kinds.index("workflows"), (
        "the governance extension must be planned before the dependent workflow"
    )


def test_install_list_reinstall_and_remove(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    installed = _invoke(
        tmp_path,
        [
            "bundle",
            "install",
            str(BUNDLE_YML),
            "--integration",
            "claude",
            "--offline",
        ],
    )
    assert installed.exit_code == 0, (installed.output, installed.exception)

    assert (tmp_path / ".specify" / "presets" / "majed-adeq").is_dir()
    assert (tmp_path / ".specify" / "extensions" / "majed-governance").is_dir()
    assert (tmp_path / ".specify" / "workflows" / "majed-controlled").is_dir()
    records = _records(tmp_path)
    bundle = next(item for item in records["bundles"] if item["bundle_id"] == "majed-governed")
    assert bundle["version"] == "1.1.0"

    listed = _invoke(tmp_path, ["bundle", "list", "--json"])
    assert listed.exit_code == 0
    assert "majed-governed" in listed.output

    repeated = _invoke(
        tmp_path,
        [
            "bundle",
            "install",
            str(BUNDLE_YML),
            "--integration",
            "claude",
            "--offline",
        ],
    )
    assert repeated.exit_code == 0, (repeated.output, repeated.exception)

    refreshed = _invoke(
        tmp_path,
        [
            "bundle",
            "install",
            str(BUNDLE_YML),
            "--integration",
            "claude",
            "--offline",
            "--refresh",
        ],
    )
    assert refreshed.exit_code == 0, (refreshed.output, refreshed.exception)

    user_file = tmp_path / ".specify" / "user-notes.md"
    user_file.write_text("user-owned\n", encoding="utf-8")
    removed = _invoke(tmp_path, ["bundle", "remove", "majed-governed"])
    assert removed.exit_code == 0, (removed.output, removed.exception)
    assert user_file.read_text(encoding="utf-8") == "user-owned\n"
    assert not (tmp_path / ".specify" / "presets" / "majed-adeq").exists()
    assert not (tmp_path / ".specify" / "extensions" / "majed-governance").exists()
    assert not (tmp_path / ".specify" / "workflows" / "majed-controlled").exists()


def test_bundle_build_and_install_artifact(tmp_path, monkeypatch):
    output = tmp_path / "dist"
    built = _invoke(
        REPO_ROOT,
        ["bundle", "build", "--path", str(BUNDLE_DIR), "--output", str(output)],
    )
    assert built.exit_code == 0, (built.output, built.exception)
    artifacts = list(output.glob("majed-governed-*.zip"))
    assert artifacts, "expected a versioned bundle artifact"
    artifact = artifacts[0]

    consumer = tmp_path / "consumer"
    consumer.mkdir()
    monkeypatch.chdir(consumer)
    installed = _invoke(
        consumer,
        [
            "bundle",
            "install",
            str(artifact),
            "--integration",
            "claude",
            "--offline",
        ],
    )
    assert installed.exit_code == 0, (installed.output, installed.exception)
    assert (consumer / ".specify" / "presets" / "majed-adeq").is_dir()
    assert (consumer / ".specify" / "extensions" / "majed-governance").is_dir()
    assert (consumer / ".specify" / "workflows" / "majed-controlled").is_dir()


def test_reinstall_preserves_a_user_modified_delivered_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    first = _invoke(
        tmp_path,
        [
            "bundle",
            "install",
            str(BUNDLE_YML),
            "--integration",
            "claude",
            "--offline",
        ],
    )
    assert first.exit_code == 0, (first.output, first.exception)

    target = (
        tmp_path
        / ".claude"
        / "skills"
        / "speckit-majed-governance-check"
        / "SKILL.md"
    )
    assert target.is_file(), "expected the governance skill to be delivered to the integration"
    target.write_text("USER MODIFIED COMMAND\n", encoding="utf-8")

    second = _invoke(
        tmp_path,
        [
            "bundle",
            "install",
            str(BUNDLE_YML),
            "--integration",
            "claude",
            "--offline",
        ],
    )
    assert second.exit_code == 0, (second.output, second.exception)
    assert target.read_text(encoding="utf-8") == "USER MODIFIED COMMAND\n"
