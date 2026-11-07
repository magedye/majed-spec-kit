#!/usr/bin/env python3
"""Workflow support for the majed-controlled workflow.

This bridge lives in the governance extension because a bundled workflow in the
current Spec Kit release installs only its ``workflow.yml``; companion files in
the workflow package are not copied by that path. Keeping the deterministic
logic here makes the bundle install order explicit: the governance extension is
installed before the workflow.

It uses the same stdlib-only governance validator and writes a derived,
non-authoritative evidence artifact. It does not authenticate an owner or
enforce host permissions.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Script directory is on sys.path when invoked as a file.
    from governance_core import validate_record
except ImportError:  # pragma: no cover - defensive for unusual import modes
    validate_record = None  # type: ignore[assignment]

PROFILES = {"quick", "standard", "controlled"}
MODES = {"assess", "execute"}
RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
EVIDENCE_DIR = Path(".specify") / "workflows" / "majed-controlled" / "evidence"


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _finding(code: str, severity: str, message: str, **context: Any) -> dict[str, Any]:
    payload = {"code": code, "severity": severity, "message": message}
    payload.update({key: value for key, value in context.items() if value is not None})
    return payload


def _safe_run_id() -> str:
    run_id = _env("RUN_ID")
    return run_id if RUN_ID_RE.fullmatch(run_id) else "unknown-run"


def _evidence_file() -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    return EVIDENCE_DIR / f"{_safe_run_id()}.json"


def _load_preflight() -> Any:
    raw = _env("PREFLIGHT_STDOUT")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def preflight() -> int:
    profile = _env("PROFILE").lower()
    mode = _env("MODE").lower()
    task = _env("TASK")
    evidence_path = _env("EVIDENCE_PATH")
    checks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    if profile not in PROFILES:
        checks.append({"id": "profile", "status": "BLOCKED", "detail": profile or "(missing)"})
        findings.append(_finding("INVALID_PROFILE", "ERROR", f"Unknown profile {profile!r}."))
    else:
        checks.append({"id": "profile", "status": "PASS", "detail": profile})
    if mode not in MODES:
        checks.append({"id": "mode", "status": "BLOCKED", "detail": mode or "(missing)"})
        findings.append(_finding("INVALID_MODE", "ERROR", f"Unknown mode {mode!r}."))
    else:
        checks.append({"id": "mode", "status": "PASS", "detail": mode})
    if not task:
        checks.append({"id": "task", "status": "BLOCKED", "detail": "missing"})
        findings.append(_finding("MISSING_TASK", "ERROR", "A non-empty task is required."))
    else:
        checks.append({"id": "task", "status": "PASS", "detail": "present"})

    record = None
    if evidence_path:
        candidate = Path(evidence_path)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        if not candidate.is_file():
            checks.append({"id": "evidence", "status": "BLOCKED", "detail": "missing"})
            findings.append(
                _finding("EVIDENCE_PATH_MISSING", "ERROR", f"Evidence path not found: {candidate}")
            )
        else:
            try:
                record = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                checks.append({"id": "evidence", "status": "BLOCKED", "detail": "unreadable"})
                findings.append(
                    _finding("EVIDENCE_UNREADABLE", "ERROR", f"Cannot read evidence: {exc}")
                )
            else:
                if validate_record is not None:
                    result = validate_record(record, root=Path.cwd())
                    findings.extend(
                        item
                        for item in result.get("findings", [])
                        if item.get("severity") == "ERROR"
                    )
                    checks.append(
                        {
                            "id": "evidence",
                            "status": "PASS" if result.get("status") == "PASS" else "BLOCKED",
                            "detail": str(candidate),
                        }
                    )
                else:
                    checks.append(
                        {"id": "evidence", "status": "PASS", "detail": "validator unavailable"}
                    )
    elif profile == "controlled":
        checks.append({"id": "evidence", "status": "BLOCKED", "detail": "required for controlled"})
        findings.append(
            _finding(
                "EVIDENCE_REQUIRED",
                "ERROR",
                "The controlled profile requires a governance record via --input evidence_path=...",
            )
        )
    else:
        checks.append({"id": "evidence", "status": "PASS", "detail": "optional for this profile"})

    errors = [item for item in findings if item["severity"] == "ERROR"]
    payload = {
        "status": "BLOCKED" if errors else "PASS",
        "profile": profile,
        "mode": mode,
        "checks": checks,
        "findings": findings,
        "evidence_record": record is not None,
        "limitations": [
            "This preflight checks input and governance-record consistency only.",
            "It does not authenticate an owner or enforce host-wide permissions.",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False))
    if any(item["code"] in {"INVALID_PROFILE", "INVALID_MODE", "MISSING_TASK"} for item in errors):
        return 3
    return 2 if errors else 0


def record() -> int:
    payload = {
        "schema_version": "1.0",
        "run_id": _safe_run_id(),
        "profile": _env("PROFILE").lower(),
        "mode": _env("MODE").lower(),
        "task": _env("TASK"),
        "evidence_path": _env("EVIDENCE_PATH"),
        "preflight": _load_preflight(),
        "derived": True,
        "non_authoritative": True,
        "host_enforcement": "NOT_IMPLEMENTED",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    path = _evidence_file()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    print(json.dumps({"status": "RECORDED", "path": str(path), "run_id": _safe_run_id()}))
    return 0


def _verdict(value: str, allowed: set[str], pending_value: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in allowed else pending_value


def close() -> int:
    path = _evidence_file()
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
    else:
        payload = {}
    review_choice = _verdict(_env("REVIEW_VERDICT"), {"approve", "reject", "pending"}, "pending")
    accept_choice = _verdict(_env("ACCEPT_VERDICT"), {"accept", "reject", "pending"}, "pending")
    review_status = {
        "approve": "APPROVED_SELF_ASSERTED",
        "reject": "REJECTED",
        "pending": "PENDING",
    }[review_choice]
    # A workflow gate records a choice. It cannot authenticate the owner, so even
    # an "accept" choice remains pending owner acceptance.
    acceptance_status = "REJECTED" if accept_choice == "reject" else "PENDING"
    payload["close"] = {
        "review_status": review_status,
        "review_independent": False,
        "review_source": "WORKFLOW_GATE_SELF_ASSERTED",
        "gate_accept_choice": accept_choice,
        "acceptance_status": acceptance_status,
        "owner_acceptance": "NOT_GRANTED",
        "authenticated": False,
        "limitation": "A workflow gate is not authenticated owner acceptance or host enforcement.",
    }
    payload["owner_acceptance"] = "NOT_GRANTED"
    payload["closed_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "CLOSED",
                "path": str(path),
                "review_status": review_status,
                "acceptance_status": acceptance_status,
                "owner_acceptance": "NOT_GRANTED",
            }
        )
    )
    return 0


def _configure_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1 or arguments[0] not in {"preflight", "record", "close"}:
        print("usage: workflow_bridge.py {preflight|record|close}", file=sys.stderr)
        return 3
    command = arguments[0]
    if command == "preflight":
        return preflight()
    if command == "record":
        return record()
    return close()


if __name__ == "__main__":
    raise SystemExit(main())
