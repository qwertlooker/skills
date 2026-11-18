#!/usr/bin/env python3
"""Manage one private Ascend adaptation work log per project."""

from __future__ import annotations

import argparse
import hashlib
import json
import operator
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROUTES = ("onnx-om", "ort-cann", "torch-npu", "torchair", "vllm-ascend", "hybrid")
STATUS_ORDER = ["S0", "S1", "S2", "S3", "S4"]
STATUS_EVIDENCE = {
    "S0": {"target_baseline", "upstream_audit"},
    "S1": {"static_check"},
    "S2": {"functional_inference"},
    "S3": {"npu_accuracy", "npu_performance", "comparison_report"},
    "S4": {"extended_validation"},
}
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
READINESS_EVIDENCE = {"target_audit", "clean_room_replay"}
DEPLOYMENT_EVIDENCE = STATUS_EVIDENCE["S3"] | STATUS_EVIDENCE["S4"] | READINESS_EVIDENCE
EVIDENCE_TYPES = sorted(
    {
        "upstream_audit",
        "target_baseline",
        "upstream_smoke",
        "dependency_smoke",
        "patch_check",
        "onnx_check",
        "atc_compile",
        "npu_inference",
        "functional_inference",
        "npu_accuracy",
        "npu_performance",
        "comparison_report",
        "extended_validation",
        "static_check",
        "target_audit",
        "clean_room_replay",
        "data_dry_run",
        "service_smoke",
        "other",
    }
)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    if not normalized:
        raise ValueError("project id must contain at least one safe character")
    return normalized


def log_path(workspace: Path, project_id: str, internal_dir: Path | None = None) -> Path:
    directory = internal_dir or Path(".ascend-adaptation") / slug(project_id)
    if not directory.is_absolute():
        directory = workspace.resolve() / directory
    return directory / "worklog.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"evidence file does not exist: {path}")
    return {"path": str(path), "sha256": sha256(path)}


