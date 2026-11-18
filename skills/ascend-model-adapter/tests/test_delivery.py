from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "delivery.py"
spec = importlib.util.spec_from_file_location("delivery_under_test", SCRIPT)
delivery = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(delivery)


def public_facts() -> dict[str, str]:
    """Synthetic input for artifact tests; contains no claimed NPU measurements."""
    return {
        "title": "Demo-S3 inference",
        "overview": "A synthetic model documentation fixture.",
        "environment": "Python 3; Ascend compatibility has not been tested.",
        "installation": "Use the included script with python3.",
        "data": "Input is a local UTF-8 text file.",
        "inference": "```bash\npython3 infer.py --input input.txt\n```",
        "evaluation": "No NPU accuracy or performance measurements are available.",
        "limitations": "已完成 CPU 功能测试，尚未在 Ascend NPU 上实测。",
        "faq": "Supports input downloaded from S3 storage.",
        "sources": "https://example.invalid/synthetic-fixture",
    }


class DeliveryTests(unittest.TestCase):
    def cli(self, *args: object):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(arg) for arg in args)],
            text=True, capture_output=True,
        )

    def workspace(self, root: Path):
        source = root / "source"
        source.mkdir()
        (source / "README.md").write_text(delivery.render_facts(public_facts()), encoding="utf-8")
        (source / "infer.py").write_text("print('synthetic fixture')\n", encoding="utf-8")
        (source / "infer.py").chmod(0o755)
        internal = source / ".ascend-adaptation" / "demo"
        internal.mkdir(parents=True)
        (internal / "worklog.json").write_text('{"status":"S2","target_ready":false}')
        (source / "NPU_ADAPTATION.md").write_text("Internal troubleshooting history")
        return source, internal

    def test_render_preserves_validation_gap_commands_and_legitimate_s3(self):
        facts = public_facts()
        text = delivery.render_facts(facts)
        self.assertIn(facts["limitations"], text)
        self.assertIn(facts["inference"], text)
        self.assertIn("Demo-S3", text)
        self.assertIn("S3 storage", text)
        self.assertEqual([], delivery.public_text_findings(text, "README.md"))

    def test_optional_faq_has_no_empty_section_and_required_limits_are_preserved(self):
        for value in (None, "", "   "):
            facts = public_facts()
            if value is None:
                del facts["faq"]
            else:
                facts["faq"] = value
            text = delivery.render_facts(facts)
            self.assertNotIn("常见问题", text)
            self.assertIn(facts["limitations"], text)
            self.assertIn(facts["inference"], text)
        facts["faq"] = "遇到旧缓存时，先确认模型版本。"
        text = delivery.render_facts(facts)
        self.assertIn(facts["faq"], text)
        self.assertIn("## 常见问题", text)

    def test_sources_can_be_inline_without_redundant_reference_section(self):
        for value in (None, "", "   "):
            facts = public_facts()
            facts["overview"] += "\nSource: " + facts["sources"]
            if value is None:
                del facts["sources"]
            else:
                facts["sources"] = value
            text = delivery.render_facts(facts)
            self.assertIn("https://example.invalid/synthetic-fixture", text)
            self.assertNotIn("## 参考来源", text)
        facts["sources"] = "https://example.invalid/second-source"
        self.assertIn(facts["sources"], delivery.render_facts(facts))

    def test_validation_limits_precede_commands_and_are_not_duplicated(self):
        facts = public_facts()
        text = delivery.render_facts(facts)
        self.assertLess(text.index(facts["limitations"]), text.index(facts["installation"]))
        self.assertLess(text.index(facts["limitations"]), text.index(facts["inference"]))
        self.assertEqual(1, text.count(facts["limitations"]))

    def test_reference_cache_cannot_be_published_as_a_candidate_file_or_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            cache = source / ".codex-reference"
            cache.mkdir()
            (cache / "context.md").write_text("private development notes")
            with self.assertRaises(ValueError):
                delivery.assemble(source, ["README.md", ".codex-reference/context.md"],
                                  root / "candidate", internal / "delivery-report.json")
            self.assertFalse((root / "candidate").exists())
            with self.assertRaises(ValueError):
                delivery.render_facts({**public_facts(), "overview": "详见 .codex-reference/context.md"})

    def test_render_preserves_reported_results_and_measurement_conditions(self):
        facts = public_facts()
        # Synthetic results exercise documentation only, never hardware validation.
        facts["evaluation"] = (
            "测试 fixture，非真实测量：dataset=demo，split=test，100 samples；"
            "accuracy=0.9。三次设备延迟为 10/12/11 ms，中位数 11 ms；"
            "batch=1，warmup=5，模型计时且前后同步，不含预处理。"
        )
        facts["limitations"] = "以上数字只用于文档测试，不构成真实 NPU 验证结果。"
        text = delivery.render_facts(facts)
        self.assertIn(facts["evaluation"], text)
        self.assertIn(facts["limitations"], text)

    def test_closed_fields_reject_internal_metadata_and_missing_limits(self):
        for field in ("status", "target_ready", "evidence", "next_steps"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                delivery.render_facts({**public_facts(), field: "internal"})
        facts = public_facts()
        del facts["limitations"]
        with self.assertRaises(ValueError):
            delivery.render_facts(facts)

    def test_rejects_worklog_embedded_inside_allowed_field(self):
        for value in ("当前状态：S2", "**当前状态**：`S2`", '"status": "S3"', "status=S3", "target_ready=false", "## 后续计划\n补验门禁",
                      "详见 .ascend-adaptation/demo/worklog.json", "参见 NPU_ADAPTATION.md"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                delivery.render_facts({**public_facts(), "overview": value})

    def test_nonstring_and_empty_public_values_fail(self):
        for value in (None, {}, [], "   "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                delivery.render_facts({**public_facts(), "limitations": value})

    def test_render_does_not_overwrite_existing_usage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            facts = root / "public-facts.json"
            facts.write_text(json.dumps(public_facts()))
            readme = root / "README.md"
            readme.write_text("Existing user instructions\n")
            result = self.cli("render", "--facts", facts, "--output", readme)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("Existing user instructions\n", readme.read_text())

    def test_assemble_excludes_records_and_preserves_bytes_modes_and_gaps(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            output, report = root / "candidate", internal / "delivery-report.json"
            entries = ["README.md", "infer.py"]
            result = delivery.assemble(source, entries, output, report)
            self.assertEqual(set(entries), {p.name for p in output.iterdir()})
            for entry in entries:
                self.assertEqual((source / entry).read_bytes(), (output / entry).read_bytes())
                self.assertEqual(hashlib.sha256((output / entry).read_bytes()).hexdigest(), result["files"][entry])
            self.assertTrue((output / "infer.py").stat().st_mode & 0o111)
            self.assertTrue((source / "NPU_ADAPTATION.md").exists())
            self.assertTrue((internal / "worklog.json").exists())
            self.assertEqual([], delivery.check_candidate(output))
            self.assertEqual(result, json.loads(report.read_text()))
            self.assertIn(public_facts()["limitations"], (output / "README.md").read_text())

    def test_private_or_noncanonical_entries_fail_before_any_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            for entry in ("NPU_ADAPTATION.md", ".ascend-adaptation/demo/worklog.json",
                          "../outside.txt", "/etc/hosts", "./infer.py", "missing.py",
                          "public-facts.json", "source.log"):
                output = root / "candidate"
                report = internal / "delivery-report.json"
                with self.subTest(entry=entry), self.assertRaises(ValueError):
                    delivery.assemble(source, ["README.md", entry], output, report)
                self.assertFalse(output.exists())
                self.assertFalse(report.exists())

    def test_assembly_rejects_internal_content_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            (source / "README.md").write_text("# Model\n\n当前状态：S2\n")
            with self.assertRaises(ValueError):
                delivery.assemble(source, ["README.md"], root / "candidate", internal / "delivery-report.json")
            self.assertFalse((root / "candidate").exists())

    def test_existing_candidate_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            output = root / "candidate"
            output.mkdir()
            (output / "keep.txt").write_text("keep")
            with self.assertRaises(FileExistsError):
                delivery.assemble(source, ["README.md"], output, internal / "delivery-report.json")
            self.assertEqual("keep", (output / "keep.txt").read_text())

    def test_failed_candidate_rename_rolls_back_only_this_report_and_can_be_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            output, report = root / "candidate", internal / "delivery-report.json"
            with patch.object(delivery.os, "rename", side_effect=OSError("fixture rename failure")):
                with self.assertRaisesRegex(OSError, "fixture rename failure"):
                    delivery.assemble(source, ["README.md"], output, report)
            self.assertFalse(report.exists())
            self.assertFalse(output.exists())
            delivery.assemble(source, ["README.md"], output, report)
            delivery.verify_manifest(report)

    def test_manifest_detects_added_files_and_posix_executable_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            output, report = root / "candidate", internal / "delivery-report.json"
            delivery.assemble(source, ["README.md", "infer.py"], output, report)
            self.assertEqual(0, self.cli("verify", "--report", report).returncode)
            extra = output / "extra.py"
            extra.touch()
            with self.assertRaisesRegex(ValueError, "file set changed"):
                delivery.verify_manifest(report)
            extra.unlink()
            if "executable_bits" in json.loads(report.read_text()):
                (output / "infer.py").chmod(0o644)
                with self.assertRaisesRegex(ValueError, "executable bits"):
                    delivery.verify_manifest(report)

    def test_existing_report_is_preserved_without_creating_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            report = internal / "delivery-report.json"
            report.write_text('{"previous":"keep"}')
            with self.assertRaises(FileExistsError):
                delivery.assemble(source, ["README.md"], root / "candidate", report)
            self.assertEqual('{"previous":"keep"}', report.read_text())
            self.assertFalse((root / "candidate").exists())

    def test_single_readme_check_does_not_require_deleting_internal_records(self):
        with tempfile.TemporaryDirectory() as temp:
            source, _ = self.workspace(Path(temp))
            result = self.cli("check", source / "README.md")
            self.assertEqual(0, result.returncode, result.stderr)
            (source / "README.md").write_text("# Model\n当前状态：S2\n")
            result = self.cli("check", source / "README.md")
            self.assertNotEqual(0, result.returncode)

    def test_symlinked_files_and_directories_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            (source / "linked.py").symlink_to(source / "infer.py")
            (source / "linked-dir").symlink_to(internal, target_is_directory=True)
            for entry in ("linked.py", "linked-dir/worklog.json"):
                with self.subTest(entry=entry), self.assertRaises(ValueError):
                    delivery.assemble(source, ["README.md", entry], root / "candidate", root / "report.json")

    def test_report_and_candidate_cannot_pollute_source_or_each_other(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _ = self.workspace(root)
            for output, report in ((root / "candidate", root / "candidate/report.json"),
                                   (root / "candidate", source / "README.md")):
                with self.subTest(output=output, report=report), self.assertRaises(ValueError):
                    delivery.assemble(source, ["README.md"], output, report)
                self.assertFalse((root / "candidate").exists())

    def test_nested_candidate_uses_explicit_files_without_copying_private_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            source, internal = self.workspace(Path(temp))
            before = (source / "README.md").read_bytes()
            output = source / "candidate"
            report = internal / "delivery-report.json"
            delivery.assemble(source, ["README.md", "infer.py"], output, report)
            self.assertEqual({"README.md", "infer.py"}, {p.name for p in output.iterdir()})
            self.assertEqual(before, (source / "README.md").read_bytes())
            self.assertEqual([], delivery.check_candidate(output))
            self.assertFalse((output / ".ascend-adaptation").exists())

    def test_source_change_during_copy_aborts_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            original_copy = delivery.shutil.copy2
            def mutate_then_copy(src, dst):
                Path(src).write_text("changed during copy")
                return original_copy(src, dst)
            with patch.object(delivery.shutil, "copy2", side_effect=mutate_then_copy):
                with self.assertRaises(ValueError):
                    delivery.assemble(source, ["README.md"], root / "candidate", internal / "delivery-report.json")
            self.assertFalse((root / "candidate").exists())
            self.assertFalse((internal / "delivery-report.json").exists())

    def test_cli_render_assemble_and_check_from_unrelated_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, internal = self.workspace(root)
            facts = internal / "public-facts.json"
            facts.write_text(json.dumps(public_facts()))
            result = self.cli("render", "--facts", facts, "--output", source / "README.md", "--force")
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = internal / "candidate-files.json"
            manifest.write_text(json.dumps(["README.md", "infer.py"]))
            output = root / "candidate"
            result = self.cli("assemble", "--source", source, "--files", manifest,
                              "--output", output, "--report", internal / "delivery-report.json")
            self.assertEqual(0, result.returncode, result.stderr)
            result = self.cli("check", output)
            self.assertEqual(0, result.returncode, result.stderr)
            # The included fixture entry is runnable from the assembled directory.
            run = subprocess.run([sys.executable, "infer.py"], cwd=output, capture_output=True, text=True)
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertIn("synthetic fixture", run.stdout)

    def test_check_detects_private_files_and_english_or_alternate_readmes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _ = self.workspace(root)
            (source / "README.en.md").write_text("# Internal status\n\nstatus=S2\n")
            findings = delivery.check_candidate(source)
            self.assertTrue(any("README.en.md" in item for item in findings))
            self.assertTrue(any("NPU_ADAPTATION.md" in item for item in findings))


class ScaffoldBoundaryTests(unittest.TestCase):
    def scaffold(self, output: Path, *extra: str):
        return subprocess.run([sys.executable, str(ROOT / "scripts/scaffold_adapter.py"),
                               "https://example.invalid/demo.git", str(output),
                               "--category", "cv", "--route", "torch-npu", *extra],
                              text=True, capture_output=True)

    def test_default_workspace_does_not_create_readme(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "workspace"
            result = self.scaffold(output, "--layout", "workspace")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((output / "README.md").exists())
            self.assertTrue((output / ".ascend-adaptation/cv__demo/NPU_ADAPTATION.md").exists())

    def test_explicit_readme_and_legacy_target_are_public_drafts(self):
        with tempfile.TemporaryDirectory() as temp:
            for name, args in (("workspace", ["--layout", "workspace", "--with-readme"]),
                               ("target", ["--layout", "target"])):
                output = Path(temp) / name
                result = self.scaffold(output, *args)
                self.assertEqual(0, result.returncode, result.stderr)
                text = (output / "README.md").read_text()
                self.assertEqual([], delivery.public_text_findings(text, "README.md"))
                self.assertIn("尚未在 Ascend NPU 上实测", text)
                self.assertNotIn("TODO", text)
                self.assertNotIn("脚手架", text)

    def test_repository_internal_location_can_be_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "workspace"
            result = self.scaffold(output, "--layout", "workspace", "--internal-dir", ".")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((output / "NPU_ADAPTATION.md").exists())
            self.assertFalse((output / "README.md").exists())

    def test_scaffold_private_directory_is_excluded_in_existing_git_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "workspace"
            output.mkdir()
            subprocess.run(["git", "init", "-q", str(output)], check=True)
            result = self.scaffold(output, "--layout", "workspace")
            self.assertEqual(0, result.returncode, result.stderr)
            ignored = subprocess.run(["git", "-C", str(output), "check-ignore",
                                      ".ascend-adaptation/cv__demo/NPU_ADAPTATION.md"],
                                     capture_output=True, text=True)
            self.assertEqual(0, ignored.returncode, ignored.stderr)

    def test_force_with_linked_internal_document_does_not_partially_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "workspace"
            internal = output / ".ascend-adaptation/cv__demo"
            internal.mkdir(parents=True)
            marker = root / "keep.md"
            marker.write_text("keep")
            (internal / "NPU_ADAPTATION.md").symlink_to(marker)
            result = self.scaffold(output, "--layout", "workspace", "--force")
            self.assertNotEqual(0, result.returncode)
            self.assertFalse((output / "requirements.txt").exists())
            self.assertEqual("keep", marker.read_text())


if __name__ == "__main__":
    unittest.main()
