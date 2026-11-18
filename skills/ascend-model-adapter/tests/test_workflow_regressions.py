"""User-facing CLI regressions; all models and evidence here are synthetic."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def cli(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          check=False, capture_output=True, text=True, cwd=cwd)


class WorkflowRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.common = ["--workspace", self.root, "--project-id", "fixture"]

    def log(self, action, *args):
        return cli("project_log.py", action, *self.common, *args)

    def ok(self, result):
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def init(self):
        self.ok(self.log("init", "--model-url", "local-fixture", "--target-path", "candidate",
                         "--source-revision", "revision-A", "--checkpoint", "weight-A",
                         "--target-repo-commit", "not-applicable", "--target-path-exists", "no",
                         "--route", "torch-npu", "--hardware-model", "fixture-hardware"))

    def evidence(self, kind, *extra):
        if not extra:
            trace = self.root / "fixture-log.txt"
            if not trace.exists():
                trace.write_text("synthetic observations", encoding="utf-8")
            extra = ("--log-path", trace)
        return self.log("add-evidence", "--type", kind, "--command", "fixture-only",
                        "--exit-code", "0", "--claim", "synthetic fixture", *extra)

    def prepare_s1(self):
        for status, kinds in [("S0", ["target_baseline", "upstream_audit"]),
                              ("S1", ["static_check"])]:
            for kind in kinds:
                self.ok(self.evidence(kind))
            self.ok(self.log("set-status", "--status", status))

    def test_changed_baseline_does_not_reuse_pre_freeze_evidence(self):
        self.init()
        for kind in ["target_baseline", "upstream_audit"]:
            self.ok(self.evidence(kind))
        self.ok(self.log("update-context", "--checkpoint", "weight-B"))
        self.assertNotEqual(0, self.log("set-status", "--status", "S0").returncode)
        for kind in ["target_baseline", "upstream_audit"]:
            self.ok(self.evidence(kind))
        self.ok(self.log("set-status", "--status", "S0"))
        data = json.loads(self.log("show").stdout)
        self.assertEqual(4, len(data["evidence"]), "preserve historical records")

    def test_route_change_invalidates_functional_evidence_not_static_history(self):
        self.init()
        self.prepare_s1()
        self.ok(self.evidence("functional_inference"))
        self.ok(self.log("update-context", "--route", "onnx-om"))
        self.assertNotEqual(0, self.log("set-status", "--status", "S2").returncode)
        self.ok(self.evidence("functional_inference"))
        self.ok(self.log("set-status", "--status", "S2"))

    def test_same_context_does_not_invalidate_evidence(self):
        self.init()
        self.prepare_s1()
        self.ok(self.evidence("functional_inference"))
        self.ok(self.log("update-context", "--route", "torch-npu"))
        self.ok(self.log("set-status", "--status", "S2"))

    def test_custom_internal_directory_survives_different_cwd(self):
        internal = self.root / "private records"
        self.common.extend(["--internal-dir", "private records"])
        self.init()
        self.assertTrue((internal / "worklog.json").is_file())
        self.assertFalse((self.root / ".ascend-adaptation").exists())
        result = cli("project_log.py", "show", *self.common, cwd=self.root.parent)
        self.ok(result)
        self.assertEqual("fixture", json.loads(result.stdout)["project_id"])
        other = self.log("init", "--model-url", "other", "--target-path", "candidate")
        self.assertNotEqual(0, other.returncode)

    def test_formal_stage_rejects_success_without_nonempty_observations(self):
        self.init()
        self.ok(self.log("update-context", "--patch-required"))
        empty = self.root / "empty.log"
        empty.touch()
        for status, kinds in [("S0", ["upstream_audit", "target_baseline"]),
                              ("S1", ["static_check", "patch_check"]),
                              ("S2", ["functional_inference"])]:
            for kind in kinds:
                with self.subTest(kind=kind):
                    args = ["--type", kind, "--command", "fixture", "--exit-code", 0, "--claim", "synthetic"]
                    self.ok(self.log("add-evidence", *args))
            for kind in sorted(kinds):
                self.assertIn("missing nonempty native result", self.log("set-status", "--status", status).stderr)
                self.ok(self.evidence(kind, "--log-path", empty))
                self.assertIn("missing nonempty native result", self.log("set-status", "--status", status).stderr)
                self.ok(self.evidence(kind))
            self.ok(self.log("set-status", "--status", status))

    def test_log_only_evidence_is_checked_and_cannot_be_overwritten_silently(self):
        self.init()
        for kind in ["target_baseline", "upstream_audit"]:
            self.ok(self.evidence(kind))
        self.ok(self.log("set-status", "--status", "S0"))
        log = self.root / "static.log"
        missing = self.evidence("static_check", "--log-path", log)
        self.assertNotEqual(0, missing.returncode)
        log.write_text("original fixture result")
        self.ok(self.evidence("static_check", "--log-path", log))
        log.write_text("different run")
        self.assertNotEqual(0, self.log("set-status", "--status", "S1").returncode)
        self.ok(self.evidence("static_check", "--log-path", log))
        self.ok(self.log("set-status", "--status", "S1"))

    def test_review_report_cannot_overwrite_existing_source_or_report(self):
        target = self.root / "Demo"
        target.mkdir()
        readme = target / "README.md"
        original = "# Demo\n\nExisting user instructions.\n"
        readme.write_text(original)
        for report in [readme, self.root / "previous-review.json"]:
            if report != readme:
                report.write_text("previous report")
            before = report.read_bytes()
            result = cli("modelzoo_pr_quickcheck.py", self.root, "--target", "Demo",
                         "--no-ruff", "--json-out", report)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(before, report.read_bytes())
        output = self.root / "fresh-review.json"
        self.ok(cli("modelzoo_pr_quickcheck.py", self.root, "--target", "Demo",
                    "--no-ruff", "--json-out", output))
        self.assertIsInstance(json.loads(output.read_text()), list)

    def test_resume_scaffold_with_chinese_names_and_requested_scope(self):
        ids = set()
        for name in ["模型 甲", "模型 乙"]:
            workspace = self.root / name
            result = cli("scaffold_adapter.py", f"/models/{name}.git", workspace, "--category", "视觉", "--route", "torchair", "--layout", "workspace",
                         "--image", "fixture:v1", "--hardware-model", "fixture-npu",
                         "--validation-goal", "跑通一张图片")
            self.ok(result)
            private, = (workspace / ".ascend-adaptation").iterdir()
            self.assertIn(f"Project ID: {private.name}", result.stdout)
            ids.add(private.name)
            notes = (private / "NPU_ADAPTATION.md").read_text()
            for value in ["torchair", "fixture:v1", "fixture-npu"]:
                self.assertIn(value, notes)
            plan = (private / "ACCEPTANCE_PLAN.md").read_text()
            self.assertIn("跑通一张图片", plan)
            self.assertNotIn("最低正式验收清单", plan)
            self.ok(cli("project_log.py", "init", "--workspace", workspace, "--project-id",
                        private.name, "--target-path", "candidate", "--model-url", "fixture"))
            self.assertTrue((private / "worklog.json").is_file())
        self.assertEqual(2, len(ids))

    def test_model_display_name_does_not_break_generated_python(self):
        name = 'Acme "small" 模型'
        self.ok(cli("scaffold_adapter.py", "local-model", self.root,
                    "--category", "cv", "--route", "onnx-om", "--layout", "workspace",
                    "--model-name", name, "--with-infer"))
        for script in ["infer.py", "export_onnx.py"]:
            self.ok(subprocess.run([sys.executable, str(self.root / script), "--help"],
                                   check=False, capture_output=True, text=True))

    @unittest.skipUnless(shutil.which("ruff"), "requires Ruff for a real read-only review replay")
    def test_review_remains_read_only_with_ruff_fix_enabled_in_repo(self):
        target = self.root / "Demo"
        target.mkdir()
        (target / "README.md").write_text("# Demo\n")
        (self.root / "ruff.toml").write_text('fix = true\nfix-only = true\n')
        script = target / "infer.py"
        script.write_text("import os\nprint('fixture')\n")
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob("*") if p.is_file()}
        result = cli("modelzoo_pr_quickcheck.py", self.root, "--target", "Demo", cwd=self.root)
        after = {p.relative_to(self.root): p.read_bytes()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "review must not fix files or create a cache")
        self.assertNotEqual(0, result.returncode, "lint defects must remain visible")

    def test_custom_private_directory_is_excluded_and_cannot_mix_projects(self):
        self.ok(subprocess.run(["git", "init", "-q", str(self.root)], check=False, capture_output=True, text=True))
        self.common.extend(["--internal-dir", "private records"])
        self.init()
        self.ok(subprocess.run(["git", "-C", str(self.root), "check-ignore",
                                "private records/worklog.json"], check=False, capture_output=True, text=True))
        wrong = cli("project_log.py", "show", "--workspace", self.root,
                    "--project-id", "other", "--internal-dir", "private records")
        self.assertNotEqual(0, wrong.returncode)


if __name__ == "__main__":
    unittest.main()
