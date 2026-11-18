from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"


def load_script(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(f"test_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ModelZooSamplerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script("modelzoo_sampler.py")

    def test_filter_and_non_destructive_clone(self):
        entry = self.module.Entry(
            "audio", "DemoASR", "/x", "1 天前", 1, 1, "vLLM route"
        )
        self.assertEqual(
            [entry], self.module.filter_entries([entry], {"audio"}, ["vllm"])
        )
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "existing"
            destination.mkdir()
            marker = destination / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                self.module.clone_sparse([entry], destination)
            self.assertEqual("keep", marker.read_text(encoding="utf-8"))


class ReviewSamplerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script("gitcode_pr_review_sampler.py")

    def test_exact_pr_path_and_noise(self):
        mapping = self.module.parse_pr_path(["12=ACL_PyTorch/built-in/cv/Demo"])
        self.assertEqual({12: ["ACL_PyTorch/built-in/cv/Demo"]}, mapping)
        self.assertEqual(
            ["ACL_PyTorch/built-in/cv/Demo"],
            self.module.match_paths(
                ["ACL_PyTorch/built-in/cv/Demo/README.md"], mapping[12]
            ),
        )
        self.assertTrue(self.module.is_noise("changed the description"))
        self.assertTrue(self.module.is_noise("AI 代码审查执行失败，请稍后重试"))

    def test_discussions_follow_cursor_and_validate_complete_count(self):
        pages = [
            {"page_num": 1, "page_count": 2, "total": 2,
             "content": {"data": [{"id": 1}], "end_id": 1, "end_system_id": 4}},
            {"page_num": 2, "page_count": 2, "total": 2,
             "content": {"data": [{"id": 2}]}},
        ]
        with patch.object(self.module, "get_json", side_effect=pages) as get:
            result = self.module.fetch_discussions(None, "https://example.invalid/discussions", {})
        self.assertEqual(2, result["pages"])
        self.assertEqual([1, 2], [row["id"] for row in result["content"]["data"]])
        self.assertIn("end_id=1", get.call_args_list[1].args[1])
        self.assertIn("end_system_id=4", get.call_args_list[1].args[1])

    def test_discussions_reject_schema_repeat_and_incomplete_results(self):
        first = {"page_num": 1, "page_count": 2, "total": 2,
                 "content": {"data": [{"id": 1}], "end_id": 1, "end_system_id": 4}}
        repeated = {**first, "page_num": 2}
        incomplete = {"page_num": 1, "page_count": 1, "total": 2,
                      "content": {"data": [{"id": 1}]}}
        for pages in ([{}], [first, repeated], [incomplete]):
            with self.subTest(pages=pages), patch.object(self.module, "get_json", side_effect=pages):
                result = self.module.fetch_discussions(None, "https://example.invalid/discussions", {})
                self.assertIn("_error", result)

    def test_pr_metadata_without_head_is_not_accepted(self):
        with patch.object(self.module, "get_json", return_value={"iid": 1}), \
             patch.object(self.module, "fetch_discussions", return_value={"total": 0, "pages": 1, "content": {"data": []}}):
            detail, _ = self.module.fetch_pr(None, "https://example.invalid", "org/repo", 1, {})
        self.assertIn("_error", detail)

    def test_every_expected_pr_directory_must_match(self):
        argv = ["sampler", "--pr-path", "1=A", "--pr-path", "1=B"]
        with patch.object(sys, "argv", argv), \
             patch.object(self.module, "fetch_pr", return_value=({"iid": 1, "sha": "head"}, [])), \
             patch.object(self.module, "fetch_diff_paths", return_value=(["A/README.md"], None)), \
             patch.object(self.module.time, "sleep"), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = self.module.main()
        self.assertEqual(3, result)


class QuickcheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script("modelzoo_pr_quickcheck.py")

    def test_setext_heading_is_not_conflict_and_compile_is_clean(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "ACL_PyTorch/built-in/cv/Demo"
            target.mkdir(parents=True)
            readme = target / "README.md"
            readme.write_text("Title\n=======\n", encoding="utf-8")
            script = target / "infer.py"
            script.write_text("print('ok')\n", encoding="utf-8")
            self.assertEqual([], self.module.check_conflict_markers(root, [target]))
            self.assertEqual([], self.module.check_py_compile(target))
            self.assertFalse(any(target.rglob("__pycache__")))
            readme.write_text(
                "<<<<<<< ours\na\n=======\nb\n>>>>>>> theirs\n", encoding="utf-8"
            )
            self.assertEqual(1, len(self.module.check_conflict_markers(root, [target])))

    def test_review_patterns_flag_failure_handling_and_allow_source_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "ACL_PyTorch/built-in/cv/Demo"
            target.mkdir(parents=True)
            (target / "README.md").write_text(
                "https://huggingface.co/org/repo/blob/main/model.bin\n",
                encoding="utf-8",
            )
            (target / "run.py").write_text(
                "import subprocess\nsubprocess.run(['false'])\n", encoding="utf-8"
            )
            findings = self.module.check_review_patterns(root, target)
            messages = [finding.message for finding in findings]
            self.assertTrue(any("child failure" in message for message in messages))
            self.assertTrue(any("HTML" in message for message in messages))
            self.assertFalse(any(finding.level == "ERROR" for finding in findings))

    def test_ambiguous_device_and_data_calls_require_content_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "ACL_PyTorch/built-in/cv/Demo"
            target.mkdir(parents=True)
            (target / "infer.py").write_text(
                'device = "npu:0"\nfrom datasets import load_dataset\n'
                'data = datasets.load_dataset("demo")\n',
                encoding="utf-8",
            )
            findings = self.module.check_modelzoo_constraints(root, target)
            messages = [finding.message for finding in findings]
            self.assertTrue(any("indexed device" in message for message in messages))
            self.assertTrue(
                any("data-loading API" in message for message in messages)
            )
            self.assertTrue(all(finding.level == "INFO" for finding in findings))

    def test_valid_historical_names_and_source_link_do_not_fail_strict_cli(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "Demo"
            target.mkdir()
            (target / "dscore_tool").mkdir()
            (target / "run_eval.sh").write_text("#!/bin/sh\nexit 0\n")
            (target / "README.md").write_text(
                "# Demo\n\nbash run_eval.sh\n\nEvaluator: dscore_tool/\n\n"
                "[Source](https://huggingface.co/org/repo/blob/main/model.bin)\n"
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "modelzoo_pr_quickcheck.py"),
                 str(root), "--target", "Demo", "--no-ruff", "--strict"],
                capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class ScaffoldTests(unittest.TestCase):
    def test_collision_does_not_partially_write(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "out"
            output.mkdir()
            requirements = output / "requirements.txt"
            requirements.write_text("existing\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "scaffold_adapter.py"),
                    "https://example.com/demo.git",
                    str(output),
                    "--category",
                    "cv",
                    "--route",
                    "onnx-om",
                    "--layout",
                    "target",
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertFalse((output / "README.md").exists())
            self.assertEqual("existing\n", requirements.read_text(encoding="utf-8"))

    def test_workspace_keeps_internal_documents_private_and_existing_readme(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "workspace"
            output.mkdir()
            readme = output / "README.md"
            readme.write_text("# Existing usage\n\nKeep these instructions.\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "scaffold_adapter.py"),
                    "https://example.com/demo.git",
                    str(output),
                    "--category",
                    "cv",
                    "--route",
                    "torch-npu",
                    "--layout",
                    "workspace",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("# Existing usage\n\nKeep these instructions.\n", readme.read_text())
            for name in ("NPU_ADAPTATION.md", "ACCEPTANCE_PLAN.md"):
                self.assertTrue((output / ".ascend-adaptation/cv__demo" / name).is_file(), name)
                self.assertFalse((output / name).exists(), name)


class ProjectLogTests(unittest.TestCase):
    def run_log(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "project_log.py"), *args],
            text=True,
            capture_output=True,
        )

    def test_project_specific_log_and_status_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            common = ["--workspace", temp, "--project-id", "cv__Demo"]
            result = self.run_log(
                "init",
                *common,
                "--model-url",
                "https://example.com/demo",
                "--target-path",
                "ACL_PyTorch/built-in/cv/Demo",
                "--source-revision",
                "abc123",
                "--checkpoint",
                "not-applicable",
                "--target-repo-commit",
                "target123",
                "--target-path-exists",
                "no",
                "--route",
                "torch-npu",
                "--hardware-model",
                "Atlas 800I A2",
            )
            self.assertEqual(0, result.returncode, result.stderr)
            path = Path(temp) / ".ascend-adaptation/cv__Demo/worklog.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsNone(data["status"])
            self.assertFalse(data["target_ready"])
            second = self.run_log(
                "init",
                "--workspace",
                temp,
                "--project-id",
                "cv__Other",
                "--model-url",
                "https://example.com/other",
                "--target-path",
                "ACL_PyTorch/built-in/cv/Other",
            )
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertTrue(
                (Path(temp) / ".ascend-adaptation/cv__Other/worklog.json").exists()
            )
            blocked = self.run_log("set-status", *common, "--status", "S0")
            self.assertNotEqual(0, blocked.returncode)
            for evidence_type in ("target_baseline", "upstream_audit"):
                evidence = self.run_log(
                    "add-evidence",
                    *common,
                    "--type",
                    evidence_type,
                    "--command",
                    evidence_type,
                    "--exit-code",
                    "0",
                    "--claim",
                    f"{evidence_type} passed",
                )
                self.assertEqual(0, evidence.returncode, evidence.stderr)
            advanced = self.run_log("set-status", *common, "--status", "S0")
            self.assertEqual(0, advanced.returncode, advanced.stderr)
            frozen = self.run_log(
                "update-context", *common, "--source-revision", "different"
            )
            self.assertNotEqual(0, frozen.returncode)

            for evidence_type, status in (
                ("static_check", "S1"),
                ("functional_inference", "S2"),
            ):
                evidence = self.run_log(
                    "add-evidence",
                    *common,
                    "--type",
                    evidence_type,
                    "--command",
                    evidence_type,
                    "--exit-code",
                    "0",
                    "--claim",
                    f"{evidence_type} passed",
                )
                self.assertEqual(0, evidence.returncode, evidence.stderr)
                status_result = self.run_log("set-status", *common, "--status", status)
                self.assertEqual(0, status_result.returncode, status_result.stderr)

            for evidence_type in (
                "npu_accuracy",
                "npu_performance",
                "comparison_report",
            ):
                evidence = self.run_log(
                    "add-evidence",
                    *common,
                    "--type",
                    evidence_type,
                    "--command",
                    evidence_type,
                    "--exit-code",
                    "0",
                    "--claim",
                    f"{evidence_type} passed",
                )
                self.assertEqual(0, evidence.returncode, evidence.stderr)
            s3 = self.run_log("set-status", *common, "--status", "S3")
            # These legacy records are just labels and exit codes.
            self.assertNotEqual(0, s3.returncode)
            self.assertIn("native result", s3.stderr)
            not_ready = self.run_log("set-target-ready", *common)
            self.assertNotEqual(0, not_ready.returncode)


if __name__ == "__main__":
    unittest.main()
