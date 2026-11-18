"""Local workflow replays; synthetic records never establish NPU validation."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def cli(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, args)],
        capture_output=True, text=True,
    )


class ResumeLogScenarios(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.subject = self.root / "resolved.json"
        self.subject.write_text(json.dumps({"implementation": "fixture-A", "precision": "bf16"}))
        self.results = {}
        for kind, payload in {
            "npu_accuracy": {"scores": [1, 1]},
            "npu_performance": {"runs": [10, 11, 10], "unit": "fixtures/s"},
            "comparison_report": {"passed": True, "samples": 2},
            "extended_validation": {"extended_case": "fixture only"},
            "target_audit": {"audit": "fixture only"},
            "clean_room_replay": {"replay": "fixture only"},
        }.items():
            path = self.root / (kind + ".json")
            path.write_text(json.dumps(payload))
            self.results[kind] = path
        self.common = ["--workspace", self.root, "--project-id", "fixture"]
        result = self.log(
            "init", "--model-url", "https://example.invalid/fixture",
            "--target-path", "candidate", "--source-revision", "fixture-revision",
            "--checkpoint", "fixture-checkpoint", "--target-repo-commit", "not-applicable",
            "--target-path-exists", "no", "--route", "torch-npu",
            "--hardware-model", "synthetic-hardware-not-measured",
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def log(self, action, *args):
        return cli("project_log.py", action, *self.common, *args)

    def evidence(self, kind, code=0, artifact=None, *, subject=None, compared=None):
        extra = []
        if kind in self.results:
            extra.extend(["--subject", subject or self.subject])
            artifact = artifact or self.results[kind]
        if artifact is not None:
            extra.extend(["--artifact", artifact])
        if kind == "comparison_report":
            extra.extend(["--compared", compared or self.results["npu_accuracy"]])
        result = self.log("add-evidence", "--type", kind, "--command", "synthetic-fixture",
                          "--exit-code", code, "--claim", "test fixture only", *extra)
        self.assertEqual(0, result.returncode, result.stderr)

    def advance(self, status):
        result = self.log("set-status", "--status", status)
        self.assertEqual(0, result.returncode, result.stderr)

    def prepare(self, until):
        for status, kinds in (
            ("S0", ["target_baseline", "upstream_audit"]),
            ("S1", ["static_check"]),
            ("S2", ["functional_inference"]),
            ("S3", ["npu_accuracy", "npu_performance", "comparison_report"]),
        ):
            for kind in kinds:
                self.evidence(kind)
            self.advance(status)
            if status == until:
                break

    def test_failed_retry_blocks_old_success_and_allows_recovery(self):
        self.prepare("S2")
        for kind in ["npu_accuracy", "npu_performance", "comparison_report"]:
            self.evidence(kind)
        self.evidence("npu_accuracy", 1)
        self.assertNotEqual(0, self.log("set-status", "--status", "S3").returncode)
        self.evidence("npu_accuracy")
        self.advance("S3")
        data = json.loads((self.root / ".ascend-adaptation/fixture/worklog.json").read_text())
        self.assertIn(1, [item["exit_code"] for item in data["evidence"]])

    def test_failed_prerequisite_blocks_later_status(self):
        self.prepare("S2")
        self.evidence("static_check", 1)
        for kind in ["npu_accuracy", "npu_performance", "comparison_report"]:
            self.evidence(kind)
        self.assertNotEqual(0, self.log("set-status", "--status", "S3").returncode)

    def test_regression_clears_readiness_and_blocks_rearming(self):
        self.prepare("S3")
        for kind in ["target_audit", "clean_room_replay"]:
            self.evidence(kind)
        self.assertEqual(0, self.log("set-target-ready").returncode)
        self.evidence("npu_accuracy", 1)
        data = json.loads((self.root / ".ascend-adaptation/fixture/worklog.json").read_text())
        self.assertFalse(data["target_ready"])
        self.assertNotEqual(0, self.log("set-target-ready").returncode)

    def test_changed_or_missing_artifact_cannot_unlock_status(self):
        self.prepare("S0")
        artifact = self.root / "static-result.txt"
        artifact.write_text("original fixture")
        self.evidence("static_check", artifact=artifact)
        artifact.write_text("different fixture")
        self.assertNotEqual(0, self.log("set-status", "--status", "S1").returncode)
        artifact.unlink()
        self.assertNotEqual(0, self.log("set-status", "--status", "S1").returncode)
        artifact.write_text("original fixture")
        self.advance("S1")

    def test_qa_and_performance_must_describe_same_deployment(self):
        self.prepare("S2")
        self.evidence("npu_accuracy")
        self.evidence("comparison_report")
        other = self.root / "int8-release.json"
        other.write_text(json.dumps({"implementation": "fixture-B", "precision": "int8"}))
        fast = self.root / "int8-benchmark.json"
        fast.write_text(json.dumps({"runs": [19, 20, 21], "unit": "fixtures/s"}))
        self.evidence("npu_performance", artifact=fast, subject=other)
        rejected = self.log("set-status", "--status", "S3")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("subjects differ", rejected.stderr)
        # Register the archived run for A, leaving the measurements for B intact.
        self.evidence("npu_performance")
        self.advance("S3")
        self.assertEqual(0, self.log("show", "--verify", "--subject", self.subject).returncode)
        self.assertNotEqual(0, self.log("show", "--verify", "--subject", other).returncode)
        self.evidence("target_audit")
        self.evidence("clean_room_replay", subject=other)
        self.assertNotEqual(0, self.log("set-target-ready").returncode)
        self.evidence("clean_room_replay")
        self.assertEqual(0, self.log("set-target-ready").returncode)
        self.subject.write_text('{"implementation":"changed fixture"}')
        self.assertNotEqual(0, self.log("show", "--verify").returncode)

    def test_old_comparison_cannot_certify_new_scores(self):
        self.prepare("S3")
        updated = self.root / "scores-rerun.json"
        updated.write_text('{"scores":[1,0]}')
        self.evidence("npu_accuracy", artifact=updated)
        result = self.log("show", "--verify")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--compared", result.stderr)
        self.evidence("target_audit")
        self.evidence("clean_room_replay")
        self.assertNotEqual(0, self.log("set-target-ready").returncode)
        revised = self.root / "recomputed.json"
        revised.write_text('{"passed":true,"min_correct":1,"actual":1}')
        self.evidence("comparison_report", artifact=revised, compared=updated)
        self.assertEqual(0, self.log("set-target-ready").returncode)
        # A report on a byte-identical independent copy is valid, too.
        copied = self.root / "scores-used-by-judge.json"
        copied.write_bytes(updated.read_bytes())
        self.evidence("comparison_report", artifact=revised, compared=copied)
        self.assertEqual(0, self.log("show", "--verify").returncode)
        copied.unlink()
        self.assertNotEqual(0, self.log("show", "--verify").returncode)

    def test_historical_snapshot_readable_without_silently_endorsing_it(self):
        self.prepare("S3")
        self.evidence("target_audit")
        self.evidence("clean_room_replay")
        self.assertEqual(0, self.log("set-target-ready").returncode)
        path = self.root / ".ascend-adaptation/fixture/worklog.json"
        legacy = json.loads(path.read_bytes())
        for row in legacy["evidence"]:
            row.pop("subject", None)
            row.pop("compared", None)
            for artifact in row["artifacts"]:
                artifact.pop("role", None)
        path.write_text(json.dumps(legacy))
        original = path.read_bytes()
        self.assertTrue(json.loads(self.log("show").stdout)["target_ready"])
        self.assertNotEqual(0, self.log("show", "--verify").returncode)
        self.assertNotEqual(0, self.log("set-target-ready").returncode)
        self.assertEqual(original, path.read_bytes())
        for kind in ["npu_accuracy", "npu_performance", "comparison_report",
                     "target_audit", "clean_room_replay"]:
            self.evidence(kind)
        self.assertEqual(0, self.log("set-target-ready").returncode)
        self.assertEqual(0, self.log("show", "--verify").returncode)

    def test_native_measurements_bind_resolved_settings_not_timestamp_or_load(self):
        self.prepare("S2")
        release = {"weights": "r1", "runtime": "fixture", "dtype": "bf16", "device": "fixture"}
        qa = self.root / "eval-native.json"
        qa.write_text(json.dumps({"deployment": release, "count": 240, "timestamp": 1}))
        bench = self.root / "perf-native.json"
        other = self.root / "perf-int8.json"
        other.write_text(json.dumps({"deployment": {**release, "dtype": "int8"}, "count": 20}))
        bench.write_text(json.dumps({"count": 20, "deployment": dict(reversed(list(release.items())))}))

        def native(kind, receipt):
            return self.log("add-evidence", "--type", kind, "--command", "fixture", "--exit-code", 0,
                            "--claim", "synthetic fixture", "--artifact", self.results[kind],
                            "--subject", receipt, "--subject-fields", "deployment")

        self.assertEqual(0, native("npu_accuracy", qa).returncode)
        self.assertEqual(0, native("npu_performance", other).returncode)
        report = self.log("add-evidence", "--type", "comparison_report", "--command", "score fixture",
                          "--exit-code", 0, "--claim", "fixture", "--artifact", self.results["comparison_report"],
                          "--compared", self.results["npu_accuracy"])
        self.assertEqual(0, report.returncode, report.stderr)
        rejected = self.log("set-status", "--status", "S3")
        self.assertIn("subjects differ", rejected.stderr)
        self.assertEqual(0, native("npu_performance", bench).returncode)
        self.advance("S3")
        current = self.log("show", "--verify", "--subject", bench, "--subject-fields", "deployment")
        self.assertEqual(0, current.returncode, current.stderr)
        self.assertNotEqual(0, self.log("show", "--verify", "--subject", other,
                                       "--subject-fields", "deployment").returncode)
        # Keep original receipts intact even when the selected deployment matches.
        qa.write_text(json.dumps({"deployment": release, "count": 1, "timestamp": 1}))
        self.assertNotEqual(0, self.log("show", "--verify").returncode)

    def test_all_candidate_files_consumed_and_missing_subject_fields_rejected(self):
        self.prepare("S2")
        common = ["--command", "fixture", "--exit-code", 0, "--claim", "fixture"]
        missing = self.log("add-evidence", "--type", "npu_accuracy", *common, "--subject",
                           self.subject, "--subject-fields", "implementation", "no-such-key")
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("no-such-key", missing.stderr)
        other_score = self.root / "other-task.json"
        other_score.write_text('{"scores":[0,1]}')
        result = self.log("add-evidence", "--type", "npu_accuracy", *common, "--subject", self.subject,
                          "--artifact", self.results["npu_accuracy"], "--artifact", other_score)
        self.assertEqual(0, result.returncode, result.stderr)
        self.evidence("npu_performance")
        self.evidence("comparison_report")
        rejected = self.log("set-status", "--status", "S3")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("--compared", rejected.stderr)
        result = self.log("add-evidence", "--type", "comparison_report", *common,
                          "--artifact", self.results["comparison_report"],
                          "--compared", other_score, "--compared", self.results["npu_accuracy"])
        self.assertEqual(0, result.returncode, result.stderr)
        self.advance("S3")

    def test_native_verdict_uses_digest_at_scoring_time_after_result_path_reused(self):
        self.prepare("S2")
        scores = self.results["npu_accuracy"]
        report = self.results["comparison_report"]
        old_hash = hashlib.sha256(scores.read_bytes()).hexdigest()
        report.write_text(json.dumps({"candidate_sha256": old_hash, "passed": True}))
        # The archive now has a new prediction at the old path, but an old verdict.
        scores.write_text('{"scores":[1,0]}')
        self.evidence("npu_accuracy")
        self.evidence("npu_performance")
        common = ["--command", "score fixture", "--exit-code", 0, "--claim", "fixture",
                  "--type", "comparison_report", "--compared-field", "candidate_sha256"]
        registered = self.log("add-evidence", *common, "--artifact", report)
        self.assertEqual(0, registered.returncode, registered.stderr)
        blocked = self.log("set-status", "--status", "S3")
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("--compared-field", blocked.stderr)
        new_report = self.root / "current-verdict.json"
        native_hash = hashlib.sha256(scores.read_bytes()).hexdigest()
        new_report.write_text(json.dumps({"candidate_sha256": [native_hash], "passed": True, "min_correct": 1}))
        self.assertEqual(0, self.log("add-evidence", *common, "--artifact", new_report).returncode)
        self.advance("S3")
        new_report.write_text('{"candidate_sha256":"missing"}')
        self.assertNotEqual(0, self.log("show", "--verify").returncode)
        malformed = self.log("add-evidence", *common, "--artifact", new_report)
        self.assertNotEqual(0, malformed.returncode)
        self.assertIn("SHA256", malformed.stderr)

    def test_offline_report_distinguishes_violated_target_and_unmeasured_latency(self):
        report = self.root / "native.json"
        report.write_text('{"content_exact_rate":0.0,"sample_count":2,"mean_ms":100}')
        def check(*criteria):
            return cli("project_log.py", "check-report", report, *criteria)
        bad = check("--require", "sample_count", "eq", 3, "--require", "content_exact_rate", "eq", 1)
        self.assertEqual(1, bad.returncode)
        self.assertIn("sample_count=2", bad.stderr)
        self.assertIn("content_exact_rate=0.0", bad.stderr)
        missing = check("--require", "p95_e2e_ms", "lt", 150)
        self.assertEqual(2, missing.returncode)
        self.assertIn("p95_e2e_ms", missing.stderr)
        self.assertEqual(2, check().returncode, "scores alone have no standalone pass policy")
        for invalid in ["true", "NaN", "Infinity", '"99"']:
            report.write_text('{"p95_e2e_ms":' + invalid + '}')
            self.assertEqual(2, check("--require", "p95_e2e_ms", "lt", 150).returncode)
        report.write_text('{"p95_e2e_ms":150}')
        self.assertEqual(1, check("--require", "p95_e2e_ms", "lt", 150).returncode)
        self.assertEqual(0, check("--require", "p95_e2e_ms", "le", 150).returncode)

    def test_report_rejects_ambiguous_fields_and_preserves_decimal_boundaries(self):
        report = self.root / "native.json"
        for raw, criteria, code in [
            ('{"passed":false,"passed":true}', [], 2),
            ('{"samples":0,"samples":3}', ["samples", "eq", "3"], 2),
            ('{"passed":"false","samples":3}', ["samples", "eq", "3"], 2),
            ('{"passed":null,"samples":3}', ["samples", "eq", "3"], 2),
            ('{"rate":0.99999999999999999}', ["rate", "eq", "1"], 1),
            ('{"rate":1}', ["rate", "le", "0.99999999999999999"], 1),
            ('{"rate":1e-50}', ["rate", "eq", "10e-51"], 0),
        ]:
            with self.subTest(raw=raw, criteria=criteria):
                report.write_text(raw)
                args = ["--require", *criteria] if criteria else []
                result = cli("project_log.py", "check-report", report, *args)
                self.assertEqual(code, result.returncode, result.stderr)

    def test_ambiguous_native_report_blocks_promotion(self):
        self.prepare("S2")
        self.evidence("npu_accuracy")
        self.evidence("npu_performance")
        report = self.results["comparison_report"]
        report.write_text('{"passed":false,"passed":true}')
        self.evidence("comparison_report", artifact=report)
        result = self.log("set-status", "--status", "S3")
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("duplicate report field", result.stderr)

    def test_same_deployment_and_file_hashes_cannot_override_failed_native_verdict(self):
        self.prepare("S2")
        self.evidence("npu_accuracy")
        self.evidence("npu_performance")
        report = self.root / "native-verdict.json"
        report.write_text('{"passed":false,"score":0}')
        self.evidence("comparison_report", artifact=report)
        blocked = self.log("set-status", "--status", "S3")
        self.assertEqual(1, blocked.returncode, blocked.stderr)
        self.assertIn("passed=false", blocked.stderr)
        self.evidence("comparison_report")
        self.advance("S3")
        perf = self.root / "latencies.json"
        perf.write_text('{"p95_e2e_ms":180}')
        common = ["--type", "npu_performance", "--command", "fixture", "--exit-code", 0,
                  "--claim", "synthetic", "--subject", self.subject, "--require", "p95_e2e_ms", "lt", 150]
        self.assertEqual(0, self.log("add-evidence", *common, "--artifact", perf).returncode)
        check = self.log("show", "--verify")
        self.assertEqual(1, check.returncode)
        self.assertIn("p95_e2e_ms=180", check.stderr)
        # A mean cannot substitute for an observed percentile.
        summary = self.root / "mean-only.json"
        summary.write_text('{"mean_ms":100}')
        self.assertEqual(0, self.log("add-evidence", *common, "--artifact", summary).returncode)
        self.assertEqual(2, self.log("show", "--verify").returncode)

    def test_parallel_runs_preserve_every_observation(self):
        def record(index):
            return self.log("add-evidence", "--type", "other", "--command", "fixture",
                            "--exit-code", str(index % 2), "--claim", str(index))

        with ThreadPoolExecutor(max_workers=8) as pool:
            processes = list(pool.map(record, range(24)))
        for process in processes:
            self.assertEqual(0, process.returncode, process.stderr)
        rows = json.loads(self.log("show").stdout)["evidence"]
        self.assertEqual([(i, i % 2) for i in range(24)],
                         sorted((int(row["claim"]), row["exit_code"]) for row in rows))


class ExistingProjectScenarios(unittest.TestCase):
    def scaffold(self, root, route, *extra):
        return cli("scaffold_adapter.py", "https://example.invalid/demo", root,
                   "--category", "cv", "--route", route, "--layout", "workspace", *extra)

    def test_existing_onnx_runtime_deployment_has_a_route_without_om_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self.scaffold(root, "ort-cann")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((root / "export_onnx.py").exists())
            self.assertFalse((root / "convert_om.sh").exists())
            common = ["--workspace", root, "--project-id", "cv__demo"]
            result = cli("project_log.py", "init", *common, "--model-url", "fixture.onnx",
                         "--target-path", "candidate", "--route", "ort-cann")
            self.assertEqual(0, result.returncode, result.stderr)
            result = cli("project_log.py", "update-context", *common, "--route", "ort-cann")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("ort-cann", json.loads(cli("project_log.py", "show", *common).stdout)["route"])

    def test_offline_scaffold_starts_at_supplied_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            for source, expected in [("upstream.git", {"export_onnx.py", "convert_om.sh"}),
                                     ("frozen.onnx", {"convert_om.sh"}), ("ready.om", set())]:
                root = Path(temp) / source
                result = cli("scaffold_adapter.py", source, root, "--category", "cv",
                             "--route", "onnx-om", "--layout", "workspace")
                self.assertEqual(0, result.returncode, result.stderr)
                actual = {p.name for p in root.iterdir() if p.suffix in {".py", ".sh"}}
                self.assertEqual(expected, actual)
    def test_fill_missing_files_preserves_existing_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            existing = {"requirements.txt": "actual-business-dependency==1.0\n",
                        "README.md": "# Actual usage\n", "infer.py": "print('existing')\n"}
            for name, content in existing.items():
                (root / name).write_text(content)
            result = self.scaffold(root, "torch-npu", "--with-infer", "--missing-only")
            self.assertEqual(0, result.returncode, result.stderr)
            for name, content in existing.items():
                self.assertEqual(content, (root / name).read_text())
            self.assertTrue((root / ".ascend-adaptation/cv__demo/ACCEPTANCE_PLAN.md").is_file())
            repeated = self.scaffold(root, "torch-npu", "--with-infer", "--missing-only")
            self.assertEqual(0, repeated.returncode, repeated.stderr)

    def test_missing_only_rejects_links_before_partial_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "keep.txt"
            target.write_text("keep")
            (root / "requirements.txt").symlink_to(target)
            result = self.scaffold(root, "onnx-om", "--missing-only")
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("keep", target.read_text())
            self.assertFalse((root / "export_onnx.py").exists())
            self.assertFalse((root / ".ascend-adaptation").exists())

    def test_om_stub_does_not_require_pytorch_backend(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self.scaffold(root, "onnx-om", "--with-infer")
            self.assertEqual(0, result.returncode, result.stderr)
            # Trap accidental PyTorch backend import regardless of host packages.
            (root / "torch_npu.py").write_text("raise RuntimeError('WRONG_BACKEND_IMPORT')\n")
            run = subprocess.run([sys.executable, str(root / "infer.py"),
                                  "--model-path", "fixture.om", "--input", "fixture.bin",
                                  "--output", str(root / "outputs")], capture_output=True, text=True)
            self.assertNotEqual(0, run.returncode)
            self.assertNotIn("WRONG_BACKEND_IMPORT", run.stderr)
            self.assertIn("NotImplementedError", run.stderr)
            self.assertFalse((root / "outputs").exists())

    def test_incomplete_conversion_stops_before_environment_or_atc(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self.scaffold(root, "onnx-om")
            self.assertEqual(0, result.returncode, result.stderr)
            run = subprocess.run(["bash", str(root / "convert_om.sh"), "fixture.onnx", "fixture", "fixture-soc"],
                                 capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
            self.assertNotEqual(0, run.returncode)
            self.assertIn("INPUT_SHAPE", run.stderr)
            self.assertNotIn("set_env.sh", run.stderr)

    def test_conversion_uses_only_requested_format_and_precision_and_propagates_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(0, self.scaffold(root, "onnx-om").returncode)
            model = root / "model with spaces.onnx"
            model.write_text("not a real model")
            args_file = root / "received.json"
            runner = root / "atc"
            runner.write_text(
                f"#!{sys.executable}\nimport json, os, sys\n"
                "from pathlib import Path\n"
                "Path(os.environ['FIXTURE_ARGS']).write_text(json.dumps(sys.argv[1:]))\n"
                "raise SystemExit(17)\n"
            )
            runner.chmod(0o755)
            environment = root / "fixture env.sh"
            environment.write_text("# synthetic environment only\n")
            shape = "input_ids:1,16;attention_mask:1,16"
            for settings, optional_args in [
                ({}, []),
                ({"INPUT_FORMAT": "ND"}, ["--input_format=ND"]),
                ({"PRECISION_MODE": "origin"}, ["--precision_mode_v2=origin"]),
                ({"INPUT_FORMAT": "ND", "PRECISION_MODE": "origin"},
                 ["--input_format=ND", "--precision_mode_v2=origin"]),
            ]:
                with self.subTest(settings=settings):
                    run = subprocess.run(
                        ["bash", str(root / "convert_om.sh"), str(model), str(root / "out"), "fixture-soc"],
                        capture_output=True, text=True,
                        env={"PATH": str(root) + ":/usr/bin:/bin", "INPUT_SHAPE": shape,
                             "ASCEND_ENV_SCRIPT": str(environment), "FIXTURE_ARGS": str(args_file),
                             **settings},
                    )
                    self.assertEqual(17, run.returncode, run.stderr)
                    self.assertCountEqual(json.loads(args_file.read_text()), [
                        "--framework=5", "--model=" + str(model), "--output=" + str(root / "out"),
                        "--soc_version=fixture-soc", "--input_shape=" + shape, *optional_args,
                    ])


if __name__ == "__main__":
    unittest.main()
