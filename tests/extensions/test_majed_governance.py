"""Focused qualification tests for the Majed governance extension."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXT_DIR = PROJECT_ROOT / "extensions" / "majed-governance"
SCRIPT_PATH = EXT_DIR / "scripts" / "python" / "governance_core.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("majed_governance_core", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_record() -> dict:
    return {
        "schema_version": "1.0",
        "record_id": "MSK-GOV-REC-001",
        "revision": "rev-1",
        "requirements": [
            {
                "id": "MSK-01",
                "source": "docs/request.md#req-1",
                "obligation": "Preserve the requested outcome and constraints.",
                "acceptance_criteria": ["The request and non-goals are recorded."],
                "status": "COMPLETE",
                "evidence": [
                    {
                        "id": "EV-001",
                        "kind": "test",
                        "path": "tests/example.py",
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
                    "scope": "focused component review",
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
            }
        ],
        "acceptance": {"status": "PENDING", "owner": "", "source": ""},
        "budget": {"status": "NO_TELEMETRY", "limits": {}},
    }


def _codes(result: dict) -> set[str]:
    return {finding["code"] for finding in result["findings"]}


def test_valid_record_passes():
    module = _load_module()
    result = module.validate_record(_base_record())
    assert result["status"] == "PASS", result
    assert not [f for f in result["findings"] if f["severity"] == "ERROR"]


def test_complete_without_evidence_is_rejected():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["evidence"] = []
    result = module.validate_record(record)
    assert result["status"] == "FINDINGS"
    assert "UNSUPPORTED_COMPLETION" in _codes(result)


def test_self_asserted_evidence_cannot_support_complete():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["evidence"][0]["provenance"] = "SELF_ASSERTED"
    result = module.validate_record(record)
    assert "SELF_ASSERTED_COMPLETION" in _codes(result)


def test_stale_evidence_revision_is_rejected():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["evidence"][0]["revision"] = "rev-0"
    result = module.validate_record(record)
    assert "STALE_EVIDENCE" in _codes(result)


def test_false_independence_is_rejected():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["review"] = {
        "status": "INDEPENDENT",
        "independent": False,
        "reviewer": "same-agent",
    }
    result = module.validate_record(record)
    assert "FALSE_INDEPENDENCE" in _codes(result)


def test_model_supplied_owner_approval_is_not_authorization():
    module = _load_module()
    record = _base_record()
    req = record["requirements"][0]
    req["status"] = "PENDING"
    req["protected"] = True
    req["owner_approved"] = True
    req["authorization"] = {"status": "NOT_VERIFIED", "source": "MODEL_OUTPUT"}
    result = module.validate_record(record)
    assert "AUTHORIZATION_NOT_VERIFIED" in _codes(result)
    assert "UNTRUSTED_OWNER_APPROVAL_FIELD" in _codes(result)


def test_expired_authorization_is_rejected():
    module = _load_module()
    record = _base_record()
    req = record["requirements"][0]
    req["status"] = "PENDING"
    req["protected"] = True
    req["authorization"] = {
        "status": "GRANTED",
        "source": "OWNER_RECORD",
        "expires_at": "2020-01-01T00:00:00Z",
    }
    result = module.validate_record(record)
    assert "EXPIRED_AUTHORIZATION" in _codes(result)


def test_duplicate_ids_are_rejected():
    module = _load_module()
    record = _base_record()
    record["requirements"].append(copy.deepcopy(record["requirements"][0]))
    result = module.validate_record(record)
    assert "DUPLICATE_REQUIREMENT_ID" in _codes(result)


def test_control_implemented_without_enforcement_is_rejected():
    module = _load_module()
    record = _base_record()
    record["controls"][0]["enforcement_type"] = "NONE"
    result = module.validate_record(record)
    assert "UNSUPPORTED_ENFORCEMENT" in _codes(result)


def test_missing_required_control_is_reported():
    module = _load_module()
    result = module.validate_record(_base_record(), required_controls=["D2"])
    assert "MISSING_CONTROL" in _codes(result)


def test_invalid_schema_is_invalid():
    module = _load_module()
    result = module.validate_record({"schema_version": "2.0"})
    assert result["status"] == "INVALID"


def test_unauthenticated_acceptance_is_rejected():
    module = _load_module()
    record = _base_record()
    record["acceptance"] = {
        "status": "ACCEPTED",
        "owner": "owner-1",
        "source": "OWNER_RECORD",
        "authenticated": False,
    }
    result = module.validate_record(record)
    assert "UNAUTHENTICATED_ACCEPTANCE" in _codes(result)


def test_inventory_entry_cannot_authorize_a_protected_action():
    module = _load_module()
    record = _base_record()
    req = record["requirements"][0]
    req["status"] = "PENDING"
    req["protected"] = True
    req["authorization"] = {"status": "GRANTED", "source": "INVENTORY"}
    result = module.validate_record(record)
    assert "UNTRUSTED_AUTHORIZATION_SOURCE" in _codes(result)
    assert "AUTHORIZATION_NOT_VERIFIED" in _codes(result)


def test_enforced_budget_without_meter_is_rejected():
    module = _load_module()
    record = _base_record()
    record["budget"] = {"status": "ENFORCED", "limits": {"retries": 2}, "meter": ""}
    result = module.validate_record(record)
    assert "UNSUPPORTED_BUDGET" in _codes(result)


def test_schema_and_template_are_valid_json():
    schema = json.loads(
        (EXT_DIR / "schemas" / "governance-record.schema.json").read_text(encoding="utf-8")
    )
    template = json.loads(
        (EXT_DIR / "templates" / "governance-record.json").read_text(encoding="utf-8")
    )
    assert schema["properties"]["requirements"]["type"] == "array"
    assert template["schema_version"] == "1.0"


def test_trace_and_decision_views_are_derived_and_non_authoritative():
    module = _load_module()
    record = _base_record()
    record["requirements"][0]["status"] = "PENDING"
    trace = module.trace_markdown(record)
    decision = module.decision_markdown(record)
    assert "DERIVED / NON-AUTHORITATIVE" in trace
    assert "MSK-01" in trace
    assert "OWNER_DECISION_REQUIRED" in decision
    assert "MSK-01" in decision


def test_cli_exit_codes(tmp_path):
    module = _load_module()
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    invalid = tmp_path / "invalid.json"
    good.write_text(json.dumps(_base_record()), encoding="utf-8")
    bad_record = _base_record()
    bad_record["requirements"][0]["evidence"] = []
    bad.write_text(json.dumps(bad_record), encoding="utf-8")
    invalid.write_text("{not-json", encoding="utf-8")

    assert module.main(["check", "--record", str(good), "--json"]) == 0
    assert module.main(["check", "--record", str(bad), "--json"]) == 2
    assert module.main(["check", "--record", str(invalid), "--json"]) == 3


def test_manifest_and_command_layout():
    manifest = yaml.safe_load((EXT_DIR / "extension.yml").read_text(encoding="utf-8"))
    assert manifest["extension"]["id"] == "majed-governance"
    commands = {entry["name"] for entry in manifest["provides"]["commands"]}
    assert commands == {
        "speckit.majed-governance.check",
        "speckit.majed-governance.trace",
        "speckit.majed-governance.decide",
    }
    for entry in manifest["provides"]["commands"]:
        assert (EXT_DIR / entry["file"]).is_file()


def test_extension_installs_from_directory(tmp_path):
    from specify_cli.extensions import ExtensionManager

    (tmp_path / ".specify").mkdir()
    manager = ExtensionManager(tmp_path)
    manifest = manager.install_from_directory(
        EXT_DIR, "1.3.3.dev0", register_commands=False
    )
    assert manifest.id == "majed-governance"
    assert manager.registry.is_installed("majed-governance")
    assert (
        tmp_path
        / ".specify"
        / "extensions"
        / "majed-governance"
        / "scripts"
        / "python"
        / "governance_core.py"
    ).is_file()