def subject_record(path: Path, fields: list[str]) -> dict:
    if not fields:
        return file_record(path)
    path = path.expanduser().resolve()
    raw = path.read_bytes()
    metadata = json.loads(raw)
    if not isinstance(metadata, dict):
        raise ValueError(f"deployment metadata must be a JSON object: {path}")
    missing = sorted(set(fields) - metadata.keys())
    if missing:
        raise ValueError(f"{path}: missing deployment fields {missing}")
    selected = {name: metadata[name] for name in sorted(set(fields))}
    if all(value in (None, "", {}, []) for value in selected.values()):
        raise ValueError(f"{path}: selected deployment fields are empty")
    canonical = json.dumps(selected, sort_keys=True, allow_nan=False, separators=(",", ":"))
    return {
        "path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
        "fields": list(selected), "deployment_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }


@contextmanager
def edit_log(path: Path):
    # A stable lock inode covers the whole read/modify/replace, including init.
    # The OS releases the lock when the handle closes, also after a process dies.
    with path.with_suffix(".lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt

            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def add_git_exclude(workspace: Path, internal_dir: Path | None = None) -> None:
    result = subprocess.run(
        ["git", "-C", str(workspace), "rev-parse", "--show-toplevel"],
        text=True,
        check=False, capture_output=True,
    )
    if result.returncode != 0:
        return
    root = Path(result.stdout.strip()).resolve()
    try:
        directory = internal_dir or workspace.resolve() / ".ascend-adaptation"
        relative = directory.resolve().relative_to(root)
    except ValueError:
        return
    # Anchor to the repository root; escape gitignore pattern metacharacters.
    pattern = "/" + re.sub(r"([\\*?\[\]#! ])", r"\\\1", relative.as_posix()) + "/"
    git_path = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"],
        text=True,
        check=False, capture_output=True,
    )
    if git_path.returncode != 0:
        return
    exclude = Path(git_path.stdout.strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if pattern not in existing.splitlines():
        with exclude.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(pattern + "\n")


def load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"project work log does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_project(path: Path, project_id: str) -> dict:
    data = load(path)
    if data.get("project_id") != slug(project_id):
        raise ValueError(f"work log belongs to another project: {path}")
    return data


def init(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite project work log: {path}")
    data = {
        "schema_version": 2,
        "project_id": slug(args.project_id),
        "model_url": args.model_url,
        "source_revision": args.source_revision,
        "checkpoint": args.checkpoint,
        "target_repo_commit": args.target_repo_commit,
        "target_path_exists": args.target_path_exists,
        "patch_required": args.patch_required,
        "target_path": args.target_path,
        "mode": args.mode,
        "route": args.route,
        "hardware_model": args.hardware_model,
        "status": None,
        "target_ready": False,
        "created_at": now(),
        "updated_at": now(),
        "decisions": [],
        "issues": [],
        "evidence": [],
    }
    write_json(path, data)
    add_git_exclude(args.workspace, path.parent if args.internal_dir else None)
    print(path)
    return 0


def add_evidence(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    data = load_project(path, args.project_id)
    if (args.compared or args.compared_field) and args.type != "comparison_report":
        raise ValueError("scored inputs belong to comparison_report")
    outputs = [Path(value).expanduser().resolve() for value in args.artifact]
    log_file = Path(args.log_path).expanduser().resolve() if args.log_path else None
    artifacts = []
    for artifact in dict.fromkeys(outputs + ([log_file] if log_file else [])):
        artifacts.append({**file_record(artifact), "role": "result" if artifact in outputs else "log"})
    item = {
        "type": args.type,
        "timestamp": now(),
        "command": args.command,
        "exit_code": args.exit_code,
        "claim": args.claim,
        "log_path": str(log_file) if log_file else "",
        "environment": args.environment,
        "artifacts": artifacts,
    }
    if args.subject:
        item["subject"] = subject_record(args.subject, args.subject_fields)
    if args.compared:
        paths = dict.fromkeys(path.expanduser().resolve() for path in args.compared)
        item["compared"] = [file_record(path) for path in paths]
    if args.require:
        if args.type not in {"comparison_report", "npu_performance", "extended_validation"}:
            raise ValueError("--require belongs to a comparison, performance or extended validation report")
        item["criteria"] = args.require
    if args.compared_field:
        item["compared_field"] = args.compared_field
    if args.compared_field or args.require:
        report = native_report(item)
        if args.compared_field:
            comparison_inputs(item, report)
        # A failed native verdict is still part of the history. Apply the
        # criterion when checking a level, not when recording the observation.
    data["evidence"].append(item)
    # Readiness is a snapshot; a new relevant result requires reassessment.
    readiness_types = set().union(*STATUS_EVIDENCE.values()) | READINESS_EVIDENCE | {"patch_check"}
    if args.type in readiness_types:
        data["target_ready"] = False
    data["updated_at"] = now()
    write_json(path, data)
    return 0


def required_evidence(data: dict, status: str) -> set[str]:
    required = set().union(
        *(STATUS_EVIDENCE[level] for level in STATUS_ORDER[:STATUS_ORDER.index(status) + 1])
    )
    if status != "S0" and data.get("patch_required"):
        required.add("patch_check")
    return required


class CriterionFailed(ValueError):
    """A measured value violates an explicit acceptance criterion."""


def unique_report_fields(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate report field {key!r}")
        result[key] = value
    return result


def parse_report_value(raw: bytes | str):
    # Compare the values written by the evaluator without binary-float rounding.
    try:
        return json.loads(raw, parse_float=Decimal, parse_constant=Decimal,
                          object_pairs_hook=unique_report_fields)
    except InvalidOperation as exc:
        raise ValueError("number exceeds supported decimal range") from exc


def finite_report_number(value) -> bool:
    return type(value) is int or (isinstance(value, Decimal) and value.is_finite())


def check_metrics(report: dict, checks: list, *, require_decision: bool) -> None:
    if not isinstance(report, dict):
        raise ValueError("expected a JSON object containing the measured values")
    comparisons = {"eq": operator.eq, "ge": operator.ge, "le": operator.le,
                   "gt": operator.gt, "lt": operator.lt}
    failures, unknown = [], []
    verdict = report.get("passed")
    if "passed" in report and type(verdict) is not bool:
        raise ValueError("native verdict passed must be a JSON boolean")
    if verdict is False:
        failures.append("native verdict passed=false")
    elif require_decision and verdict is not True and not checks:
        raise ValueError("no native boolean verdict; supply the task's --require FIELD OP VALUE")

    for field, op, threshold in checks:
        if op not in comparisons:
            raise ValueError(f"invalid operator {op!r}; choose from {list(comparisons)}")
        expected = parse_report_value(threshold)
        actual = report.get(field)
        if type(expected) is bool:
            if op != "eq":
                raise ValueError("boolean criteria require eq")
            comparable = type(actual) is bool
        elif finite_report_number(expected):
            comparable = finite_report_number(actual)
        else:
            raise ValueError(f"{field}: expected a finite numeric or boolean threshold")
        if not comparable:
            unknown.append(f"{field}: missing, non-finite or wrong measurement type")
        elif not comparisons[op](actual, expected):
            failures.append(f"{field}={actual} violates {op} {expected}")
    if failures:
        raise CriterionFailed("; ".join(failures + unknown))
    if unknown:
        raise ValueError("; ".join(unknown))


def native_report(item: dict) -> dict | None:
    results = [Path(a["path"]) for a in item["artifacts"] if a.get("role") == "result"]
    explicit = item.get("compared_field") or item.get("criteria")
    if len(results) != 1 or (not explicit and results[0].suffix.lower() != ".json"):
        if explicit:
            raise ValueError("--compared-field or --require needs one native JSON report as --artifact")
        return None
    report = parse_report_value(results[0].read_bytes())
    if isinstance(report, dict):
        return report
    if explicit:
        raise ValueError(f"{results[0]}: expected a JSON object")
    return None


def comparison_inputs(item: dict, report: dict | None) -> list[str]:
    field = item.get("compared_field")
    if not field:
        return sorted(ref["sha256"] for ref in item.get("compared", []))
    if report is None or field not in report:
        raise ValueError(f"native report missing candidate result digest field {field!r}")
    recorded = report[field]
    hashes = recorded if isinstance(recorded, list) else [recorded]
    if not hashes or not all(isinstance(h, str) and re.fullmatch(r"[0-9a-fA-F]{64}", h) for h in hashes):
        raise ValueError(f"{field!r} must contain SHA256 hex digests of scored results")
    return sorted(h.lower() for h in hashes)


def validate_deployment(latest: dict, kinds: set[str], expected: dict | None) -> None:
    # Identity concerns the deployment. Workloads and timestamps need not match.
    subjects = {}
    for kind in sorted(kinds):
        item = latest[kind]
        if not any(a["sha256"] != EMPTY_SHA256 for a in item.get("artifacts", [])):
            raise ValueError(f"{kind}: missing nonempty native result (--artifact or --log-path)")
        subject = item.get("subject")
        if not subject and kind == "comparison_report":
            continue  # A derived verdict inherits the subject of the scored files.
        if not subject or subject["sha256"] == EMPTY_SHA256:
            raise ValueError(f"{kind}: link the measured --subject from the run or its archive")
        subjects[kind] = subject
    if expected:
        subjects["deployment to verify"] = expected
    identities = {ref.get("deployment_sha256", ref["sha256"]) for ref in subjects.values()}
    if len(identities) != 1:
        sources = ", ".join(f"{kind}={ref['path']}" for kind, ref in subjects.items())
        raise ValueError(f"deployment subjects differ; check the measured configurations: {sources}")

    outputs = sorted(
        a["sha256"] for a in latest["npu_accuracy"]["artifacts"] if a.get("role") == "result"
    )
    comparison = latest["comparison_report"]
    report = native_report(comparison)
    inputs = comparison_inputs(comparison, report)
    if not outputs or set(outputs) == {EMPTY_SHA256} or inputs != outputs:
        raise ValueError(
            "comparison_report inputs (--compared-field or --compared) must match the current npu_accuracy "
            "--artifact result files; score the saved results again if needed"
        )
    if report is not None:
        check_metrics(report, comparison.get("criteria", []), require_decision=False)
    for kind in sorted(kinds - {"comparison_report", "npu_accuracy"}):
        item = latest[kind]
        report = native_report(item)
        if report is not None:
            check_metrics(report, item.get("criteria", []), require_decision=False)


def validate_evidence(data: dict, required: set[str], expected: dict | None = None) -> None:
    # Records of one type describe the same frozen scope. Keep history, but
    # never use an earlier success to override a later failed acceptance run.
    latest = {item["type"]: item for item in data["evidence"]}
    invalidated = {kind for kind in required if latest.get(kind, {}).get("invalidated_by")}
    if invalidated:
        raise ValueError(
            f"evidence invalidated by context change: {sorted(invalidated)}; "
            "review and register current results"
        )
    missing = {
        kind for kind in required
        if latest.get(kind, {}).get("exit_code") != 0
    }
    if missing:
        raise ValueError(f"missing successful latest evidence: {sorted(missing)}")
    digests = {}
    for kind in sorted(required):
        item = latest[kind]
        files = [*item.get("artifacts", []), *item.get("compared", [])]
        if item.get("subject"):
            files.append(item["subject"])
        for artifact in files:
            path = Path(artifact["path"])
            if path not in digests:
                digests[path] = sha256(path) if path.is_file() else None
            if digests[path] != artifact["sha256"]:
                raise ValueError(f"evidence artifact missing or changed for {kind}: {path}")

    formal = required & DEPLOYMENT_EVIDENCE
    if formal:
        validate_deployment(latest, formal, expected)
    elif expected:
        raise ValueError("deployment matching is available for S3 and above")


def verify_status(data: dict, status: str, *, ready: bool = False, expected: dict | None = None) -> None:
    if status not in STATUS_ORDER:
        raise ValueError("no recorded status to verify")
    if ready and status not in {"S3", "S4"}:
        raise ValueError("target readiness requires technical status S3 or S4")
    fields = ["target_repo_commit", "target_path_exists", "source_revision", "checkpoint"]
    if STATUS_ORDER.index(status) >= STATUS_ORDER.index("S2"):
        fields.extend(["route", "hardware_model"])
    missing = [key for key in fields if data.get(key) in {None, "", "undecided", "unconfirmed"}]
    if missing:
        raise ValueError(f"confirm project context before {status}: {missing}")
    required = required_evidence(data, status)
    if ready:
        required |= READINESS_EVIDENCE
    validate_evidence(data, required, expected)


def set_status(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    data = load_project(path, args.project_id)
    current = data["status"]
    expected_index = 0 if current is None else STATUS_ORDER.index(current) + 1
    target_index = STATUS_ORDER.index(args.status)
    if target_index != expected_index:
        expected = (
            STATUS_ORDER[expected_index]
            if expected_index < len(STATUS_ORDER)
            else "none"
        )
        raise ValueError(
            f"status transitions must be sequential: current={current}, expected={expected}"
        )
    verify_status(data, args.status)
    data["status"] = args.status
    data["updated_at"] = now()
    write_json(path, data)
    return 0


def add_decision(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    data = load_project(path, args.project_id)
    data["decisions"].append(
        {
            "timestamp": now(),
            "decision": args.decision,
            "rationale": args.rationale,
            "alternatives": args.alternatives,
            "impact": args.impact,
        }
    )
    data["updated_at"] = now()
    write_json(path, data)
    return 0


def add_issue(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    data = load_project(path, args.project_id)
    data["issues"].append(
        {
            "timestamp": now(),
            "phase": args.phase,
            "symptom": args.symptom,
            "attempts": args.attempts,
            "root_cause": args.root_cause,
            "fix": args.fix,
            "reusable": args.reusable,
        }
    )
    data["updated_at"] = now()
    write_json(path, data)
    return 0


def update_context(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    data = load_project(path, args.project_id)
    status = data.get("status")
    baseline_keys = {
        "source_revision",
        "checkpoint",
        "target_repo_commit",
        "target_path_exists",
    }
    patch_keys = {"patch_required"}
    route_keys = {"route", "hardware_model"}
    changes = {}
    for key in (
        "source_revision",
        "checkpoint",
        "target_repo_commit",
        "target_path_exists",
        "patch_required",
        "route",
        "hardware_model",
    ):
        value = getattr(args, key)
        if value is not None:
            if status is not None and key in baseline_keys and value != data.get(key):
                raise ValueError(
                    f"{key} is frozen after S0; start a new project log for a new baseline"
                )
            if (
                status in {"S1", "S2", "S3", "S4"}
                and key in patch_keys
                and value != data.get(key)
            ):
                raise ValueError("patch_required is frozen after S1")
            if (
                status in {"S2", "S3", "S4"}
                and key in route_keys
                and value != data.get(key)
            ):
                raise ValueError(
                    f"{key} is frozen after S2; start a new project log for a new route/hardware"
                )
            if value != data.get(key):
                changes[key] = {"before": data.get(key), "after": value}
                data[key] = value
    if changes:
        changed_keys = set(changes)
        # Preserve history while preventing observations of an old context from
        # certifying a new one, even before its status has been frozen.
        if changed_keys & baseline_keys:
            affected = set(EVIDENCE_TYPES)
        elif changed_keys & patch_keys:
            affected = set(EVIDENCE_TYPES) - STATUS_EVIDENCE["S0"]
        else:
            affected = set(EVIDENCE_TYPES) - STATUS_EVIDENCE["S0"] - {
                "static_check", "patch_check"
            }
        timestamp = now()
        data.setdefault("context_changes", []).append({"timestamp": timestamp, "changes": changes})
        for item in data["evidence"]:
            if item["type"] in affected:
                item.setdefault("invalidated_by", []).append({"timestamp": timestamp, "changes": changes})
        data["target_ready"] = False
    data["updated_at"] = now()
    write_json(path, data)
    return 0


def set_target_ready(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    data = load_project(path, args.project_id)
    verify_status(data, data.get("status"), ready=True)
    data["target_ready"] = True
    data["updated_at"] = now()
    write_json(path, data)
    return 0


def show(args: argparse.Namespace) -> int:
    path = log_path(args.workspace, args.project_id, args.internal_dir)
    data = load_project(path, args.project_id)
    if args.subject and not args.verify:
        raise ValueError("--subject requires --verify")
    if args.verify:
        expected = subject_record(args.subject, args.subject_fields) if args.subject else None
        verify_status(data, data.get("status"), ready=data.get("target_ready", False), expected=expected)
        print("Recorded evidence and file links verified.", file=sys.stderr)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Create a new project-specific work log"
    )
    init_parser.add_argument("--workspace", type=Path, required=True)
    init_parser.add_argument("--project-id", required=True)
    init_parser.add_argument("--model-url", required=True)
    init_parser.add_argument("--source-revision", default="unconfirmed")
    init_parser.add_argument("--checkpoint", default="unconfirmed")
    init_parser.add_argument("--target-repo-commit", default="unconfirmed")
    init_parser.add_argument(
        "--target-path-exists",
        choices=["yes", "no", "unconfirmed"],
        default="unconfirmed",
    )
    init_parser.add_argument("--patch-required", action="store_true")
    init_parser.add_argument("--target-path", required=True)
    init_parser.add_argument(
        "--mode", choices=["adapt", "review", "deliver", "resume"], default="adapt"
    )
    init_parser.add_argument(
        "--route",
        choices=["undecided", *ROUTES],
        default="undecided",
    )
    init_parser.add_argument("--hardware-model", default="unconfirmed")
    init_parser.set_defaults(func=init)

    evidence_parser = subparsers.add_parser(
        "add-evidence", help="Append command/result evidence"
    )
    evidence_parser.add_argument("--workspace", type=Path, required=True)
    evidence_parser.add_argument("--project-id", required=True)
    evidence_parser.add_argument("--type", choices=EVIDENCE_TYPES, required=True)
    evidence_parser.add_argument("--command", required=True)
    evidence_parser.add_argument("--exit-code", type=int, required=True)
    evidence_parser.add_argument("--claim", required=True)
    evidence_parser.add_argument("--log-path", default="")
    evidence_parser.add_argument("--environment", default="")
    evidence_parser.add_argument("--artifact", action="append", default=[])
    scored = evidence_parser.add_mutually_exclusive_group()
    scored.add_argument("--compared-field", help="Native JSON report field containing the scored candidate SHA256(s)")
    scored.add_argument("--compared", type=Path, action="append", default=[],
                        help="Immutable candidate result read in this comparison; repeat for each input")
    evidence_parser.set_defaults(func=add_evidence)

    status_parser = subparsers.add_parser(
        "set-status", help="Advance one validated status"
    )
    status_parser.add_argument("--workspace", type=Path, required=True)
    status_parser.add_argument("--project-id", required=True)
    status_parser.add_argument("--status", choices=STATUS_ORDER, required=True)
    status_parser.set_defaults(func=set_status)

    decision_parser = subparsers.add_parser(
        "add-decision", help="Append an adaptation decision"
    )
    decision_parser.add_argument("--workspace", type=Path, required=True)
    decision_parser.add_argument("--project-id", required=True)
    decision_parser.add_argument("--decision", required=True)
    decision_parser.add_argument("--rationale", required=True)
    decision_parser.add_argument("--alternatives", default="")
    decision_parser.add_argument("--impact", default="")
    decision_parser.set_defaults(func=add_decision)

    issue_parser = subparsers.add_parser(
        "add-issue", help="Append a troubleshooting record"
    )
    issue_parser.add_argument("--workspace", type=Path, required=True)
    issue_parser.add_argument("--project-id", required=True)
    issue_parser.add_argument("--phase", required=True)
    issue_parser.add_argument("--symptom", required=True)
    issue_parser.add_argument("--attempts", default="")
    issue_parser.add_argument("--root-cause", required=True)
    issue_parser.add_argument("--fix", required=True)
    issue_parser.add_argument("--reusable", action="store_true")
    issue_parser.set_defaults(func=add_issue)

    context_parser = subparsers.add_parser(
        "update-context", help="Update frozen project context"
    )
    context_parser.add_argument("--workspace", type=Path, required=True)
    context_parser.add_argument("--project-id", required=True)
    context_parser.add_argument("--source-revision")
    context_parser.add_argument("--checkpoint")
    context_parser.add_argument("--target-repo-commit")
    context_parser.add_argument(
        "--target-path-exists", choices=["yes", "no", "unconfirmed"]
    )
    context_parser.add_argument(
        "--patch-required", action=argparse.BooleanOptionalAction, default=None
    )
    context_parser.add_argument(
        "--route",
        choices=["undecided", *ROUTES],
    )
    context_parser.add_argument("--hardware-model")
    context_parser.set_defaults(func=update_context)

    ready_parser = subparsers.add_parser(
        "set-target-ready",
        help="Mark target readiness after S3/S4, audit, and clean-room replay",
    )
    ready_parser.add_argument("--workspace", type=Path, required=True)
    ready_parser.add_argument("--project-id", required=True)
    ready_parser.set_defaults(func=set_target_ready)

    show_parser = subparsers.add_parser("show", help="Print a project work log")
    show_parser.add_argument("--workspace", type=Path, required=True)
    show_parser.add_argument("--project-id", required=True)
    show_parser.add_argument("--verify", action="store_true", help="Recheck historical status and readiness without writing")
    show_parser.set_defaults(func=show)

    check_parser = subparsers.add_parser("check-report", help="Apply acceptance criteria to a native JSON report without a log")
    check_parser.add_argument("report", type=Path)
    for command in (check_parser, evidence_parser):
        command.add_argument("--require", nargs=3, action="append", default=[],
                             metavar=("FIELD", "OP", "VALUE"),
                             help="Top-level native metric, eq/ge/le/gt/lt, JSON number or boolean; repeat for joint criteria")

    for command in (evidence_parser, show_parser):
        command.add_argument("--subject", type=Path, help="Measured run metadata or resolved deployment description")
        command.add_argument("--subject-fields", nargs="+", default=[], metavar="KEY",
                             help="Compare these top-level deployment fields of native JSON run metadata")

    for command in (init_parser, evidence_parser, status_parser, decision_parser,
                    issue_parser, context_parser, ready_parser, show_parser):
        command.add_argument(
            "--internal-dir", type=Path,
            help="Project-private directory, relative to workspace or absolute; pass on every command",
        )

    args = parser.parse_args()
    if getattr(args, "subject_fields", None) and not args.subject:
        parser.error("--subject-fields requires --subject")
    try:
        if args.command_name == "check-report":
            check_metrics(parse_report_value(args.report.read_bytes()), args.require, require_decision=True)
            print("Declared report criteria satisfied.")
            return 0
        if args.func == show:
            return show(args)
        path = log_path(args.workspace, args.project_id, args.internal_dir)
        if args.func == init:
            path.parent.mkdir(parents=True, exist_ok=True)
        elif not path.is_file():
            raise FileNotFoundError(f"project work log does not exist: {path}")
        with edit_log(path):
            return args.func(args)
    except CriterionFailed as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
