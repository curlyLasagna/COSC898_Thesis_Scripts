import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replay_clean_vm.py"
SPEC = importlib.util.spec_from_file_location("replay_clean_vm", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ReplayCleanVmTests(unittest.TestCase):
    def test_eligible_trials_selects_only_locally_passing_complete_trials(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            passing = run_dir / "task_00" / "sample_00"
            passing.mkdir(parents=True)
            for name in ("flake.nix", "flake.lock"):
                (passing / name).write_text("{}", encoding="utf-8")
            (passing / "trial_meta.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
            failing = run_dir / "task_00" / "sample_01"
            failing.mkdir(parents=True)
            (failing / "trial_meta.json").write_text(json.dumps({"passed": False}), encoding="utf-8")
            summary = {"tasks": [{"task_idx": 0, "dependency_list": ["gcc"], "samples": [
                {"passed": True, "trial_dir": str(passing)},
                {"passed": False, "trial_dir": str(failing)},
            ]}]}
            (run_dir / "benchmark_summary.json").write_text(json.dumps(summary), encoding="utf-8")
            trials = MODULE.eligible_trials(run_dir)
            self.assertEqual([(trial[0], trial[1]) for trial in trials], [(0, "sample_00")])

    def test_command_generation_keeps_execution_inside_guest_trial_directory(self):
        commands = MODULE.guest_validation_commands(["python3"], ["python3 --version"], "/tmp/trial")
        self.assertEqual(commands[0][0], "flake_check")
        self.assertTrue(all("cd /tmp/trial" in command for _, command in commands))
        self.assertIn("command -v python3", commands[2][1])

    def test_classifies_the_first_failing_validation_stage(self):
        record = MODULE.CommandRecord("dependency_cmake", "", 1, 0.0, "", "")
        self.assertEqual(MODULE.classify([record]), "missing_dependency")
        record = MODULE.CommandRecord("task_00", "", 1, 0.0, "", "")
        self.assertEqual(MODULE.classify([record]), "functional_failure")


if __name__ == "__main__":
    unittest.main()
