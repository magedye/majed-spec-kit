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
import re
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
COMPONENT_VERSION = "1.1.0"
SOURCE_AUTHORITIES = {"OWNER_APPROVED", "PROJECT_POLICY", "REFERENCE", "UNVERIFIED"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
NORMATIVE_RE = re.compile(
    r"\b(MUST(?:\s+NOT)?|SHALL(?:\s+NOT)?|SHOULD(?:\s+NOT)?|REQUIRED|NEVER|ALWAYS)\b",
    re.IGNORECASE,
)
ARABIC_NORMATIVE_RE = re.compile(r"(يجب|ينبغي|لا\s+يجوز|ممنوع|إلزامي|اختياري)")
SOURCE_SECTION_RE = re.compile(
    r"requirements?|constraints?|non[- ]goals?|acceptance|المتطلبات|القيود|غير\s+الأهداف|معايير\s+القبول",
    re.IGNORECASE,
)


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
    evidence_seen: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    req_id = _text(requirement.get("id"))
    if evidence_seen is None:
        evidence_seen = {}
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
        if evidence_id in evidence_seen:
            findings.append(
                _finding(
                    "DUPLICATE_EVIDENCE_ID",
                    "ERROR",
                    f"Evidence id {evidence_id!r} is reused; first seen in "
                    f"{evidence_seen[evidence_id]!r}.",
                    requirement_id=req_id,
                    evidence_id=evidence_id,
                )
            )
        else:
            evidence_seen[evidence_id] = req_id
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


def _validate_source_reference(
    requirement: dict[str, Any],
    record_revision: str,
    findings: list[dict[str, Any]],
) -> str:
    req_id = _text(requirement.get("id"))
    source = requirement.get("source")
    if isinstance(source, str):
        value = source.strip()
        if not value:
            findings.append(
                _finding(
                    "MISSING_SOURCE",
                    "ERROR",
                    "Requirement has no source reference.",
                    requirement_id=req_id,
                )
            )
        return value
    if isinstance(source, dict):
        path = _text(source.get("path"))
        line_start = source.get("line_start")
        line_end = source.get("line_end")
        revision = _text(source.get("revision"))
        if not path:
            findings.append(
                _finding(
                    "MISSING_SOURCE_PATH",
                    "ERROR",
                    "Source object has no path.",
                    requirement_id=req_id,
                )
            )
        if (
            not isinstance(line_start, int)
            or isinstance(line_start, bool)
            or line_start < 1
            or not isinstance(line_end, int)
            or isinstance(line_end, bool)
            or line_end < line_start
        ):
            findings.append(
                _finding(
                    "INVALID_SOURCE_SPAN",
                    "ERROR",
                    "Source line_start/line_end must be positive integers with start <= end.",
                    requirement_id=req_id,
                )
            )
        if not revision:
            findings.append(
                _finding(
                    "MISSING_SOURCE_REVISION",
                    "ERROR",
                    "Source object has no revision.",
                    requirement_id=req_id,
                )
            )
        elif revision not in {record_revision, "*"}:
            findings.append(
                _finding(
                    "STALE_SOURCE_REVISION",
                    "ERROR",
                    f"Source revision {revision!r} does not match record revision "
                    f"{record_revision!r}.",
                    requirement_id=req_id,
                )
            )
        if path and isinstance(line_start, int) and isinstance(line_end, int):
            return f"{path}:{line_start}-{line_end}"
        return path
    if source is None:
        findings.append(
            _finding(
                "MISSING_SOURCE",
                "ERROR",
                "Requirement has no source reference.",
                requirement_id=req_id,
            )
        )
    else:
        findings.append(
            _finding(
                "INVALID_SOURCE",
                "ERROR",
                "Source must be a string or a source-span object.",
                requirement_id=req_id,
            )
        )
    return ""


def _validate_requirements(
    record: dict[str, Any],
    findings: list[dict[str, Any]],
    root: Path | None,
) -> tuple[dict[str, int], dict[str, int], int, set[str], int]:
    requirements = record.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        findings.append(
            _finding(
                "MISSING_REQUIREMENTS",
                "ERROR",
                "The record must contain a non-empty requirements list.",
            )
        )
        return {}, {}, 0, set(), 0

    record_revision = _text(record.get("revision"))
    seen_ids: set[str] = set()
    statuses: dict[str, int] = {}
    provenance_counts: dict[str, int] = {}
    evidence_total = 0
    evidence_seen: dict[str, str] = {}
    open_requirements = 0

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
        if status not in {"COMPLETE", "NOT_APPLICABLE"}:
            open_requirements += 1

        _validate_source_reference(requirement, record_revision, findings)
        required = requirement.get("required") is True
        component = _text(requirement.get("component"))
        tests = _text_list(requirement.get("tests"))
        if required and not component:
            findings.append(
                _finding(
                    "MISSING_COMPONENT_LINK",
                    "ERROR",
                    "A required requirement needs a component link.",
                    requirement_id=req_id,
                )
            )
        if required and not tests:
            findings.append(
                _finding(
                    "MISSING_TEST_LINK",
                    "ERROR",
                    "A required requirement needs at least one test link.",
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
        evidence = _validate_evidence(
            requirement, record_revision, root, findings, evidence_seen
        )
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

    return statuses, provenance_counts, evidence_total, seen_ids, open_requirements


def _validate_controls(
    record: dict[str, Any],
    findings: list[dict[str, Any]],
    required_controls: Iterable[str],
    evidence_by_id: dict[str, dict[str, Any]],
    requirement_ids: set[str] | None = None,
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

        linked_requirements = _text_list(control.get("requirement_ids"))
        for requirement_id in linked_requirements:
            if requirement_ids is not None and requirement_id not in requirement_ids:
                findings.append(
                    _finding(
                        "MISSING_CONTROL_REQUIREMENT",
                        "ERROR",
                        f"Control links unknown requirement {requirement_id!r}.",
                        control_id=control_id,
                    )
                )
        if status == "IMPLEMENTED" and not linked_requirements:
            findings.append(
                _finding(
                    "CONTROL_WITHOUT_REQUIREMENT_LINK",
                    "WARNING",
                    "An IMPLEMENTED control has no requirement_ids link.",
                    control_id=control_id,
                )
            )

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
    open_requirements: int = 0,
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
        if open_requirements > 0:
            findings.append(
                _finding(
                    "ACCEPTANCE_WITH_OPEN_REQUIREMENTS",
                    "ERROR",
                    "Acceptance cannot be ACCEPTED while requirements remain open.",
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

    (
        statuses,
        provenance_counts,
        evidence_total,
        requirement_ids,
        open_requirements,
    ) = _validate_requirements(record, findings, root)
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
        record, findings, required_controls, evidence_by_id, requirement_ids
    )
    acceptance_status = _validate_acceptance(record, findings, open_requirements)
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
        "> **DERIVED / NON-AUTHORITATIVE** - this view summarizes a local record.",
        "> It is not an owner approval, an independent review, or enforcement evidence.",
        "",
        f"- Record: `{record_id}`",
        f"- Revision: `{revision}`",
        "",
        "| Requirement | Source | Component | Status | AC | Evidence | Authorization | Review |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for requirement in record.get("requirements", []) or []:
        if not isinstance(requirement, dict):
            continue
        req_id = _text(requirement.get("id")) or "(missing)"
        source = requirement.get("source")
        if isinstance(source, dict):
            source_text = (
                f"{_text(source.get('path'))}:"
                f"{source.get('line_start', '?')}-{source.get('line_end', '?')}"
            )
        else:
            source_text = _text(source) or "(missing)"
        component = _text(requirement.get("component")) or "(none)"
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
            f"| `{req_id}` | `{source_text}` | `{component}` | {status} | "
            f"{criteria} | {evidence} | {auth_status or 'NOT_RECORDED'} | "
            f"{review_status or 'NOT_RECORDED'} |"
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
        "> **DERIVED / NON-AUTHORITATIVE** - this brief prepares a decision. It does not grant it.",
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


def intake_source(
    source_path: Path,
    *,
    revision: str,
    record_id: str = "MSK-INTAKE-001",
) -> dict[str, Any]:
    """Extract traceable candidate obligations without claiming completeness."""
    if not revision.strip():
        raise ValueError("revision is required for source binding")
    try:
        text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot read source: {exc}") from exc

    lines = text.splitlines()
    requirements: list[dict[str, Any]] = []
    current_section = ""
    scanned = 0
    for number, raw_line in enumerate(lines, 1):
        scanned += 1
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current_section = stripped.lstrip("#").strip()
            continue
        bullet = bool(re.match(r"^(?:[-*+]|\d+[.)])\s+", stripped))
        normative = bool(
            NORMATIVE_RE.search(stripped) or ARABIC_NORMATIVE_RE.search(stripped)
        )
        in_obligation_section = bool(SOURCE_SECTION_RE.search(current_section))
        if not (bullet and (normative or in_obligation_section)):
            continue
        kind = "OBLIGATION"
        section_lower = current_section.lower()
        if "non" in section_lower and "goal" in section_lower:
            kind = "NON_GOAL"
        elif "constraint" in section_lower or "قيود" in current_section:
            kind = "CONSTRAINT"
        elif "acceptance" in section_lower or "قبول" in current_section:
            kind = "ACCEPTANCE"
        requirements.append(
            {
                "id": f"MSK-IN-{len(requirements) + 1:03d}",
                "source": {
                    "path": source_path.as_posix(),
                    "line_start": number,
                    "line_end": number,
                    "revision": revision.strip(),
                },
                "obligation": stripped,
                "kind": kind,
                "acceptance_criteria": [],
                "status": "PENDING",
                "required": False,
                "component": "",
                "tests": [],
                "evidence": [],
                "authorization": {"status": "NOT_REQUIRED"},
                "review": {
                    "status": "PENDING",
                    "independent": False,
                    "reviewer": "",
                    "scope": "",
                },
            }
        )

    status = "PARSED" if requirements else "NO_CANDIDATES"
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "revision": revision.strip(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requirements": requirements,
        "controls": [],
        "acceptance": {
            "status": "PENDING",
            "owner": "",
            "source": "",
            "authenticated": False,
        },
        "budget": {"status": "NO_TELEMETRY", "limits": {}, "meter": ""},
        "intake": {
            "status": status,
            "source": source_path.as_posix(),
            "candidate_count": len(requirements),
            "scanned_lines": scanned,
            "derived": True,
            "non_authoritative": True,
            "limitations": [
                "Deterministic candidate extraction only; it does not prove semantic completeness.",
                "Candidates remain PENDING until acceptance criteria, links, and evidence are supplied.",
            ],
        },
    }


def _normalise_files(files: Iterable[str] | str) -> list[str]:
    if isinstance(files, str):
        raw = [item.strip() for item in files.split(",")]
    else:
        raw = [str(item).strip() for item in files]
    return [item.replace("\\", "/") for item in raw if item]


def impact_report(
    files: Iterable[str] | str,
    impact_map: Any,
    *,
    rollback: str = "",
    dependency_notes: str = "",
) -> dict[str, Any]:
    """Map changed files to components and require a rollback for risky changes."""
    findings: list[dict[str, Any]] = []
    if not isinstance(impact_map, dict) or _text(
        impact_map.get("schema_version")
    ) != SCHEMA_VERSION:
        return {
            "status": "INVALID",
            "findings": [
                _finding(
                    "INVALID_IMPACT_MAP",
                    "ERROR",
                    "Impact map must be a schema_version 1.0 object.",
                )
            ],
            "components": [],
            "kinds": [],
            "files": [],
            "risk": "UNKNOWN",
            "reversible": None,
            "derived": True,
            "non_authoritative": True,
        }
    entries = impact_map.get("paths")
    if not isinstance(entries, list) or not entries:
        return {
            "status": "INVALID",
            "findings": [
                _finding("INVALID_IMPACT_MAP", "ERROR", "Impact map needs a non-empty paths list.")
            ],
            "components": [],
            "kinds": [],
            "files": [],
            "risk": "UNKNOWN",
            "reversible": None,
            "derived": True,
            "non_authoritative": True,
        }
    normalised = _normalise_files(files)
    if not normalised:
        findings.append(
            _finding("NO_FILES", "ERROR", "At least one changed file is required.")
        )
    components: list[str] = []
    kinds: list[str] = []
    risks: list[str] = []
    reversible = True
    for file_name in normalised:
        matches = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and _text(entry.get("prefix"))
            and file_name.startswith(_text(entry.get("prefix")).replace("\\", "/"))
        ]
        if not matches:
            findings.append(
                _finding(
                    "UNMATCHED_PATH",
                    "ERROR",
                    f"No impact-map entry matches {file_name!r}.",
                    path=file_name,
                )
            )
            continue
        best = max(matches, key=lambda entry: len(_text(entry.get("prefix"))))
        component = _text(best.get("component"))
        kind = _text(best.get("kind"))
        risk = _text(best.get("risk")).upper() or "UNKNOWN"
        if component and component not in components:
            components.append(component)
        if kind and kind not in kinds:
            kinds.append(kind)
        if risk not in risks:
            risks.append(risk)
        if best.get("reversible") is not True:
            reversible = False

    risk_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "UNKNOWN": 5}
    overall_risk = max(risks, key=lambda item: risk_rank.get(item, 5)) if risks else "UNKNOWN"
    if (overall_risk in {"HIGH", "CRITICAL"} or not reversible) and not rollback.strip():
        findings.append(
            _finding(
                "MISSING_ROLLBACK",
                "ERROR",
                "A high-risk or non-reversible change needs an explicit rollback/recovery statement.",
            )
        )
    if len(components) > 1 and not dependency_notes.strip():
        findings.append(
            _finding(
                "MISSING_DEPENDENCY_NOTES",
                "WARNING",
                "Multiple components are affected; record dependency/order notes.",
            )
        )

    errors = [item for item in findings if item["severity"] == "ERROR"]
    return {
        "status": "FINDINGS" if errors else "PASS",
        "findings": findings,
        "components": components,
        "kinds": kinds,
        "files": normalised,
        "risk": overall_risk,
        "reversible": reversible,
        "rollback_present": bool(rollback.strip()),
        "dependency_notes_present": bool(dependency_notes.strip()),
        "derived": True,
        "non_authoritative": True,
    }


def validate_sources(manifest: Any, *, root: Path | None = None) -> dict[str, Any]:
    """Validate a source manifest and its content hashes."""
    findings: list[dict[str, Any]] = []
    if not isinstance(manifest, dict) or _text(
        manifest.get("schema_version")
    ) != SCHEMA_VERSION:
        return {
            "status": "INVALID",
            "findings": [
                _finding(
                    "INVALID_SOURCE_MANIFEST",
                    "ERROR",
                    "Source manifest must be a schema_version 1.0 object.",
                )
            ],
            "summary": {},
        }
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        return {
            "status": "INVALID",
            "findings": [
                _finding("INVALID_SOURCE_MANIFEST", "ERROR", "sources must be a non-empty list.")
            ],
            "summary": {},
        }
    ids = {_text(source.get("id")) for source in sources if isinstance(source, dict)}
    seen: set[str] = set()
    priorities: set[int] = set()
    ordered: list[tuple[int, str]] = []
    authorities: dict[str, int] = {}
    for source in sources:
        if not isinstance(source, dict):
            findings.append(
                _finding("INVALID_SOURCE_ENTRY", "ERROR", "Source entries must be mappings.")
            )
            continue
        source_id = _text(source.get("id"))
        if not source_id:
            findings.append(
                _finding("MISSING_SOURCE_ID", "ERROR", "Source entry has no id.")
            )
            continue
        if source_id in seen:
            findings.append(
                _finding(
                    "DUPLICATE_SOURCE_ID",
                    "ERROR",
                    f"Source id {source_id!r} appears more than once.",
                    source_id=source_id,
                )
            )
        seen.add(source_id)
        path_text = _text(source.get("path"))
        revision = _text(source.get("revision"))
        authority = _text(source.get("authority")).upper()
        digest = _text(source.get("sha256")).lower()
        priority = source.get("priority")
        if (
            not isinstance(priority, int)
            or isinstance(priority, bool)
            or priority < 1
        ):
            findings.append(
                _finding(
                    "INVALID_SOURCE_PRIORITY",
                    "ERROR",
                    "Source priority must be an integer of at least 1.",
                    source_id=source_id,
                )
            )
        elif priority in priorities:
            findings.append(
                _finding(
                    "DUPLICATE_SOURCE_PRIORITY",
                    "ERROR",
                    f"Source priority {priority} is used more than once.",
                    source_id=source_id,
                )
            )
        else:
            priorities.add(priority)
            ordered.append((priority, source_id))
        if not path_text:
            findings.append(
                _finding("MISSING_SOURCE_PATH", "ERROR", "Source has no path.", source_id=source_id)
            )
        if not revision:
            findings.append(
                _finding(
                    "MISSING_SOURCE_REVISION",
                    "ERROR",
                    "Source has no revision.",
                    source_id=source_id,
                )
            )
        if authority not in SOURCE_AUTHORITIES:
            findings.append(
                _finding(
                    "INVALID_SOURCE_AUTHORITY",
                    "ERROR",
                    f"Unknown source authority {authority!r}.",
                    source_id=source_id,
                )
            )
        else:
            authorities[authority] = authorities.get(authority, 0) + 1
            if authority == "UNVERIFIED":
                findings.append(
                    _finding(
                        "UNVERIFIED_SOURCE",
                        "WARNING",
                        "Source authority is explicitly UNVERIFIED.",
                        source_id=source_id,
                    )
                )
        if authority != "UNVERIFIED":
            if not digest or not re.fullmatch(r"[0-9a-f]{64}", digest):
                findings.append(
                    _finding(
                        "SOURCE_HASH_MISSING",
                        "ERROR",
                        "A trusted source needs a 64-hex sha256.",
                        source_id=source_id,
                    )
                )
            elif root is not None and path_text:
                candidate = Path(path_text)
                if not candidate.is_absolute():
                    candidate = root / candidate
                if not candidate.is_file():
                    findings.append(
                        _finding(
                            "SOURCE_PATH_MISSING",
                            "ERROR",
                            f"Source path does not exist: {candidate}",
                            source_id=source_id,
                        )
                    )
                elif _sha256(candidate) != digest:
                    findings.append(
                        _finding(
                            "SOURCE_HASH_MISMATCH",
                            "ERROR",
                            "Source sha256 does not match the manifest.",
                            source_id=source_id,
                        )
                    )
        supersedes = _text(source.get("supersedes"))
        if supersedes:
            if supersedes == source_id:
                findings.append(
                    _finding(
                        "SELF_SUPERSEDES",
                        "ERROR",
                        "A source cannot supersede itself.",
                        source_id=source_id,
                    )
                )
            elif supersedes not in ids:
                findings.append(
                    _finding(
                        "UNKNOWN_SUPERSEDES",
                        "ERROR",
                        f"Superseded source {supersedes!r} is not present.",
                        source_id=source_id,
                    )
                )
    errors = [item for item in findings if item["severity"] == "ERROR"]
    return {
        "status": "FINDINGS" if errors else "PASS",
        "findings": findings,
        "summary": {
            "sources": len(sources),
            "by_authority": authorities,
            "effective_order": [source_id for _, source_id in sorted(ordered)],
            "errors": len(errors),
            "warnings": len(findings) - len(errors),
        },
    }


def converge_items(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one bounded remediation item per open requirement."""
    items: list[dict[str, Any]] = []
    record_revision = _text(record.get("revision"))
    for requirement in record.get("requirements", []) or []:
        if not isinstance(requirement, dict):
            continue
        req_id = _text(requirement.get("id")) or "(missing)"
        status = _text(requirement.get("status")).upper()
        if status in {"COMPLETE", "NOT_APPLICABLE"}:
            continue
        actions: list[str] = []
        if not _text_list(requirement.get("acceptance_criteria")):
            actions.append("DEFINE_ACCEPTANCE_CRITERIA")
        evidence = requirement.get("evidence")
        evidence_items = evidence if isinstance(evidence, list) else []
        if not evidence_items:
            actions.append("ADD_EVIDENCE")
        else:
            if any(
                isinstance(item, dict)
                and _text(item.get("revision"))
                and _text(item.get("revision")) not in {record_revision, "*"}
                for item in evidence_items
            ):
                actions.append("REFRESH_EVIDENCE")
            if not any(
                isinstance(item, dict)
                and _text(item.get("provenance")).upper() in TRUSTED_EVIDENCE_PROVENANCE
                for item in evidence_items
            ):
                actions.append("ADD_TRUSTED_EVIDENCE")
        if requirement.get("protected") is True:
            authorization = requirement.get("authorization")
            auth_status = (
                _text(authorization.get("status")).upper()
                if isinstance(authorization, dict)
                else ""
            )
            if auth_status != "GRANTED":
                actions.append("OBTAIN_AUTHORIZATION")
        review = requirement.get("review")
        review_status = (
            _text(review.get("status")).upper() if isinstance(review, dict) else ""
        )
        if review_status != "INDEPENDENT":
            actions.append("OBTAIN_INDEPENDENT_REVIEW")
        if requirement.get("required") is True:
            if not _text(requirement.get("component")):
                actions.append("LINK_COMPONENT")
            if not _text_list(requirement.get("tests")):
                actions.append("LINK_TESTS")
        items.append(
            {
                "requirement_id": req_id,
                "status": status or "UNKNOWN",
                "actions": actions or ["REVIEW_STATUS"],
                "bounded": True,
            }
        )
    return items


def converge_markdown(record: dict[str, Any]) -> str:
    items = converge_items(record)
    lines = [
        "# Bounded Convergence Plan",
        "",
        "> **DERIVED / NON-AUTHORITATIVE** - one remediation item per open requirement.",
        "",
        "| Requirement | Status | Bounded actions |",
        "|---|---|---|",
    ]
    for item in items:
        lines.append(
            f"| `{item['requirement_id']}` | {item['status']} | "
            f"{', '.join(item['actions'])} |"
        )
    if not items:
        lines.append("| - | - | No open requirements. |")
    lines.append("")
    lines.append("> This plan does not create tasks, approve work, or prove completion.")
    return "\n".join(lines)


def metrics_report(record: dict[str, Any]) -> dict[str, Any]:
    """Compute deterministic quality counts without creating a new source of truth."""
    requirements = [
        item for item in record.get("requirements", []) or [] if isinstance(item, dict)
    ]
    by_status: dict[str, int] = {}
    required = 0
    required_complete = 0
    evidence_total = 0
    by_provenance: dict[str, int] = {}
    stale = 0
    self_asserted = 0
    protected = 0
    auth_pending = 0
    review_independent = 0
    review_self = 0
    record_revision = _text(record.get("revision"))
    for requirement in requirements:
        status = _text(requirement.get("status")).upper() or "UNKNOWN"
        by_status[status] = by_status.get(status, 0) + 1
        if requirement.get("required") is True:
            required += 1
            if status == "COMPLETE":
                required_complete += 1
        if requirement.get("protected") is True:
            protected += 1
            authorization = requirement.get("authorization")
            auth_status = (
                _text(authorization.get("status")).upper()
                if isinstance(authorization, dict)
                else ""
            )
            if auth_status != "GRANTED":
                auth_pending += 1
        review = requirement.get("review")
        review_status = (
            _text(review.get("status")).upper() if isinstance(review, dict) else ""
        )
        if review_status == "INDEPENDENT":
            review_independent += 1
        elif review_status == "SELF_REVIEW":
            review_self += 1
        for evidence in requirement.get("evidence", []) or []:
            if not isinstance(evidence, dict):
                continue
            evidence_total += 1
            provenance = _text(evidence.get("provenance")).upper() or "UNKNOWN"
            by_provenance[provenance] = by_provenance.get(provenance, 0) + 1
            if provenance == "SELF_ASSERTED":
                self_asserted += 1
            revision = _text(evidence.get("revision"))
            if revision and revision not in {record_revision, "*"}:
                stale += 1
    controls = [
        item for item in record.get("controls", []) or [] if isinstance(item, dict)
    ]
    control_domains: dict[str, int] = {}
    control_statuses: dict[str, int] = {}
    for control in controls:
        domain = _text(control.get("domain")).upper() or "UNKNOWN"
        control_domains[domain] = control_domains.get(domain, 0) + 1
        status = _text(control.get("status")).upper() or "UNKNOWN"
        control_statuses[status] = control_statuses.get(status, 0) + 1
    validation = validate_record(record)
    acceptance = record.get("acceptance")
    budget = record.get("budget")
    return {
        "record_id": _text(record.get("record_id")),
        "revision": record_revision,
        "requirements": {
            "total": len(requirements),
            "by_status": by_status,
            "required": required,
            "required_complete": required_complete,
            "required_coverage": (
                round(required_complete / required, 4) if required else None
            ),
        },
        "evidence": {
            "total": evidence_total,
            "by_provenance": by_provenance,
            "stale": stale,
            "self_asserted": self_asserted,
        },
        "authorization": {
            "protected": protected,
            "not_granted": auth_pending,
        },
        "review": {
            "independent": review_independent,
            "self_review": review_self,
        },
        "controls": {
            "total": len(controls),
            "by_domain": control_domains,
            "by_status": control_statuses,
        },
        "acceptance_status": (
            _text(acceptance.get("status")).upper()
            if isinstance(acceptance, dict)
            else "NOT_RECORDED"
        ),
        "budget_status": (
            _text(budget.get("status")).upper()
            if isinstance(budget, dict)
            else "NOT_RECORDED"
        ),
        "validation": {
            "status": validation["status"],
            "errors": validation["summary"].get("errors", 0),
            "warnings": validation["summary"].get("warnings", 0),
        },
        "derived": True,
        "non_authoritative": True,
    }


def metrics_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Governance Metrics",
        "",
        "> **DERIVED / NON-AUTHORITATIVE** - local record counts, not effectiveness proof.",
        "",
        f"- Record: `{report.get('record_id') or '(missing)'}`",
        f"- Revision: `{report.get('revision') or '(missing)'}`",
        f"- Requirements: {report['requirements']['total']} {report['requirements']['by_status']}",
        f"- Required complete: {report['requirements']['required_complete']}/{report['requirements']['required']}",
        f"- Evidence: {report['evidence']['total']} {report['evidence']['by_provenance']}",
        f"- Stale evidence: {report['evidence']['stale']}",
        f"- Self-asserted evidence: {report['evidence']['self_asserted']}",
        f"- Controls: {report['controls']['total']} {report['controls']['by_domain']}",
        f"- Acceptance: {report['acceptance_status']}",
        f"- Budget: {report['budget_status']}",
        f"- Validation: {report['validation']['status']} "
        f"({report['validation']['errors']} errors, {report['validation']['warnings']} warnings)",
    ]
    return "\n".join(lines)


def _version_tuple(value: str) -> tuple[int, int, int]:
    parts = re.findall(r"\d+", value)
    numbers = [int(part) for part in parts[:3]]
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers[:3])  # type: ignore[return-value]


def version_info() -> dict[str, Any]:
    return {
        "component": "majed-governance",
        "version": COMPONENT_VERSION,
        "schema_version": SCHEMA_VERSION,
    }


def version_satisfies(required: str) -> bool:
    return _version_tuple(COMPONENT_VERSION) >= _version_tuple(required)


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


def _add_record_args(sub: argparse.ArgumentParser) -> None:
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only governance checks and derived views for Majed Spec Kit."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "trace", "decide"):
        _add_record_args(subparsers.add_parser(name))

    intake = subparsers.add_parser("intake")
    intake.add_argument("--source", required=True, help="Source request document")
    intake.add_argument("--revision", default="", help="Revision the source belongs to")
    intake.add_argument("--record-id", default="MSK-INTAKE-001")
    intake.add_argument("--output", default=None, help="Optional output JSON path")
    intake.add_argument("--json", action="store_true", help="Emit JSON output")

    impact = subparsers.add_parser("impact")
    impact.add_argument("--map", required=True, help="Impact map JSON path")
    impact.add_argument("--files", required=True, help="Comma-separated changed files")
    impact.add_argument("--rollback", default="", help="Rollback/recovery statement")
    impact.add_argument("--dependency-notes", default="")
    impact.add_argument("--json", action="store_true", help="Emit JSON output")

    sources = subparsers.add_parser("sources")
    sources.add_argument("--manifest", required=True, help="Source manifest JSON path")
    sources.add_argument("--root", default=None)
    sources.add_argument("--json", action="store_true", help="Emit JSON output")

    converge = subparsers.add_parser("converge")
    converge.add_argument("--record", required=True)
    converge.add_argument("--json", action="store_true")
    converge.add_argument(
        "--check",
        action="store_true",
        help="Exit 2 when open remediation items exist",
    )
    converge.add_argument(
        "--apply",
        action="store_true",
        help="Write the bounded remediation plan as a derived artifact",
    )
    converge.add_argument(
        "--output",
        default=".specify/governance/remediation.json",
        help="Output path for --apply",
    )

    metrics = subparsers.add_parser("metrics")
    metrics.add_argument("--record", required=True)
    metrics.add_argument("--json", action="store_true")

    version = subparsers.add_parser("version")
    version.add_argument("--require", default="")
    version.add_argument("--json", action="store_true")
    return parser


def _configure_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def _read_json(path: Path, code: str) -> tuple[Any, dict[str, Any] | None]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, {
            "status": "INVALID",
            "findings": [
                _finding(code, "ERROR", f"Cannot read JSON input: {exc}")
            ],
            "summary": {},
        }


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        info = version_info()
        required = _text(args.require)
        compatible = version_satisfies(required) if required else True
        payload = {**info, "required": required, "compatible": compatible}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(
                f"{info['component']} {info['version']} "
                f"(schema {info['schema_version']}) "
                f"{'compatible' if compatible else 'INCOMPATIBLE'}"
            )
        return 0 if compatible else 2

    if args.command == "intake":
        if not _text(args.revision):
            payload = {
                "status": "INVALID",
                "findings": [
                    _finding("MISSING_REVISION", "ERROR", "intake requires --revision.")
                ],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 3
        try:
            record = intake_source(
                Path(args.source),
                revision=args.revision,
                record_id=args.record_id,
            )
        except ValueError as exc:
            payload = {
                "status": "INVALID",
                "findings": [_finding("INTAKE_FAILED", "ERROR", str(exc))],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 3
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        status = record["intake"]["status"]
        summary = {
            "status": status,
            "candidate_count": record["intake"]["candidate_count"],
            "output": args.output,
        }
        if args.json:
            print(json.dumps({**summary, "record": record}, ensure_ascii=False, indent=2))
        else:
            print(
                f"Intake: {status} "
                f"({record['intake']['candidate_count']} candidates)"
            )
        return 0 if status == "PARSED" else 2

    if args.command == "impact":
        impact_map, error = _read_json(Path(args.map), "UNREADABLE_IMPACT_MAP")
        if error is not None:
            print(json.dumps(error, ensure_ascii=False, indent=2))
            return 3
        report = impact_report(
            args.files,
            impact_map,
            rollback=args.rollback,
            dependency_notes=args.dependency_notes,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"Impact: {report['status']}")
            print(f"Components: {', '.join(report['components']) or 'none'}")
            print(f"Risk: {report['risk']}  Reversible: {report['reversible']}")
            for finding in report["findings"]:
                print(f"- {finding['severity']} {finding['code']}: {finding['message']}")
        if report["status"] == "PASS":
            return 0
        if report["status"] == "FINDINGS":
            return 2
        return 3

    if args.command == "sources":
        manifest, error = _read_json(Path(args.manifest), "UNREADABLE_SOURCE_MANIFEST")
        if error is not None:
            print(json.dumps(error, ensure_ascii=False, indent=2))
            return 3
        report = validate_sources(
            manifest, root=Path(args.root) if args.root else None
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"Sources: {report['status']}")
            for finding in report["findings"]:
                print(f"- {finding['severity']} {finding['code']}: {finding['message']}")
        if report["status"] == "PASS":
            return 0
        if report["status"] == "FINDINGS":
            return 2
        return 3

    record, error = _read_json(Path(args.record), "UNREADABLE_RECORD")
    if error is not None:
        print(json.dumps(error, ensure_ascii=False, indent=2))
        return 3
    if not isinstance(record, dict):
        print("Governance check: INVALID\n- Record must be a JSON object.")
        return 3

    if args.command == "trace":
        print(trace_markdown(record))
        return 0
    if args.command == "decide":
        print(decision_markdown(record))
        return 0
    if args.command == "converge":
        items = converge_items(record)
        if args.apply:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema_version": SCHEMA_VERSION,
                "record_id": _text(record.get("record_id")),
                "revision": _text(record.get("revision")),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "items": items,
                "derived": True,
                "non_authoritative": True,
                "limitations": [
                    "This plan does not modify the governance record or approve work.",
                    "Correction executes through native tasks and evidence workflows.",
                ],
            }
            output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({"status": "WRITTEN", "path": str(output), "items": len(items)}))
            return 2 if args.check and items else 0
        if args.json:
            print(json.dumps({"items": items}, ensure_ascii=False, indent=2))
        else:
            print(converge_markdown(record))
        return 2 if args.check and items else 0
    if args.command == "metrics":
        report = metrics_report(record)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(metrics_markdown(report))
        return 0

    root = Path(args.root) if args.root else None
    result = validate_record(
        record,
        root=root,
        required_controls=_parse_required_controls(args.required_controls),
    )
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
