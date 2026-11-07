#!/usr/bin/env python3
"""Deterministic, read-only governance record checks for Majed Spec Kit.

The record is a project-owned JSON document. This script validates its shape,
detects unsupported completion claims, stale evidence, untrusted authorization,
false independence, and unsupported control claims. It does not authenticate an
owner, enforce host permissions, or replace Spec Kit status.

Exit codes:
  0  PASS (no errors; warnings are allowed)
  2  FINDINGS (one or more errors)
  3  INVALID input or unreadable record

Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
DOMAINS = {f"D{index}" for index in range(1, 7)}

REQUIREMENT_STATUSES = {
    "COMPLETE",
    "PARTIAL",
    "PENDING",
    "NOT_VERIFIED",
    "NOT_APPLICABLE",
}
EVIDENCE_RESULTS = {"PASS", "FAIL", "UNKNOWN"}
EVIDENCE_PROVENANCE = {
    "SELF_ASSERTED",
    "TOOL_OUTPUT",
    "INDEPENDENT_REVIEW",
    "OWNER_RECORD",
}
TRUSTED_EVIDENCE_PROVENANCE = {"TOOL_OUTPUT", "INDEPENDENT_REVIEW", "OWNER_RECORD"}
AUTHORIZATION_STATUSES = {
    "NOT_REQUIRED",
    "GRANTED",
    "PENDING",
    "NOT_VERIFIED",
    "NOT_GRANTED",
}
TRUSTED_AUTH_SOURCES = {
    "OWNER_RECORD",
    "SIGNED_OWNER_DECISION",
    "OWNER_APPROVED_SOURCE",
    "PROJECT_POLICY",
    "VERIFIED_DELEGATION",
}
UNTRUSTED_AUTH_SOURCES = {
    "MODEL_OUTPUT",
    "AGENT_REGISTRY",
    "INVENTORY",
    "SELF_ASSERTED",
    "CHAT",
    "LLM",
    "AGENT",
}
REVIEW_STATUSES = {"PENDING", "SELF_REVIEW", "INDEPENDENT", "NOT_VERIFIED"}
CONTROL_STATUSES = {
    "IMPLEMENTED",
    "PARTIAL",
    "DESIGNED_NOT_IMPLEMENTED",
    "NOT_APPLICABLE",
}
ENFORCEMENT_TYPES = {
    "NONE",
    "ADVISORY",
    "PRE_EXECUTION",
    "POST_EXECUTION",
    "OS",
    "NETWORK",
    "TOOL_GATEWAY",
    "UNKNOWN",
}
VERIFICATION_STATUSES = {
    "PASS",
    "FAIL",
    "NOT_RUN",
    "NOT_VERIFIED",
    "NOT_APPLICABLE",
}
ACCEPTANCE_STATUSES = {
    "PENDING",
    "ACCEPTED",
    "REJECTED",
    "NOT_GRANTED",
    "NOT_VERIFIED",
}
BUDGET_STATUSES = {"ENFORCED", "NO_TELEMETRY", "NOT_ENFORCED", "NOT_APPLICABLE"}


def _finding(
    code: str,
    severity: str,
    message: str,
    **context: Any,
) -> dict[str, Any]:
    data: dict[str, Any] = {"code": code, "severity": severity, "message": message}
    data.update({key: value for key, value in context.items() if value is not None})
    return data


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _parse_timestamp(value: Any) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evidence_path(path_text: str, root: Path | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if root is not None and not path.is_absolute():
        path = root / path
    return path


def _validate_authorization(
    requirement: dict[str, Any],
    findings: list[dict[str, Any]],
) -> str:
    req_id = _text(requirement.get("id"))
    protected = requirement.get("protected") is True
    authorization = requirement.get("authorization")
    if not isinstance(authorization, dict):
        if protected:
            findings.append(
                _finding(
                    "AUTHORIZATION_NOT_VERIFIED",
                    "ERROR",
                    "Protected requirement has no verifiable authorization record.",
                    requirement_id=req_id,
                )
            )
        return "NOT_RECORDED"

    status = _text(authorization.get("status")).upper()
    source = _text(authorization.get("source")).upper()
    if status not in AUTHORIZATION_STATUSES:
        findings.append(
            _finding(
                "INVALID_AUTHORIZATION_STATUS",
                "ERROR",
                f"Unknown authorization status {status!r}.",
                requirement_id=req_id,
            )
        )

    if source in UNTRUSTED_AUTH_SOURCES:
        findings.append(
            _finding(
                "UNTRUSTED_AUTHORIZATION_SOURCE",
                "ERROR",
                f"Authorization source {source!r} is not a trusted owner source.",
                requirement_id=req_id,
            )
        )

    if protected:
        if status != "GRANTED":
            findings.append(
                _finding(
                    "AUTHORIZATION_NOT_VERIFIED",
                    "ERROR",
                    "Protected requirement is not backed by a GRANTED authorization.",
                    requirement_id=req_id,
                )
            )
        elif source not in TRUSTED_AUTH_SOURCES:
            findings.append(
                _finding(
                    "AUTHORIZATION_NOT_VERIFIED",
                    "ERROR",
                    "Protected requirement authorization has no trusted source.",
                    requirement_id=req_id,
                )
            )

    expires_at = authorization.get("expires_at")
    if expires_at is not None:
        parsed = _parse_timestamp(expires_at)
        if parsed is None:
            findings.append(
                _finding(
                    "INVALID_AUTHORIZATION_EXPIRY",
                    "ERROR",
                    "Authorization expiry is not a valid ISO-8601 timestamp.",
                    requirement_id=req_id,
                )
            )
        elif status == "GRANTED" and parsed < datetime.now(timezone.utc):
            findings.append(
                _finding(
                    "EXPIRED_AUTHORIZATION",
                    "ERROR",
                    "Authorization has expired.",
                    requirement_id=req_id,
                )
            )
    return status


def _validate_review(
    requirement: dict[str, Any],
    findings: list[dict[str, Any]],
) -> str:
    req_id = _text(requirement.get("id"))
    review = requirement.get("review")
    if not isinstance(review, dict):
        if requirement.get("status") == "COMPLETE":
            findings.append(
                _finding(
                    "REVIEW_NOT_RECORDED",
                    "WARNING",
                    "Completion is recorded without a review record.",
                    requirement_id=req_id,
                )
            )
        return "NOT_RECORDED"

    status = _text(review.get("status")).upper()
    if status not in REVIEW_STATUSES:
        findings.append(
            _finding(
                "INVALID_REVIEW_STATUS",
                "ERROR",
                f"Unknown review status {status!r}.",
                requirement_id=req_id,
            )
        )
        return status
    if status == "INDEPENDENT":
        if review.get("independent") is not True or not _text(review.get("reviewer")):
            findings.append(
                _finding(
                    "FALSE_INDEPENDENCE",
                    "ERROR",
                    "A review labeled INDEPENDENT needs independent=true and a reviewer identity.",
                    requirement_id=req_id,
                )
            )
    if status == "SELF_REVIEW" and requirement.get("status") == "COMPLETE":
        findings.append(
            _finding(
                "SELF_REVIEW_ONLY",
                "WARNING",
                "Completion is supported only by self-review; this is not independent verification.",
                requirement_id=req_id,
            )
        )
    return status


def _validate_evidence(
    requirement: dict[str, Any],
    record_revision: str,
    root: Path | None,
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    req_id = _text(requirement.get("id"))
    evidence_items = requirement.get("evidence")
    if evidence_items is None:
        return []
    if not isinstance(evidence_items, list):
        findings.append(
            _finding(
                "INVALID_EVIDENCE_LIST",
                "ERROR",
                "Requirement evidence must be a list.",
                requirement_id=req_id,
            )
        )
        return []
    normalized: list[dict[str, Any]] = []
    for index, evidence in enumerate(evidence_items):
        if not isinstance(evidence, dict):
            findings.append(
                _finding(
                    "INVALID_EVIDENCE_ENTRY",
                    "ERROR",
                    "Evidence entries must be mappings.",
                    requirement_id=req_id,
                )
            )
            continue
        evidence_id = _text(evidence.get("id")) or f"{req_id}-EV-{index + 1}"
        result = _text(evidence.get("result")).upper()
        provenance = _text(evidence.get("provenance")).upper()
        revision = _text(evidence.get("revision"))
        summary = _text(evidence.get("summary"))
        path_text = _text(evidence.get("path"))
        if result not in EVIDENCE_RESULTS:
            findings.append(
                _finding(
                    "INVALID_EVIDENCE_RESULT",
                    "ERROR",
                    f"Unknown evidence result {result!r}.",
                    requirement_id=req_id,
                    evidence_id=evidence_id,
                )
            )
        if provenance not in EVIDENCE_PROVENANCE:
            findings.append(
                _finding(
                    "INVALID_EVIDENCE_PROVENANCE",
                    "ERROR",
                    f"Unknown evidence provenance {provenance!r}.",
                    requirement_id=req_id,
                    evidence_id=evidence_id,
                )
            )
        if revision and revision not in {record_revision, "*"}:
            findings.append(
                _finding(
                    "STALE_EVIDENCE",
                    "ERROR",
                    f"Evidence revision {revision!r} does not match record revision {record_revision!r}.",
                    requirement_id=req_id,
                    evidence_id=evidence_id,
                )
            )
        if not summary:
            findings.append(
                _finding(
                    "EVIDENCE_SUMMARY_MISSING",
                    "WARNING",
                    "Evidence has no summary of what it shows.",
                    requirement_id=req_id,
                    evidence_id=evidence_id,
                )
            )
        candidate = _evidence_path(path_text, root)
        if candidate is not None and (root is not None or candidate.is_absolute()):
            if not candidate.is_file():
                findings.append(
                    _finding(
                        "EVIDENCE_PATH_MISSING",
                        "ERROR",
                        f"Evidence path does not exist: {candidate}",
                        requirement_id=req_id,
                        evidence_id=evidence_id,
                    )
                )
            else:
                expected = _text(evidence.get("sha256")).lower()
                if expected and _sha256(candidate) != expected:
                    findings.append(
                        _finding(
                            "EVIDENCE_HASH_MISMATCH",
                            "ERROR",
                            "Evidence file sha256 does not match the recorded digest.",
                            requirement_id=req_id,
                            evidence_id=evidence_id,
                        )
                    )
        normalized.append(
            {
                "id": evidence_id,
                "result": result,
                "provenance": provenance,
                "revision": revision,
                "path": path_text,
            }
        )
    return normalized


def _validate_requirements(
    record: dict[str, Any],
    findings: list[dict[str, Any]],
    root: Path | None,
) -> tuple[dict[str, int], dict[str, int], int]:
    requirements = record.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        findings.append(
            _finding(
                "MISSING_REQUIREMENTS",
                "ERROR",
                "The record must contain a non-empty requirements list.",
            )
        )
        return {}, {}, 0

    record_revision = _text(record.get("revision"))
    seen_ids: set[str] = set()
    statuses: dict[str, int] = {}
    provenance_counts: dict[str, int] = {}
    evidence_total = 0

    for requirement in requirements:
        if not isinstance(requirement, dict):
            findings.append(
                _finding(
                    "INVALID_REQUIREMENT_ENTRY",
                    "ERROR",
                    "Requirement entries must be mappings.",
                )
            )
            continue
        req_id = _text(requirement.get("id"))
        if not req_id:
            findings.append(
                _finding("MISSING_REQUIREMENT_ID", "ERROR", "Requirement has no id.")
            )
            continue
        if req_id in seen_ids:
            findings.append(
                _finding(
                    "DUPLICATE_REQUIREMENT_ID",
                    "ERROR",
                    f"Requirement id {req_id!r} appears more than once.",
                    requirement_id=req_id,
                )
            )
        seen_ids.add(req_id)

        status = _text(requirement.get("status")).upper()
        if status not in REQUIREMENT_STATUSES:
            findings.append(
                _finding(
                    "INVALID_REQUIREMENT_STATUS",
                    "ERROR",
                    f"Unknown requirement status {status!r}.",
                    requirement_id=req_id,
                )
            )
        statuses[status or "UNKNOWN"] = statuses.get(status or "UNKNOWN", 0) + 1

        if not _text(requirement.get("source")):
            findings.append(
                _finding(
                    "MISSING_SOURCE",
                    "ERROR",
                    "Requirement has no source reference.",
                    requirement_id=req_id,
                )
            )
        if not _text(requirement.get("obligation")):
            findings.append(
                _finding(
                    "MISSING_OBLIGATION",
                    "ERROR",
                    "Requirement has no obligation text.",
                    requirement_id=req_id,
                )
            )
        if requirement.get("owner_approved") is True:
            findings.append(
                _finding(
                    "UNTRUSTED_OWNER_APPROVAL_FIELD",
                    "WARNING",
                    "owner_approved=true is model-supplied data, not a verified owner grant.",
                    requirement_id=req_id,
                )
            )

        criteria = _text_list(requirement.get("acceptance_criteria"))
        evidence = _validate_evidence(requirement, record_revision, root, findings)
        evidence_total += len(evidence)
        for item in evidence:
            provenance = item["provenance"]
            provenance_counts[provenance] = provenance_counts.get(provenance, 0) + 1

        if status == "COMPLETE":
            if not criteria:
                findings.append(
                    _finding(
                        "MISSING_ACCEPTANCE_CRITERIA",
                        "ERROR",
                        "A COMPLETE requirement needs at least one acceptance criterion.",
                        requirement_id=req_id,
                    )
                )
            if not evidence:
                findings.append(
                    _finding(
                        "UNSUPPORTED_COMPLETION",
                        "ERROR",
                        "A COMPLETE requirement has no evidence.",
                        requirement_id=req_id,
                    )
                )
            else:
                if not any(item["result"] == "PASS" for item in evidence):
                    findings.append(
                        _finding(
                            "UNSUPPORTED_COMPLETION",
                            "ERROR",
                            "A COMPLETE requirement has no passing evidence.",
                            requirement_id=req_id,
                        )
                    )
                if not any(
                    item["provenance"] in TRUSTED_EVIDENCE_PROVENANCE
                    for item in evidence
                ):
                    findings.append(
                        _finding(
                            "SELF_ASSERTED_COMPLETION",
                            "ERROR",
                            "A COMPLETE requirement relies only on self-asserted evidence.",
                            requirement_id=req_id,
                        )
                    )
        elif status in {"PARTIAL", "PENDING", "NOT_VERIFIED"} and not evidence:
            findings.append(
                _finding(
                    "NO_EVIDENCE_RECORDED",
                    "WARNING",
                    f"{status} requirement has no evidence recorded.",
                    requirement_id=req_id,
                )
            )
        elif status == "NOT_APPLICABLE" and not _text(requirement.get("justification")):
            findings.append(
                _finding(
                    "NOT_APPLICABLE_WITHOUT_JUSTIFICATION",
                    "WARNING",
                    "NOT_APPLICABLE should include a justification.",
                    requirement_id=req_id,
                )
            )

        _validate_authorization(requirement, findings)
        _validate_review(requirement, findings)

    return statuses, provenance_counts, evidence_total


def _validate_controls(
    record: dict[str, Any],
    findings: list[dict[str, Any]],
    required_controls: Iterable[str],
    evidence_by_id: dict[str, dict[str, Any]],
) -> tuple[dict[str, int], dict[str, int]]:
    controls = record.get("controls")
    if controls is None:
        controls = []
    if not isinstance(controls, list):
        findings.append(
            _finding("INVALID_CONTROLS_LIST", "ERROR", "controls must be a list.")
        )
        return {}, {}

    by_domain: dict[str, int] = {}
    by_status: dict[str, int] = {}
    seen: set[str] = set()
    for control in controls:
        if not isinstance(control, dict):
            findings.append(
                _finding(
                    "INVALID_CONTROL_ENTRY",
                    "ERROR",
                    "Control entries must be mappings.",
                )
            )
            continue
        control_id = _text(control.get("id"))
        if not control_id:
            findings.append(
                _finding("MISSING_CONTROL_ID", "ERROR", "Control has no id.")
            )
            continue
        if control_id in seen:
            findings.append(
                _finding(
                    "DUPLICATE_CONTROL_ID",
                    "ERROR",
                    f"Control id {control_id!r} appears more than once.",
                    control_id=control_id,
                )
            )
        seen.add(control_id)

        domain = _text(control.get("domain")).upper()
        if domain not in DOMAINS:
            findings.append(
                _finding(
                    "UNKNOWN_CONTROL_DOMAIN",
                    "ERROR",
                    f"Control domain {domain!r} is not one of D1..D6.",
                    control_id=control_id,
                )
            )
        else:
            by_domain[domain] = by_domain.get(domain, 0) + 1

        status = _text(control.get("status")).upper()
        if status not in CONTROL_STATUSES:
            findings.append(
                _finding(
                    "INVALID_CONTROL_STATUS",
                    "ERROR",
                    f"Unknown control status {status!r}.",
                    control_id=control_id,
                )
            )
        else:
            by_status[status] = by_status.get(status, 0) + 1

        enforcement = _text(control.get("enforcement_type")).upper()
        if enforcement not in ENFORCEMENT_TYPES:
            findings.append(
                _finding(
                    "INVALID_ENFORCEMENT_TYPE",
                    "ERROR",
                    f"Unknown enforcement type {enforcement!r}.",
                    control_id=control_id,
                )
            )
        if status == "IMPLEMENTED" and enforcement == "NONE":
            findings.append(
                _finding(
                    "UNSUPPORTED_ENFORCEMENT",
                    "ERROR",
                    "An IMPLEMENTED control cannot declare enforcement_type NONE.",
                    control_id=control_id,
                )
            )

        verification = _text(control.get("verification_status")).upper()
        if verification not in VERIFICATION_STATUSES:
            findings.append(
                _finding(
                    "INVALID_VERIFICATION_STATUS",
                    "ERROR",
                    f"Unknown verification status {verification!r}.",
                    control_id=control_id,
                )
            )
        if verification == "PASS":
            evidence_ids = _text_list(control.get("evidence_ids"))
            if not evidence_ids:
                findings.append(
                    _finding(
                        "UNSUPPORTED_VERIFICATION",
                        "ERROR",
                        "A PASS control has no evidence_ids.",
                        control_id=control_id,
                    )
                )
            for evidence_id in evidence_ids:
                evidence = evidence_by_id.get(evidence_id)
                if evidence is None:
                    findings.append(
                        _finding(
                            "MISSING_CONTROL_EVIDENCE",
                            "ERROR",
                            f"Control references unknown evidence {evidence_id!r}.",
                            control_id=control_id,
                            evidence_id=evidence_id,
                        )
                    )
                elif evidence.get("result") != "PASS":
                    findings.append(
                        _finding(
                            "UNSUPPORTED_VERIFICATION",
                            "ERROR",
                            f"Control evidence {evidence_id!r} is not PASS.",
                            control_id=control_id,
                            evidence_id=evidence_id,
                        )
                    )
        if status == "IMPLEMENTED" and verification != "PASS":
            findings.append(
                _finding(
                    "UNVERIFIED_IMPLEMENTATION",
                    "WARNING",
                    "Control is marked IMPLEMENTED but its verification is not PASS.",
                    control_id=control_id,
                )
            )

    for required in required_controls:
        control_id = _text(required)
        if not control_id:
            continue
        if control_id not in seen:
            findings.append(
                _finding(
                    "MISSING_CONTROL",
                    "ERROR",
                    f"Required control {control_id!r} is not present in the record.",
                    control_id=control_id,
                )
            )
    return by_domain, by_status


def _validate_acceptance(
    record: dict[str, Any],
    findings: list[dict[str, Any]],
) -> str:
    acceptance = record.get("acceptance")
    if not isinstance(acceptance, dict):
        findings.append(
            _finding(
                "ACCEPTANCE_NOT_RECORDED",
                "WARNING",
                "No acceptance status is recorded; owner acceptance is not granted.",
            )
        )
        return "NOT_RECORDED"

    status = _text(acceptance.get("status")).upper()
    if status not in ACCEPTANCE_STATUSES:
        findings.append(
            _finding(
                "INVALID_ACCEPTANCE_STATUS",
                "ERROR",
                f"Unknown acceptance status {status!r}.",
            )
        )
        return status
    if status == "ACCEPTED":
        owner = _text(acceptance.get("owner"))
        source = _text(acceptance.get("source")).upper()
        authenticated = acceptance.get("authenticated") is True
        if not owner or source not in TRUSTED_AUTH_SOURCES or not authenticated:
            findings.append(
                _finding(
                    "UNAUTHENTICATED_ACCEPTANCE",
                    "ERROR",
                    "ACCEPTED requires an owner, a trusted source, and authenticated=true.",
                )
            )
    elif status in {"PENDING", "NOT_GRANTED", "NOT_VERIFIED"}:
        findings.append(
            _finding(
                "OWNER_ACCEPTANCE_PENDING",
                "WARNING",
                "Owner acceptance is not granted; a gate label is not acceptance.",
            )
        )
    return status


def _validate_budget(
    record: dict[str, Any],
    findings: list[dict[str, Any]],
) -> str:
    budget = record.get("budget")
    if not isinstance(budget, dict):
        return "NOT_RECORDED"
    status = _text(budget.get("status")).upper()
    if status not in BUDGET_STATUSES:
        findings.append(
            _finding(
                "INVALID_BUDGET_STATUS",
                "ERROR",
                f"Unknown budget status {status!r}.",
            )
        )
        return status
    if status == "ENFORCED":
        limits = budget.get("limits")
        meter = budget.get("meter")
        if not isinstance(limits, dict) or not limits or not _text(meter):
            findings.append(
                _finding(
                    "UNSUPPORTED_BUDGET",
                    "ERROR",
                    "ENFORCED budget needs limits and a trustworthy meter.",
                )
            )
    elif status in {"NO_TELEMETRY", "NOT_ENFORCED"}:
        findings.append(
            _finding(
                "BUDGET_NOT_ENFORCED",
                "WARNING",
                "Budget/cost limits are not enforced; do not claim a hard cap.",
            )
        )
    return status


def validate_record(
    record: Any,
    *,
    root: Path | None = None,
    required_controls: Iterable[str] = (),
) -> dict[str, Any]:
    """Validate a governance record and return a structured result."""
    findings: list[dict[str, Any]] = []
    if not isinstance(record, dict):
        return {
            "status": "INVALID",
            "findings": [
                _finding("INVALID_RECORD", "ERROR", "Record must be a JSON object.")
            ],
            "summary": {},
        }
    if _text(record.get("schema_version")) != SCHEMA_VERSION:
        return {
            "status": "INVALID",
            "findings": [
                _finding(
                    "UNSUPPORTED_SCHEMA_VERSION",
                    "ERROR",
                    f"Only schema_version {SCHEMA_VERSION!r} is supported.",
                )
            ],
            "summary": {},
        }
    if not _text(record.get("record_id")):
        findings.append(
            _finding("MISSING_RECORD_ID", "ERROR", "record_id is required.")
        )
    if not _text(record.get("revision")):
        findings.append(
            _finding(
                "MISSING_REVISION",
                "ERROR",
                "revision is required so evidence can be checked for staleness.",
            )
        )
    if record.get("owner_approved") is True:
        findings.append(
            _finding(
                "UNTRUSTED_OWNER_APPROVAL_FIELD",
                "WARNING",
                "owner_approved=true is not a verified owner grant.",
            )
        )

    statuses, provenance_counts, evidence_total = _validate_requirements(
        record, findings, root
    )
    # Build the evidence index after requirement validation so controls can
    # resolve evidence IDs.
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for requirement in record.get("requirements", []):
        if not isinstance(requirement, dict):
            continue
        for evidence in requirement.get("evidence", []) or []:
            if not isinstance(evidence, dict):
                continue
            evidence_id = _text(evidence.get("id"))
            if evidence_id:
                evidence_by_id[evidence_id] = {
                    "result": _text(evidence.get("result")).upper()
                }
    control_domains, control_statuses = _validate_controls(
        record, findings, required_controls, evidence_by_id
    )
    acceptance_status = _validate_acceptance(record, findings)
    budget_status = _validate_budget(record, findings)

    errors = [item for item in findings if item["severity"] == "ERROR"]
    warnings = [item for item in findings if item["severity"] == "WARNING"]
    return {
        "status": "FINDINGS" if errors else "PASS",
        "findings": findings,
        "summary": {
            "requirements": {
                "total": sum(statuses.values()),
                "by_status": statuses,
            },
            "evidence": {
                "total": evidence_total,
                "by_provenance": provenance_counts,
            },
            "controls": {
                "total": sum(control_statuses.values()),
                "by_domain": control_domains,
                "by_status": control_statuses,
            },
            "acceptance_status": acceptance_status,
            "budget_status": budget_status,
            "errors": len(errors),
            "warnings": len(warnings),
        },
    }


def trace_markdown(record: dict[str, Any]) -> str:
    """Render a derived, non-authoritative traceability view."""
    revision = _text(record.get("revision")) or "(missing)"
    record_id = _text(record.get("record_id")) or "(missing)"
    lines = [
        "# Governance Trace",
        "",
        "> **DERIVED / NON-AUTHORITATIVE** — this view summarizes a local record.",
        "> It is not an owner approval, an independent review, or enforcement evidence.",
        "",
        f"- Record: `{record_id}`",
        f"- Revision: `{revision}`",
        "",
        "| Requirement | Status | Acceptance criteria | Evidence | Authorization | Review |",
        "|---|---|---|---|---|---|",
    ]
    for requirement in record.get("requirements", []) or []:
        if not isinstance(requirement, dict):
            continue
        req_id = _text(requirement.get("id")) or "(missing)"
        status = _text(requirement.get("status")) or "(missing)"
        criteria = len(_text_list(requirement.get("acceptance_criteria")))
        evidence = len(requirement.get("evidence", []) or [])
        authorization = requirement.get("authorization")
        auth_status = (
            _text(authorization.get("status"))
            if isinstance(authorization, dict)
            else "NOT_RECORDED"
        )
        review = requirement.get("review")
        review_status = (
            _text(review.get("status"))
            if isinstance(review, dict)
            else "NOT_RECORDED"
        )
        lines.append(
            f"| `{req_id}` | {status} | {criteria} | {evidence} | "
            f"{auth_status or 'NOT_RECORDED'} | {review_status or 'NOT_RECORDED'} |"
        )
    lines.extend(
        [
            "",
            "> A `COMPLETE` status is only a claim until its evidence is current and",
            "> independently inspectable. Pending owner acceptance is not an approval.",
        ]
    )
    return "\n".join(lines)


def decision_markdown(record: dict[str, Any]) -> str:
    """Render an owner decision brief without granting approval."""
    open_items: list[str] = []
    auth_items: list[str] = []
    review_items: list[str] = []
    control_items: list[str] = []
    for requirement in record.get("requirements", []) or []:
        if not isinstance(requirement, dict):
            continue
        req_id = _text(requirement.get("id")) or "(missing)"
        status = _text(requirement.get("status")).upper()
        if status not in {"COMPLETE", "NOT_APPLICABLE"}:
            open_items.append(f"- `{req_id}` is `{status or 'UNKNOWN'}`.")
        authorization = requirement.get("authorization")
        if isinstance(authorization, dict):
            auth_status = _text(authorization.get("status")).upper()
            if authorization.get("protected") is True or auth_status in {
                "PENDING",
                "NOT_VERIFIED",
                "NOT_GRANTED",
            }:
                auth_items.append(
                    f"- `{req_id}` authorization is `{auth_status or 'UNKNOWN'}`."
                )
        review = requirement.get("review")
        if isinstance(review, dict):
            review_status = _text(review.get("status")).upper()
            if review_status in {"PENDING", "NOT_VERIFIED", "SELF_REVIEW"}:
                review_items.append(
                    f"- `{req_id}` review is `{review_status}`; it is not independent verification."
                )
    for control in record.get("controls", []) or []:
        if not isinstance(control, dict):
            continue
        control_id = _text(control.get("id")) or "(missing)"
        status = _text(control.get("status")).upper()
        verification = _text(control.get("verification_status")).upper()
        if status != "IMPLEMENTED" or verification != "PASS":
            control_items.append(
                f"- `{control_id}` is `{status or 'UNKNOWN'}` / `{verification or 'UNKNOWN'}`."
            )

    acceptance = record.get("acceptance")
    acceptance_status = (
        _text(acceptance.get("status")).upper()
        if isinstance(acceptance, dict)
        else "NOT_RECORDED"
    )
    has_open = bool(open_items or auth_items or control_items) or acceptance_status != "ACCEPTED"
    lines = [
        "# Owner Decision Brief",
        "",
        "> **DERIVED / NON-AUTHORITATIVE** — this brief prepares a decision. It does not grant it.",
        "",
        f"**Status:** {'OWNER_DECISION_REQUIRED' if has_open else 'NO_OPEN_ITEMS'}",
        "",
        f"- Record: `{_text(record.get('record_id')) or '(missing)'}`",
        f"- Revision: `{_text(record.get('revision')) or '(missing)'}`",
        f"- Acceptance: `{acceptance_status}`",
        "",
        "## Open requirements",
        *(open_items or ["- None."]),
        "",
        "## Authorization items",
        *(auth_items or ["- None recorded."]),
        "",
        "## Review items",
        *(review_items or ["- None recorded."]),
        "",
        "## Control gaps",
        *(control_items or ["- None recorded."]),
        "",
        "## Limits",
        "- A workflow gate, a local JSON record, or a model-supplied approval is not authenticated owner acceptance.",
        "- This brief does not activate policy, authorize release, or prove host-wide enforcement.",
    ]
    return "\n".join(lines)


def _human_check(result: dict[str, Any], record: dict[str, Any]) -> str:
    summary = result.get("summary", {})
    requirements = summary.get("requirements", {})
    controls = summary.get("controls", {})
    lines = [
        f"Governance check: {result['status']}",
        f"Record: {_text(record.get('record_id')) or '(missing)'}",
        f"Revision: {_text(record.get('revision')) or '(missing)'}",
        f"Requirements: {requirements.get('total', 0)} {requirements.get('by_status', {})}",
        f"Controls: {controls.get('total', 0)} {controls.get('by_domain', {})}",
        f"Acceptance: {summary.get('acceptance_status', 'NOT_RECORDED')}",
        f"Errors: {summary.get('errors', 0)}  Warnings: {summary.get('warnings', 0)}",
    ]
    for finding in result.get("findings", []):
        context = ""
        if finding.get("requirement_id"):
            context += f" [{finding['requirement_id']}]"
        if finding.get("control_id"):
            context += f" [{finding['control_id']}]"
        if finding.get("evidence_id"):
            context += f" [{finding['evidence_id']}]"
        lines.append(
            f"- {finding['severity']} {finding['code']}{context}: {finding['message']}"
        )
    return "\n".join(lines)


def _load_record(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _parse_required_controls(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only governance record checks for Majed Spec Kit."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "trace", "decide"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--record", required=True, help="Path to the JSON record")
        sub.add_argument(
            "--root",
            default=None,
            help="Optional project root for resolving relative evidence paths",
        )
        sub.add_argument(
            "--required-controls",
            default="",
            help="Comma-separated control IDs that must be present",
        )
        sub.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    path = Path(args.record)
    try:
        record = _load_record(path)
    except (OSError, json.JSONDecodeError) as exc:
        payload = {
            "status": "INVALID",
            "findings": [
                _finding(
                    "UNREADABLE_RECORD",
                    "ERROR",
                    f"Cannot read JSON record: {exc}",
                )
            ],
            "summary": {},
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Governance check: INVALID\n- {payload['findings'][0]['message']}")
        return 3

    if not isinstance(record, dict):
        print("Governance check: INVALID\n- Record must be a JSON object.")
        return 3

    root = Path(args.root) if args.root else None
    result = validate_record(
        record,
        root=root,
        required_controls=_parse_required_controls(args.required_controls),
    )

    if args.command == "trace":
        print(trace_markdown(record))
        return 0
    if args.command == "decide":
        print(decision_markdown(record))
        return 0

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_human_check(result, record))
    if result["status"] == "PASS":
        return 0
    if result["status"] == "FINDINGS":
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
