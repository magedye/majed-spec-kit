"""Completion tests for the Majed governance extension (MSK-CORE-002)."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "majed-governance"
SCRIPT_PATH = EXT_DIR / "scripts" / "python" / "governance_core.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "majed_governance_core_completion", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_record() -> dict:
    return {
        "schema_version": "1.0",
        "record_id": "MSK-GOV-REC-002",
        "revision": "rev-1",
        "requirements": [
            {
                "id": "MSK-01",
                "source": {
                    "path": "docs/request.md",
                    "line_start": 1,
                    "line_end": 4,
                    "revision": "rev-1",
                },
                "obligation": "Preserve the request and its constraints.",
                "acceptance_criteria": ["The request and non-goals are recorded."],
                "status": "COMPLETE",
                "required": True,
                "component": "majed-adeq",
                "tests": ["tests/specify_cli/presets/test_majed_adeq_preset.py"],
                "evidence": [
                    {
                        "id": "EV-001",
                        "kind": "test",
                        "path": "tests/specify_cli/presets/test_majed_adeq_preset.py",
                        "revision": "rev-1",
                        "result": "PASS",
                        "provenance": "TOOL_OUTPUT",
                        "summary": "Focused test passed.",
                    }
                ],
                "authorization": {"status": "NOT_REQUIRED"},
                "review": {
                    "status": "INDEPENDENT",
                    "independent": True,
                    "reviewer": "reviewer-1",
                    "scope": "component review",
                },
            }
        ],
        "controls": [
            {
                "id": "MSK-C-D1-001",
                "domain": "D1",
                "status": "IMPLEMENTED",
                "enforcement_type": "ADVISORY",
                "verification_status": "PASS",
                "evidence_ids": ["EV-001"],
                "requirement_ids": ["MSK-01"],
            }
        ],
        "acceptance": {"status": "PENDING", "owner": "", "source": ""},
        "budget": {"status": "NO_TELEMETRY", "limits": {}},
    }


def _codes(result: dict) -> set[str]:
    return {finding["code"] for finding in result["findings"]}


def test_required_requirement_needs_component_and_test_links():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["component"] = ""
    record["requirements"][0]["tests"] = []
    result = module.validate_record(record)
    assert "MISSING_COMPONENT_LINK" in _codes(result)
    assert "MISSING_TEST_LINK" in _codes(result)


def test_source_object_stale_revision_is_rejected():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["source"]["revision"] = "rev-0"
    result = module.validate_record(record)
    assert "STALE_SOURCE_REVISION" in _codes(result)


def test_duplicate_evidence_id_is_rejected():
    module = _load_module()
    record = _base_record()
    second = copy.deepcopy(record["requirements"][0])
    second["id"] = "MSK-02"
    record["requirements"].append(second)
    result = module.validate_record(record)
    assert "DUPLICATE_EVIDENCE_ID" in _codes(result)


def test_accepted_acceptance_with_open_requirement_is_rejected():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["status"] = "PENDING"
    record["acceptance"] = {
        "status": "ACCEPTED",
        "owner": "owner-1",
        "source": "OWNER_RECORD",
        "authenticated": True,
    }
    result = module.validate_record(record)
    assert "ACCEPTANCE_WITH_OPEN_REQUIREMENTS" in _codes(result)


def test_control_requirement_link_must_exist():
    module = _load_module()
    record = _base_record()
    record["controls"][0]["requirement_ids"] = ["MSK-99"]
    result = module.validate_record(record)
    assert "MISSING_CONTROL_REQUIREMENT" in _codes(result)


def test_intake_extracts_normative_candidates_with_spans(tmp_path):
    module = _load_module()
    source = tmp_path / "request.md"
    source.write_text(
        "# Requirements\n"
        "- The system MUST preserve the source request.\n"
        "- The system SHOULD explain options.\n"
        "## Non-Goals\n"
        "- No production deployment.\n"
        "## المتطلبات\n"
        "- يجب حفظ النص الأصلي.\n",
        encoding="utf-8",
    )
    record = module.intake_source(source, revision="rev-1", record_id="INTAKE-1")
    assert record["intake"]["status"] == "PARSED"
    assert record["intake"]["candidate_count"] >= 4
    first = record["requirements"][0]
    assert first["status"] == "PENDING"
    assert first["source"]["revision"] == "rev-1"
    assert first["source"]["line_start"] == 2
    assert first["source"]["path"].replace("\\", "/").endswith("request.md")
    assert first["acceptance_criteria"] == []
    assert first["evidence"] == []


def test_intake_requires_a_revision(tmp_path):
    module = _load_module()
    source = tmp_path / "request.md"
    source.write_text("# Requirements\n- MUST do the thing.\n", encoding="utf-8")
    output = tmp_path / "record.json"
    assert (
        module.main(
            [
                "intake",
                "--source",
                str(source),
                "--revision",
                "",
                "--output",
                str(output),
            ]
        )
        == 3
    )


def test_trace_includes_source_component_and_linkage():
    module = _load_module()
    trace = module.trace_markdown(_base_record())
    assert "docs/request.md:1-4" in trace
    assert "majed-adeq" in trace


def test_impact_reports_unmatched_path_and_missing_rollback():
    module = _load_module()
    impact_map = {
        "schema_version": "1.0",
        "paths": [
            {
                "prefix": "presets/",
                "component": "majed-adeq",
                "kind": "preset",
                "risk": "HIGH",
                "reversible": False,
            }
        ],
    }
    result = module.impact_report(
        ["presets/majed-adeq/preset.yml", "docs/unmapped.md"],
        impact_map,
        rollback="",
    )
    assert "UNMATCHED_PATH" in _codes(result)
    assert "MISSING_ROLLBACK" in _codes(result)


def test_impact_accepts_matched_reversible_change():
    module = _load_module()
    impact_map = {
        "schema_version": "1.0",
        "paths": [
            {
                "prefix": "tests/",
                "component": "majed-governance",
                "kind": "test",
                "risk": "LOW",
                "reversible": True,
            }
        ],
    }
    result = module.impact_report(
        ["tests/extensions/test_majed_governance.py"],
        impact_map,
        rollback="revert the commit",
    )
    assert result["status"] == "PASS"
    assert result["components"] == ["majed-governance"]


def test_sources_manifest_detects_hash_mismatch_and_unknown_supersedes(tmp_path):
    module = _load_module()
    source = tmp_path / "policy.md"
    source.write_text("policy\n", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0",
        "sources": [
            {
                "id": "policy",
                "priority": 1,
                "path": "policy.md",
                "revision": "rev-1",
                "sha256": digest,
                "authority": "PROJECT_POLICY",
                "scope": "governance",
            }
        ],
    }
    result = module.validate_sources(manifest, root=tmp_path)
    assert result["status"] == "PASS"

    source.write_text("changed\n", encoding="utf-8")
    result = module.validate_sources(manifest, root=tmp_path)
    assert "SOURCE_HASH_MISMATCH" in _codes(result)

    manifest["sources"][0]["supersedes"] = "missing-source"
    result = module.validate_sources(manifest, root=tmp_path)
    assert "UNKNOWN_SUPERSEDES" in _codes(result)


def test_converge_groups_bounded_actions():
    module = _load_module()
    record = _base_record()
    req = record["requirements"][0]
    req["status"] = "PENDING"
    req["evidence"] = []
    req["protected"] = True
    req["authorization"] = {"status": "NOT_VERIFIED"}
    req["review"] = {"status": "PENDING", "independent": False}
    items = module.converge_items(record)
    assert len(items) == 1
    actions = set(items[0]["actions"])
    assert {"ADD_EVIDENCE", "OBTAIN_AUTHORIZATION", "OBTAIN_INDEPENDENT_REVIEW"}.issubset(
        actions
    )


def test_converge_apply_writes_a_derived_plan_without_mutating_the_record(tmp_path):
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["status"] = "PENDING"
    record["requirements"][0]["evidence"] = []
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    output = tmp_path / "remediation.json"

    assert (
        module.main(
            [
                "converge",
                "--record",
                str(record_path),
                "--apply",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    plan = json.loads(output.read_text(encoding="utf-8"))
    assert plan["derived"] is True
    assert len(plan["items"]) == 1
    assert json.loads(record_path.read_text(encoding="utf-8")) == record


def test_sources_priority_order_is_derived(tmp_path):
    module = _load_module()
    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    first.write_text("a\n", encoding="utf-8")
    second.write_text("b\n", encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "sources": [
            {
                "id": "second",
                "priority": 2,
                "path": "b.md",
                "revision": "rev-1",
                "sha256": hashlib.sha256(second.read_bytes()).hexdigest(),
                "authority": "REFERENCE",
            },
            {
                "id": "first",
                "priority": 1,
                "path": "a.md",
                "revision": "rev-1",
                "sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
                "authority": "PROJECT_POLICY",
            },
        ],
    }
    result = module.validate_sources(manifest, root=tmp_path)
    assert result["status"] == "PASS"
    assert result["summary"]["effective_order"] == ["first", "second"]


def test_metrics_reports_counts():
    module = _load_module()
    report = module.metrics_report(_base_record())
    assert report["requirements"]["total"] == 1
    assert report["requirements"]["required"] == 1
    assert report["requirements"]["required_complete"] == 1
    assert report["evidence"]["by_provenance"]["TOOL_OUTPUT"] == 1
    assert report["controls"]["by_domain"]["D1"] == 1
    assert report["acceptance_status"] == "PENDING"


def test_version_requirement():
    module = _load_module()
    assert module.main(["version", "--require", "1.0.0"]) == 0
    assert module.main(["version", "--require", "2.0.0"]) == 2


def test_cli_intake_impact_converge_sources_and_metrics(tmp_path):
    module = _load_module()
    source = tmp_path / "request.md"
    source.write_text("# Requirements\n- MUST preserve the request.\n", encoding="utf-8")
    record_path = tmp_path / "record.json"
    assert (
        module.main(
            [
                "intake",
                "--source",
                str(source),
                "--revision",
                "rev-1",
                "--output",
                str(record_path),
            ]
        )
        == 0
    )
    assert record_path.is_file()

    impact_map = tmp_path / "impact.json"
    impact_map.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "paths": [
                    {
                        "prefix": "docs/",
                        "component": "docs",
                        "kind": "documentation",
                        "risk": "LOW",
                        "reversible": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert (
        module.main(
            [
                "impact",
                "--map",
                str(impact_map),
                "--files",
                "other/missing.md",
                "--json",
            ]
        )
        == 2
    )
    assert module.main(["converge", "--record", str(record_path), "--check"]) == 2
    assert module.main(["metrics", "--record", str(record_path), "--json"]) == 0

    manifest = tmp_path / "sources.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "sources": [
                    {
                        "id": "policy",
                        "priority": 1,
                        "path": "request.md",
                        "revision": "rev-1",
                        "sha256": "0" * 64,
                        "authority": "PROJECT_POLICY",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert (
        module.main(
            [
                "sources",
                "--manifest",
                str(manifest),
                "--root",
                str(tmp_path),
                "--json",
            ]
        )
        == 2
    )
