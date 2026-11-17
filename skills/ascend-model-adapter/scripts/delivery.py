#!/usr/bin/env python3
"""Render public facts, check delivery boundaries, and assemble explicit files.

This tool does not execute model commands or certify validation claims. Natural
language, evidence validity, and reproducibility still require review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from string import Template

PUBLIC_FIELDS = {
    "title", "overview", "environment", "installation", "data", "inference",
    "evaluation", "limitations", "faq", "sources",
}
PRIVATE_NAMES = {
    ".ascend-adaptation", "worklog.json", "npu_adaptation.md",
    "acceptance_plan.md", "public-facts.json", "publication-provenance.json",
    "candidate-files.json", "delivery-report.json", ".git", "__pycache__",
    ".cache", "upstream", ".codex-reference",
}
PRIVATE_REFERENCE = re.compile(
    r"\.ascend-adaptation|\.codex-reference|worklog\.json|NPU_ADAPTATION\.md|ACCEPTANCE_PLAN\.md|"
    r"public-facts\.json|publication-provenance\.json|candidate-files\.json|"
    r"delivery-report\.json|\btarget_ready\b|\bevidence_id\s*[:=]",
    re.I,
)
PROCESS_STATE = re.compile(
    r"(?:当前|内部|技术|适配|项目|验收)(?:状态|阶段|等级|进度)\s*[:：=]?\s*S[0-4](?![A-Za-z0-9])|"
    r"\b(?:status|stage)[\"']?\s*[:=]\s*['\"]?S[0-4](?![A-Za-z0-9])|"
    r"(?<![\w-])S0\s*[–—-]\s*S4(?![\w-])|"
    r"(?<![\w-])S[0-4]\s+(?:分析完成|静态适配|功能验证完成|L2\s*迁移|扩展验收)",
    re.I,
)
PROCESS_HEADING = re.compile(
    r"^\s*#{1,6}\s+(?:内部状态|内部验收|当前进度|适配进度|门禁进度|"
    r"验收门禁|证据日志|后续计划|待办事项|工作日志|"
    r"adaptation\s+status|internal\s+status|internal\s+next\s+steps|work\s*log)\b",
    re.I,
)


def public_text_findings(text: str, label: str) -> list[str]:
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        process_line = re.sub(r"[*`_]", "", line)
        if PRIVATE_REFERENCE.search(line):
            findings.append(f"{label}:{number}: internal field or record reference")
        elif PROCESS_STATE.search(process_line) or PROCESS_HEADING.search(process_line):
            findings.append(f"{label}:{number}: internal process state or heading")
    return findings


def private_reason(path: PurePosixPath) -> str | None:
    if any(part.casefold() in PRIVATE_NAMES for part in path.parts):
        return "internal record, development checkout, or cache"
    if path.suffix.casefold() in {".log", ".pyc"}:
        return "runtime log or bytecode"
    return None


def check_candidate(root: Path) -> list[str]:
    if root.is_file() and not root.is_symlink() and root.suffix.casefold() == ".md":
        reason = private_reason(PurePosixPath(root.name))
        if reason:
            return [f"{root}: {reason}"]
        return public_text_findings(root.read_text(encoding="utf-8"), root.name)
    if not root.is_dir() or root.is_symlink():
        return [f"{root}: expected a candidate directory, not a link"]
    findings = []
    if not (root / "README.md").is_file():
        findings.append("README.md: missing")
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            findings.append(f"{relative}: symbolic links are not delivery files")
            continue
        reason = private_reason(PurePosixPath(relative.as_posix()))
        if reason:
            findings.append(f"{relative}: {reason}")
        elif path.is_file() and path.suffix.casefold() == ".md":
            findings.extend(public_text_findings(path.read_text(encoding="utf-8"), str(relative)))
    return findings


def require_clean(findings: list[str]) -> None:
    if findings:
        raise ValueError("\n".join(findings))


def render_facts(facts: object) -> str:
    if not isinstance(facts, dict):
        raise ValueError("public facts must be a JSON object")
    unknown = set(facts) - PUBLIC_FIELDS
    missing = (PUBLIC_FIELDS - {"faq", "sources"}) - set(facts)
    if unknown or missing:
        raise ValueError(f"unknown public fields: {sorted(unknown)}; missing: {sorted(missing)}")
    for name, value in facts.items():
        if not isinstance(value, str) or (name not in {"faq", "sources"} and not value.strip()):
            raise ValueError(f"public field {name} must be a nonempty Markdown string")
    if "\n" in facts["title"] or "\r" in facts["title"]:
        raise ValueError("title must be a single line")
    template = Path(__file__).resolve().parents[1] / "assets" / "readme.md.template"
    faq = facts.get("faq", "").strip()
    sources = facts.get("sources", "").strip()
    values = {
        **facts,
        "faq_section": f"\n## 常见问题\n\n{faq}\n" if faq else "",
        "sources_section": f"\n## 参考来源\n\n{sources}\n" if sources else "",
    }
    result = Template(template.read_text(encoding="utf-8")).substitute(values)
    require_clean(public_text_findings(result, "README.md"))
    return result


def atomic_write(path: Path, content: str, force: bool = False) -> None:
    if path.is_symlink() or (path.exists() and not force):
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(content)
            handle.close()
            if not force and path.exists():
                raise FileExistsError(f"refusing to overwrite {path}")
            temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def selected_files(source: Path, entries: object) -> list[Path]:
    if not isinstance(entries, list) or not entries:
        raise ValueError("candidate file list must be a nonempty JSON array")
    selected = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, str) or not entry or "\\" in entry:
            raise ValueError("each candidate entry must be a relative POSIX file path")
        relative = PurePosixPath(entry)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in entry.split("/")):
            raise ValueError(f"candidate path escapes or is not canonical: {entry}")
        if entry in seen:
            raise ValueError(f"duplicate candidate file: {entry}")
        seen.add(entry)
        reason = private_reason(relative)
        if reason:
            raise ValueError(f"{entry}: {reason}")
        path = source
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise ValueError(f"{entry}: symbolic links are not delivery files")
        if not path.is_file() or not path.resolve().is_relative_to(source):
            raise ValueError(f"{entry}: expected a file inside source")
        selected.append(path)
    if "README.md" not in seen:
        raise ValueError("candidate file list must include README.md")
    return selected


def assemble(source: Path, entries: object, output: Path, report: Path) -> dict:
    if source.is_symlink() or not source.is_dir():
        raise ValueError("source must be a directory, not a symbolic link")
    if output.is_symlink() or output.exists():
        raise FileExistsError(f"refusing to replace candidate directory: {output}")
    source = source.resolve()
    output = output.absolute()
    resolved_output = output.resolve()
    if source.is_relative_to(resolved_output):
        raise ValueError("candidate cannot be the source or contain the source")
    if report.resolve().is_relative_to(resolved_output):
        raise ValueError("delivery report must stay outside the candidate")
    paths = selected_files(source, entries)
    if report.resolve() in {path.resolve() for path in paths}:
        raise ValueError("delivery report cannot overwrite a source file")
    if report.exists() or report.is_symlink():
        raise FileExistsError(f"refusing to overwrite delivery report: {report}")
    findings = []
    for path in paths:
        if path.suffix.casefold() == ".md":
            findings.extend(public_text_findings(path.read_text(encoding="utf-8"), str(path.relative_to(source))))
    require_clean(findings)
    hashes = {path.relative_to(source).as_posix(): digest(path) for path in paths}
    result = {"source": str(source), "candidate": str(resolved_output), "files": hashes}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".ascend-delivery-", dir=output.parent) as temporary:
        staged = Path(temporary) / "candidate"
        staged.mkdir()
        for path in paths:
            relative = path.relative_to(source)
            destination = staged / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            if digest(destination) != hashes[relative.as_posix()]:
                raise ValueError(f"source changed during assembly: {relative}")
        require_clean(check_candidate(staged))
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"candidate directory appeared during assembly: {output}")
        # Write provenance outside the candidate before exposing the new directory.
        atomic_write(report, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        os.rename(staged, output)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    render = commands.add_parser("render", help="Render only approved public fields")
    render.add_argument("--facts", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)
    render.add_argument("--force", action="store_true")
    check = commands.add_parser("check", help="Check explicit information boundaries")
    check.add_argument("candidate", type=Path, help="A public Markdown file or an assembled candidate directory")
    package = commands.add_parser("assemble", help="Copy an explicit list into a new candidate")
    package.add_argument("--source", type=Path, required=True)
    package.add_argument("--files", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "render":
            content = render_facts(json.loads(args.facts.read_text(encoding="utf-8")))
            atomic_write(args.output, content, force=args.force)
            print(args.output)
        elif args.action == "check":
            require_clean(check_candidate(args.candidate))
            print("Delivery boundary checks passed; semantic review and runtime validation remain required.")
        else:
            if args.report.resolve() == args.files.resolve():
                raise ValueError("delivery report cannot overwrite the candidate file list")
            result = assemble(args.source, json.loads(args.files.read_text(encoding="utf-8")), args.output, args.report)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
