#!/usr/bin/env python3
"""
Evaluates Antigravity runs using pass@k and performance metrics.
Supports:
1. Greenfield tasks from JSONL files (natural language prompts + dependency assertions)
2. Brownfield project directories with existing code (scans modules, isolates workspaces, validates flakes)
"""

import os
import sys
import csv
import json
import math
import shutil
import signal
import datetime
import argparse
import subprocess
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional

_script_dir = Path(__file__).resolve().parent
if (_script_dir / ".agents").exists():
    REPO_ROOT = _script_dir
elif (_script_dir.parent / ".agents").exists():
    REPO_ROOT = _script_dir.parent
else:
    REPO_ROOT = _script_dir

DETECT_SCRIPT = REPO_ROOT / ".agents" / "skills" / "course-flake-generator" / "scripts" / "detect-project-requirements.py"
SCRATCH_DIR = Path.home() / ".gemini" / "antigravity-cli" / "scratch"

def clean_scratch_directory():
    """Deletes the antigravity CLI scratch directory to prevent cross-trial leakage."""
    if SCRATCH_DIR.exists():
        try:
            shutil.rmtree(SCRATCH_DIR)
        except Exception as e:
            print(f"Warning: Failed to delete scratch directory {SCRATCH_DIR}: {e}", file=sys.stderr)

def compute_pass_at_k(n: int, c: int, k: int) -> float:
    """
    Unbiased estimator of pass@k from HumanEval (Chen et al. 2021).
    n: total samples generated per task
    c: number of samples that passed all checks
    k: k for pass@k (k <= n)
    """
    if n - c < k:
        return 1.0
    if c == 0:
        return 0.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)

def copy_project_isolated(src: Path, dst: Path):
    """Copies a project into an isolated directory, omitting existing flakes and VCS."""
    def ignore_patterns(folder, names):
        ignored = {
            ".git", ".devenv", ".direnv", "result", "__pycache__",
            ".ipynb_checkpoints", "flake.nix", "flake.lock", ".agents"
        }
        return {n for n in names if n in ignored or n.endswith(".pyc")}

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=ignore_patterns)

    # Initialize a clean git repository so Nix flakes can track files
    subprocess.run(["git", "init"], cwd=dst, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=dst, capture_output=True)

def link_agents_directory(target_dir: Path, provide_skill: bool = True):
    """
    Ensures .agents directory is available in the trial workspace for skill/tool discovery.
    Configures git exclude to prevent .agents from polluting the trial git index or flake checks.
    If provide_skill is False, the custom course-flake-generator skill is excluded.
    """
    agents_src = REPO_ROOT / ".agents"
    if not agents_src.exists():
        return

    git_dir = target_dir / ".git"
    if git_dir.exists():
        exclude_file = git_dir / "info" / "exclude"
        exclude_file.parent.mkdir(parents=True, exist_ok=True)
        current_content = exclude_file.read_text(encoding="utf-8") if exclude_file.exists() else ""
        if ".agents" not in current_content:
            with open(exclude_file, "a", encoding="utf-8") as f:
                f.write("\n.agents\n")

    agents_dst = target_dir / ".agents"
    if agents_dst.is_symlink() or agents_dst.exists():
        try:
            if agents_dst.is_symlink() or agents_dst.is_file():
                agents_dst.unlink()
            elif agents_dst.is_dir():
                shutil.rmtree(agents_dst)
        except Exception:
            pass

    if provide_skill:
        try:
            agents_dst.symlink_to(agents_src, target_is_directory=True)
        except OSError:
            try:
                shutil.copytree(agents_src, agents_dst)
            except Exception as e:
                print(f"Warning: Failed to link/copy .agents to {agents_dst}: {e}", file=sys.stderr)
    else:
        try:
            agents_dst.mkdir(parents=True, exist_ok=True)
            for item in agents_src.iterdir():
                if item.name == "skills":
                    skills_dst = agents_dst / "skills"
                    skills_dst.mkdir(parents=True, exist_ok=True)
                    for skill_item in item.iterdir():
                        if skill_item.name in ("course-flake-generator", "course-flake-generate"):
                            continue
                        skill_target = skills_dst / skill_item.name
                        try:
                            skill_target.symlink_to(skill_item, target_is_directory=skill_item.is_dir())
                        except OSError:
                            if skill_item.is_dir():
                                shutil.copytree(skill_item, skill_target)
                            else:
                                shutil.copy2(skill_item, skill_target)
                elif item.name != ".git":
                    dst_item = agents_dst / item.name
                    try:
                        dst_item.symlink_to(item, target_is_directory=item.is_dir())
                    except OSError:
                        if item.is_dir():
                            shutil.copytree(item, dst_item)
                        else:
                            shutil.copy2(item, dst_item)
        except Exception as e:
            print(f"Warning: Failed to setup .agents directory without skill at {agents_dst}: {e}", file=sys.stderr)

def detect_project_modules(project_path: Path) -> Dict[str, Any]:
    """Runs detect-project-requirements.py on a project directory."""
    if not DETECT_SCRIPT.exists():
        # Fallback minimal detection
        return {
            "mode": "single_project",
            "modules": [{
                "module_name": project_path.name,
                "relative_path": ".",
                "analysis": {"detected_languages": [], "candidate_packages": []}
            }]
        }
    proc = subprocess.run(
        [sys.executable, str(DETECT_SCRIPT), "--project-path", str(project_path)],
        capture_output=True,
        text=True
    )
    if proc.returncode != 0:
        return {
            "mode": "single_project",
            "modules": [{
                "module_name": project_path.name,
                "relative_path": ".",
                "analysis": {"detected_languages": [], "candidate_packages": []}
            }]
        }
    try:
        return json.loads(proc.stdout)
    except Exception:
        return {
            "mode": "single_project",
            "modules": [{
                "module_name": project_path.name,
                "relative_path": ".",
                "analysis": {"detected_languages": [], "candidate_packages": []}
            }]
        }

def find_flake_dirs(search_root: Path) -> List[Path]:
    """Finds all directories containing flake.nix within the workspace."""
    flakes = sorted(list(search_root.rglob("flake.nix")))
    dirs = []
    for f in flakes:
        if ".agents" in f.parts:
            continue
        p = f.parent
        if p not in dirs:
            dirs.append(p)
    return dirs

def verify_single_flake(flake_dir: Path, expected_tools: List[str]) -> Dict[str, Any]:
    """Tests if a single flake.nix builds and provides expected CLI tools."""
    if not shutil.which("nix"):
        return {"passed": False, "reason": "'nix' executable not found in PATH."}

    flake_file = flake_dir / "flake.nix"
    if not flake_file.exists():
        return {"passed": False, "reason": f"flake.nix not found in {flake_dir}"}

    env = os.environ.copy()
    env["NIXPKGS_ALLOW_UNFREE"] = "1"

    # Stage flake.nix if inside git repo
    subprocess.run(["git", "add", "-N", "flake.nix"], cwd=flake_dir, capture_output=True)

    # 1. nix flake check
    check_proc = subprocess.run(
        ["nix", "flake", "check", "--extra-experimental-features", "nix-command flakes"],
        cwd=flake_dir,
        env=env,
        capture_output=True,
        text=True
    )
    if check_proc.returncode != 0:
        err_msg = check_proc.stderr.strip().splitlines()
        summary_err = err_msg[-1] if err_msg else "Unknown flake check error"
        return {"passed": False, "reason": f"nix flake check failed: {summary_err}"}

    # 2. nix develop activation
    act_proc = subprocess.run(
        ["nix", "develop", "--extra-experimental-features", "nix-command flakes", "--command", "true"],
        cwd=flake_dir,
        env=env,
        capture_output=True,
        text=True
    )
    if act_proc.returncode != 0:
        err_msg = act_proc.stderr.strip().splitlines()
        summary_err = err_msg[-1] if err_msg else "Activation failed"
        return {"passed": False, "reason": f"nix develop activation failed: {summary_err}"}

    # 3. Check expected tools if provided
    missing_tools = []
    for tool in expected_tools:
        dep_proc = subprocess.run(
            [
                "nix", "develop", "--extra-experimental-features", "nix-command flakes",
                "--command", "sh", "-c", f"command -v {tool}"
            ],
            cwd=flake_dir,
            env=env,
            capture_output=True,
            text=True
        )
        if dep_proc.returncode != 0:
            missing_tools.append(tool)

    if missing_tools:
        return {
            "passed": False,
            "reason": f"Missing tools in devShell: {', '.join(missing_tools)}"
        }

    return {"passed": True, "reason": "All checks passed"}

def run_greenfield_trial(
    instruction: str,
    dependencies: List[str],
    trial_dir: Path,
    print_timeout: str = "10m0s",
    model: Optional[str] = None,
    keep_scratch: bool = False,
    provide_skill: bool = True
) -> Dict[str, Any]:
    """Executes a single trial for a greenfield natural language prompt."""
    if not keep_scratch:
        clean_scratch_directory()
    if trial_dir.exists():
        shutil.rmtree(trial_dir)
    trial_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=trial_dir, capture_output=True)
    link_agents_directory(trial_dir, provide_skill=provide_skill)

    if provide_skill:
        prompt = (
            f"/course-flake-generator Use the course-flake-generator skill to create a Nix flake "
            f"development environment in the current working directory (.): {instruction}"
        )
    else:
        prompt = (
            f"Create a Nix flake development environment in the current working directory (.): {instruction}"
        )
    cmd = [
        "agy",
        "-p", prompt,
        "--dangerously-skip-permissions",
        "--output-format", "json",
        "--print-timeout", print_timeout
    ]
    if model:
        cmd.extend(["--model", model])

    proc = subprocess.run(cmd, cwd=trial_dir, capture_output=True, text=True)
    telemetry = parse_agy_telemetry(proc.stdout)

    flake_dirs = find_flake_dirs(trial_dir)
    if not flake_dirs:
        verification = {"passed": False, "reason": "No flake.nix was generated"}
    else:
        all_passed = True
        reasons = []
        for fdir in flake_dirs:
            ver = verify_single_flake(fdir, dependencies)
            if not ver["passed"]:
                all_passed = False
                reasons.append(f"{fdir.name}: {ver['reason']}")
        verification = {
            "passed": all_passed,
            "reason": "; ".join(reasons) if reasons else "All checks passed"
        }

    usage = telemetry.get("usage", {})
    record = {
        "passed": verification["passed"],
        "reason": verification["reason"],
        "conversation_id": telemetry.get("conversation_id", "unknown"),
        "status": telemetry.get("status", "FAILED" if proc.returncode != 0 else "SUCCESS"),
        "duration_seconds": telemetry.get("duration_seconds", 0.0),
        "num_turns": telemetry.get("num_turns", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "thinking_tokens": usage.get("thinking_tokens", 0),
        "provide_skill": provide_skill,
        "trial_dir": str(trial_dir)
    }
    save_trial_artifacts(trial_dir, record["conversation_id"], telemetry, record)
    return record

def save_trial_artifacts(trial_dir: Path, cid: str, telemetry: Dict[str, Any], meta: Dict[str, Any]):
    """Saves conversation transcript, response text, and trial metadata into trial_dir."""
    try:
        (trial_dir / "trial_meta.json").write_text(json.dumps(meta, indent=2))
    except Exception:
        pass

    response_text = telemetry.get("response", "")
    if response_text:
        try:
            (trial_dir / "agent_response.md").write_text(response_text)
        except Exception:
            pass

    if cid and cid != "unknown":
        transcript_source = Path.home() / ".gemini" / "antigravity-cli" / "brain" / cid / ".system_generated" / "logs" / "transcript.jsonl"
        if transcript_source.exists():
            try:
                shutil.copy2(transcript_source, trial_dir / "transcript.jsonl")
            except Exception:
                pass

def run_brownfield_trial(
    task: Dict[str, Any],
    trial_dir: Path,
    print_timeout: str = "10m0s",
    model: Optional[str] = None,
    keep_scratch: bool = False,
    provide_skill: bool = True
) -> Dict[str, Any]:
    """Executes a single trial for an existing codebase directory."""
    if not keep_scratch:
        clean_scratch_directory()
    if trial_dir.exists():
        shutil.rmtree(trial_dir)
    trial_dir.mkdir(parents=True, exist_ok=True)
    src_dir = Path(task["project_path"])
    trial_project_dir = trial_dir / src_dir.name

    # Copy project into clean trial directory
    copy_project_isolated(src_dir, trial_project_dir)
    link_agents_directory(trial_project_dir, provide_skill=provide_skill)

    if provide_skill:
        prompt = (
            f"/course-flake-generator Use the course-flake-generator skill to generate Nix flake "
            f"development environments for the project repository at ."
        )
    else:
        prompt = (
            f"Generate Nix flake development environments for the project repository at ."
        )
    cmd = [
        "agy",
        "-p", prompt,
        "--dangerously-skip-permissions",
        "--output-format", "json",
        "--print-timeout", print_timeout
    ]
    if model:
        cmd.extend(["--model", model])

    proc = subprocess.run(cmd, cwd=trial_project_dir, capture_output=True, text=True)
    telemetry = parse_agy_telemetry(proc.stdout)

    # Verification across all expected modules
    expected_modules = task.get("modules", [])
    if not expected_modules:
        expected_modules = [{"module_name": src_dir.name, "relative_path": ".", "analysis": {}}]

    all_passed = True
    reasons = []

    for mod in expected_modules:
        rel_p = mod.get("relative_path", ".")
        mod_dir = (trial_project_dir / rel_p).resolve()
        
        # Determine language tools from analysis if available
        langs = mod.get("analysis", {}).get("detected_languages", [])
        tools = []
        if "java" in langs:
            tools.extend(["javac", "java"])
        if "python" in langs:
            tools.append("python3")
        if "rust" in langs:
            tools.append("rustc")
        if "go" in langs:
            tools.append("go")

        ver = verify_single_flake(mod_dir, tools)
        if not ver["passed"]:
            all_passed = False
            reasons.append(f"[{mod.get('module_name', rel_p)}]: {ver['reason']}")

    verification = {
        "passed": all_passed,
        "reason": "; ".join(reasons) if reasons else "All module flakes passed"
    }

    usage = telemetry.get("usage", {})
    record = {
        "passed": verification["passed"],
        "reason": verification["reason"],
        "conversation_id": telemetry.get("conversation_id", "unknown"),
        "status": telemetry.get("status", "FAILED" if proc.returncode != 0 else "SUCCESS"),
        "duration_seconds": telemetry.get("duration_seconds", 0.0),
        "num_turns": telemetry.get("num_turns", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "thinking_tokens": usage.get("thinking_tokens", 0),
        "provide_skill": provide_skill,
        "trial_dir": str(trial_project_dir)
    }
    save_trial_artifacts(trial_dir, record["conversation_id"], telemetry, record)
    return record

def parse_agy_telemetry(stdout: str) -> Dict[str, Any]:
    """Extracts telemetry JSON block from agy output."""
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {}

def discover_tasks(input_paths: List[str]) -> List[Dict[str, Any]]:
    """Resolves input paths (files or directories) into unified benchmark tasks."""
    tasks = []
    
    for raw_path in input_paths:
        p = Path(raw_path).resolve()
        if not p.exists():
            print(f"Warning: path '{raw_path}' does not exist, skipping.", file=sys.stderr)
            continue

        if p.is_file():
            # JSONL greenfield tasks
            with open(p, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    tasks.append({
                        "task_type": "greenfield",
                        "title": item.get("track", "Greenfield NL Instruction"),
                        "instruction": item.get("instruction") or item.get("instructions", ""),
                        "dependency_list": item.get("dependency_list", []),
                        "track": item.get("track", "computer science")
                    })
        elif p.is_dir():
            # If the directory contains child directories that are distinct git repos (like input/ containing AI-Assignments, etc.)
            # and p itself is not a standalone git repo or module:
            child_git_repos = [
                d for d in p.iterdir()
                if d.is_dir() and (d / ".git").exists() and d.name not in {"eval_results", "eval_test_output", "results"}
            ]

            if child_git_repos and not (p / ".git").exists():
                for sub in sorted(child_git_repos, key=lambda x: x.name):
                    analysis = detect_project_modules(sub)
                    tasks.append({
                        "task_type": "brownfield",
                        "title": sub.name,
                        "project_path": str(sub),
                        "instruction": f"Migrate project '{sub.name}' to Nix flake development environments.",
                        "mode": analysis.get("mode", "per_module"),
                        "modules": analysis.get("modules", []),
                        "track": "Brownfield Codebase"
                    })
            else:
                analysis = detect_project_modules(p)
                tasks.append({
                    "task_type": "brownfield",
                    "title": p.name,
                    "project_path": str(p),
                    "instruction": f"Migrate project '{p.name}' to Nix flake development environments.",
                    "mode": analysis.get("mode", "per_module"),
                    "modules": analysis.get("modules", []),
                    "track": "Brownfield Codebase"
                })

    return tasks

def generate_markdown_report(report_data: Dict[str, Any], output_path: Path):
    """Generates an academic-style markdown report of the benchmark."""
    status_label = report_data.get("status", "COMPLETED")
    run_args = report_data.get("run_args", {})
    command_str = run_args.get("command", "")

    lines = [
        "# Antigravity Evaluation Report (No Custom Skill)" if not run_args.get("provide_skill", True) else "# Antigravity `course-flake-generator` Evaluation Report",
        "",
        f"**Date:** {report_data.get('timestamp', 'N/A')}  ",
        f"**Status:** `{status_label}`  ",
    ]
    if command_str:
        lines.append(f"**Execution Command:** `{command_str}`  ")

    lines.extend([
        f"**Samples per Task ($n$):** {report_data.get('num_samples')}  ",
        f"**Completed Tasks:** {len(report_data.get('tasks', []))}  ",
        ""
    ])

    if run_args:
        inputs_str = ", ".join(run_args.get("inputs", []))
        lines.extend([
            "### Execution Arguments & Configuration",
            "",
            "| Parameter | Value |",
            "| :--- | :--- |",
            f"| **Inputs** | `{inputs_str}` |",
            f"| **Samples ($n$)** | `{run_args.get('num_samples')}` |",
            f"| **$k$ Values** | `{run_args.get('k_values')}` |",
            f"| **Output Directory** | `{run_args.get('output_dir')}` |",
            f"| **Run Directory** | `{run_args.get('run_dir')}` |",
            f"| **Task Filter** | `task_index={run_args.get('task_index')}, num_tasks={run_args.get('num_tasks')}, start_index={run_args.get('start_index')}` |",
            f"| **Model Override** | `{run_args.get('model') or 'None (default)'}` |",
            f"| **Print Timeout** | `{run_args.get('print_timeout')}` |",
            f"| **Keep Scratch** | `{run_args.get('keep_scratch')}` |",
            f"| **Provide Custom Skill** | `{run_args.get('provide_skill', True)}` |",
            ""
        ])

    if status_label == "INTERRUPTED":
        lines.extend([
            "> [!WARNING]",
            f"> **Benchmark run was interrupted early.** Results below reflect the {len(report_data.get('tasks', []))} task(s) completed before termination.",
            ""
        ])

    lines.extend([
        "## Overall Accuracy (pass@k)",
        "",
        "| Metric | Score |",
        "| :--- | :--- |"
    ])
    for metric, score in report_data.get("overall_scores", {}).items():
        lines.append(f"| **{metric}** | **{score * 100:.2f}%** |")

    lines.extend([
        "",
        "## Overall Performance Telemetry",
        "",
        "| Metric | Mean per Trial |",
        "| :--- | :--- |",
        f"| Duration (seconds) | {report_data.get('perf_summary', {}).get('mean_duration_s', 0.0):.2f}s |",
        f"| Agent Turns | {report_data.get('perf_summary', {}).get('mean_turns', 0.0):.1f} |",
        f"| Total Tokens | {report_data.get('perf_summary', {}).get('mean_total_tokens', 0.0):,.0f} |",
        f"| Thinking Tokens | {report_data.get('perf_summary', {}).get('mean_thinking_tokens', 0.0):,.0f} |",
        "",
        "## Task-Level Results",
        "",
        "| Task # | Type | Task / Project Name | Successes ($c/n$) | " +
        " | ".join([f"{k}" for k in report_data.get("k_values", [])]) + " |",
        "| :--- | :--- | :--- | :---: | " + " | ".join([":---:" for _ in report_data.get("k_values", [])]) + " |"
    ])

    for t in report_data.get("tasks", []):
        scores_str = " | ".join([f"{t['scores'].get(f'pass@{k}', 0.0)*100:.1f}%" for k in report_data.get("k_values", [])])
        title = t.get("title", t["instruction"][:50])
        lines.append(f"| {t['task_idx'] + 1} | {t.get('task_type')} | {title} | {t['c']}/{t['n']} | {scores_str} |")

    lines.extend([
        "",
        "## Trial Details & Conversation Links",
        "",
        "Use `agy --conversation <conversation_id>` to inspect or resume any trial.",
        "",
        "| Task | Sample | Status | Duration | Turns | Tokens | Conversation ID | Notes |",
        "| :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |"
    ])

    for t in report_data.get("tasks", []):
        for s_idx, s in enumerate(t.get("samples", [])):
            status = "✅ PASS" if s["passed"] else "❌ FAIL"
            cid = s.get("conversation_id", "unknown")
            reason = s.get("reason", "").replace("|", "\\|")
            lines.append(
                f"| {t['task_idx'] + 1} | {s_idx + 1} | {status} | {s['duration_seconds']:.1f}s | "
                f"{s['num_turns']} | {s['total_tokens']:,} | `{cid}` | {reason} |"
            )

    output_path.write_text("\n".join(lines) + "\n")

def clean_arg(val):
    if not isinstance(val, str):
        return val
    try:
        parsed = json.loads(val)
        if isinstance(parsed, str):
            return parsed
    except Exception:
        pass
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    return val

def extract_base_command(cmd_str):
    cmd = cmd_str.strip()
    if not cmd:
        return "empty"
    parts = cmd.split()
    idx = 0
    while idx < len(parts) and "=" in parts[idx] and not parts[idx].startswith("-"):
        idx += 1
    if idx < len(parts):
        token = parts[idx].strip(";\"'")
        if token == "env" and idx + 1 < len(parts):
            idx += 1
            while idx < len(parts) and "=" in parts[idx]:
                idx += 1
            if idx < len(parts):
                token = parts[idx].strip(";\"'")
        if "/" in token:
            token = token.rstrip("/").split("/")[-1]
        return token
    return parts[0]

def generate_tool_call_reports(target_dir: Path):
    """Generates tool call frequency CSV summaries for a run directory."""
    transcript_files = sorted(target_dir.glob("task_*/sample_*/transcript.jsonl"))
    if not transcript_files:
        return

    total_tool_counts = Counter()
    trial_data = []
    trials_using_tool = defaultdict(set)
    all_tools = set()

    for tf in transcript_files:
        task = tf.parent.parent.name
        sample = tf.parent.name
        trial_id = f"{task}/{sample}"

        meta_file = tf.parent / "trial_meta.json"
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
            except Exception:
                pass

        trial_tool_counts = Counter()
        with open(tf, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                for tc in data.get("tool_calls", []):
                    tname = tc.get("name")
                    if tname:
                        trial_tool_counts[tname] += 1
                        total_tool_counts[tname] += 1
                        trials_using_tool[tname].add(trial_id)
                        all_tools.add(tname)

        trial_data.append({
            "task": task,
            "sample": sample,
            "passed": meta.get("passed", ""),
            "duration_seconds": round(meta.get("duration_seconds", 0), 2) if meta.get("duration_seconds") is not None else "",
            "total_calls": sum(trial_tool_counts.values()),
            "tool_counts": trial_tool_counts
        })

    sorted_tools = [tool for tool, _ in total_tool_counts.most_common()]
    total_calls_all = sum(total_tool_counts.values())
    num_trials = len(transcript_files)

    summary_csv = target_dir / "tool_call_frequency.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "tool_name",
            "call_count",
            "percentage_of_total",
            "trials_using_tool",
            "trial_prevalence_pct",
            "mean_calls_per_trial"
        ])
        for tool in sorted_tools:
            count = total_tool_counts[tool]
            pct = (count / total_calls_all) * 100 if total_calls_all > 0 else 0
            trials_cnt = len(trials_using_tool[tool])
            trial_pct = (trials_cnt / num_trials) * 100 if num_trials > 0 else 0
            mean_per_trial = count / num_trials if num_trials > 0 else 0
            writer.writerow([
                tool,
                count,
                f"{pct:.2f}%",
                trials_cnt,
                f"{trial_pct:.2f}%",
                f"{mean_per_trial:.2f}"
            ])
        writer.writerow([
            "TOTAL",
            total_calls_all,
            "100.00%",
            num_trials,
            "100.00%",
            f"{(total_calls_all / num_trials):.2f}" if num_trials else "0.00"
        ])

    by_trial_csv = target_dir / "tool_call_frequency_by_trial.csv"
    with open(by_trial_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["task", "sample", "passed", "duration_seconds", "total_tool_calls"] + sorted_tools
        writer.writerow(header)
        for td in trial_data:
            row = [
                td["task"],
                td["sample"],
                td["passed"],
                td["duration_seconds"],
                td["total_calls"]
            ] + [td["tool_counts"].get(tool, 0) for tool in sorted_tools]
            writer.writerow(row)

    task_counts = defaultdict(lambda: Counter())
    task_totals = Counter()
    for td in trial_data:
        task = td["task"]
        for tool, cnt in td["tool_counts"].items():
            task_counts[task][tool] += cnt
            task_totals[task] += cnt

    by_task_csv = target_dir / "tool_call_frequency_by_task.csv"
    with open(by_task_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["task", "total_tool_calls"] + sorted_tools
        writer.writerow(header)
        for task in sorted(task_counts.keys()):
            row = [task, task_totals[task]] + [task_counts[task].get(tool, 0) for tool in sorted_tools]
            writer.writerow(row)

def generate_run_command_reports(target_dir: Path):
    """Generates run_command frequency and sequential log CSV reports for a run directory."""
    transcript_files = sorted(target_dir.glob("task_*/sample_*/transcript.jsonl"))
    if not transcript_files:
        return

    all_commands = []
    cmd_frequency = Counter()
    cmd_trials = defaultdict(set)
    base_cmd_frequency = Counter()
    base_cmd_trials = defaultdict(set)

    for tf in transcript_files:
        task = tf.parent.parent.name
        sample = tf.parent.name
        trial_id = f"{task}/{sample}"

        with open(tf, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                step_idx = data.get("step_index", "")
                created_at = data.get("created_at", "")
                for tc in data.get("tool_calls", []):
                    if tc.get("name") == "run_command":
                        args = tc.get("args", {})
                        cmd = clean_arg(args.get("CommandLine", ""))
                        cwd = clean_arg(args.get("Cwd", ""))
                        action = clean_arg(args.get("toolAction", ""))
                        summary = clean_arg(args.get("toolSummary", ""))
                        base_cmd = extract_base_command(cmd)

                        cmd_frequency[cmd] += 1
                        cmd_trials[cmd].add(trial_id)
                        base_cmd_frequency[base_cmd] += 1
                        base_cmd_trials[base_cmd].add(trial_id)

                        all_commands.append({
                            "task": task,
                            "sample": sample,
                            "step_index": step_idx,
                            "created_at": created_at,
                            "cwd": cwd,
                            "base_command": base_cmd,
                            "command": cmd,
                            "tool_action": action,
                            "tool_summary": summary
                        })

    total_rc = len(all_commands)
    total_trials = len(transcript_files)

    exact_csv = target_dir / "run_command_frequency.csv"
    with open(exact_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "command",
            "base_command",
            "execution_count",
            "percentage_of_all_run_command",
            "unique_trials_used",
            "trial_prevalence_pct"
        ])
        for cmd, count in cmd_frequency.most_common():
            pct = (count / total_rc) * 100 if total_rc > 0 else 0
            trials_cnt = len(cmd_trials[cmd])
            trial_pct = (trials_cnt / total_trials) * 100 if total_trials > 0 else 0
            writer.writerow([
                cmd,
                extract_base_command(cmd),
                count,
                f"{pct:.2f}%",
                trials_cnt,
                f"{trial_pct:.2f}%"
            ])

    base_csv = target_dir / "run_command_base_frequency.csv"
    with open(base_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "base_command",
            "execution_count",
            "percentage_of_all_run_command",
            "unique_trials_used",
            "trial_prevalence_pct"
        ])
        for base, count in base_cmd_frequency.most_common():
            pct = (count / total_rc) * 100 if total_rc > 0 else 0
            trials_cnt = len(base_cmd_trials[base])
            trial_pct = (trials_cnt / total_trials) * 100 if total_trials > 0 else 0
            writer.writerow([
                base,
                count,
                f"{pct:.2f}%",
                trials_cnt,
                f"{trial_pct:.2f}%"
            ])
        writer.writerow([
            "TOTAL",
            total_rc,
            "100.00%",
            len({t for ts in base_cmd_trials.values() for t in ts}),
            f"{(len({t for ts in base_cmd_trials.values() for t in ts}) / total_trials) * 100:.2f}%" if total_trials else "0.00%"
        ])

    log_csv = target_dir / "run_command_log.csv"
    with open(log_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "task",
            "sample",
            "step_index",
            "created_at",
            "cwd",
            "base_command",
            "command",
            "tool_action",
            "tool_summary"
        ])
        for entry in all_commands:
            writer.writerow([
                entry["task"],
                entry["sample"],
                entry["step_index"],
                entry["created_at"],
                entry["cwd"],
                entry["base_command"],
                entry["command"],
                entry["tool_action"],
                entry["tool_summary"]
            ])

def generate_mcp_tool_reports(target_dir: Path):
    """Generates call_mcp_tool query frequency and invocation log CSV reports for a run directory."""
    transcript_files = sorted(target_dir.glob("task_*/sample_*/transcript.jsonl"))
    if not transcript_files:
        return

    all_mcp_calls = []
    query_frequency = Counter()
    query_trials = defaultdict(set)

    for tf in transcript_files:
        task = tf.parent.parent.name
        sample = tf.parent.name
        trial_id = f"{task}/{sample}"

        with open(tf, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                step_idx = data.get("step_index", "")
                created_at = data.get("created_at", "")
                for tc in data.get("tool_calls", []):
                    if tc.get("name") == "call_mcp_tool":
                        raw_args = tc.get("args", {})
                        server = clean_arg(raw_args.get("ServerName", ""))
                        tool = clean_arg(raw_args.get("ToolName", ""))
                        action_desc = clean_arg(raw_args.get("toolAction", ""))
                        summary_desc = clean_arg(raw_args.get("toolSummary", ""))

                        inner_args = raw_args.get("Arguments", {})
                        if isinstance(inner_args, str):
                            try:
                                inner_args = json.loads(inner_args)
                            except Exception:
                                inner_args = {"raw": inner_args}
                        if not isinstance(inner_args, dict):
                            inner_args = {"raw": str(inner_args)}

                        mcp_action = inner_args.get("action", "")
                        mcp_query = inner_args.get("query", "")
                        mcp_type = inner_args.get("type", "")
                        mcp_channel = inner_args.get("channel", "")
                        mcp_limit = inner_args.get("limit", "")

                        query_key = (mcp_action, mcp_query, mcp_type)
                        query_frequency[query_key] += 1
                        query_trials[query_key].add(trial_id)

                        all_mcp_calls.append({
                            "task": task,
                            "sample": sample,
                            "step_index": step_idx,
                            "created_at": created_at,
                            "server_name": server,
                            "mcp_tool": tool,
                            "action": mcp_action,
                            "query": mcp_query,
                            "type": mcp_type,
                            "channel": mcp_channel,
                            "limit": mcp_limit,
                            "tool_action": action_desc,
                            "tool_summary": summary_desc,
                            "arguments_json": json.dumps(inner_args, sort_keys=True),
                        })

    total_mcp = len(all_mcp_calls)
    total_trials = len(transcript_files)
    if total_mcp == 0:
        return

    sample_args = {}
    for entry in all_mcp_calls:
        key = (entry["action"], entry["query"], entry["type"])
        if key not in sample_args:
            sample_args[key] = entry["arguments_json"]

    freq_csv = target_dir / "mcp_tool_frequency.csv"
    with open(freq_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "action",
            "query",
            "type",
            "call_count",
            "percentage_of_all_mcp_calls",
            "unique_trials_used",
            "trial_prevalence_pct",
            "sample_arguments"
        ])
        for (action, query, qtype), count in query_frequency.most_common():
            pct = (count / total_mcp) * 100 if total_mcp > 0 else 0
            trials_cnt = len(query_trials[(action, query, qtype)])
            trial_pct = (trials_cnt / total_trials) * 100 if total_trials > 0 else 0
            writer.writerow([
                action,
                query,
                qtype,
                count,
                f"{pct:.2f}%",
                trials_cnt,
                f"{trial_pct:.2f}%",
                sample_args.get((action, query, qtype), "")
            ])

    log_csv = target_dir / "mcp_tool_log.csv"
    with open(log_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "task",
            "sample",
            "step_index",
            "created_at",
            "server_name",
            "mcp_tool",
            "action",
            "query",
            "type",
            "channel",
            "limit",
            "tool_action",
            "tool_summary",
            "arguments_json"
        ])
        for entry in all_mcp_calls:
            writer.writerow([
                entry["task"],
                entry["sample"],
                entry["step_index"],
                entry["created_at"],
                entry["server_name"],
                entry["mcp_tool"],
                entry["action"],
                entry["query"],
                entry["type"],
                entry["channel"],
                entry["limit"],
                entry["tool_action"],
                entry["tool_summary"],
                entry["arguments_json"]
            ])

def save_reports(
    eval_dir: Path,
    run_dir: Path,
    task_results: List[Dict[str, Any]],
    num_samples: int,
    k_values: List[int],
    total_durations: List[float],
    total_turns: List[int],
    total_tokens_list: List[int],
    thinking_tokens_list: List[int],
    is_interrupted: bool = False,
    run_timestamp: Optional[str] = None,
    run_iso_timestamp: Optional[str] = None,
    run_args: Optional[Dict[str, Any]] = None,
):
    """Flushes benchmark summaries, markdown reports, and statistics CSVs to disk."""
    if not task_results:
        return

    overall_scores = {}
    for k in k_values:
        if k <= num_samples:
            mean_score = sum(t["scores"][f"pass@{k}"] for t in task_results) / len(task_results)
            overall_scores[f"pass@{k}"] = mean_score

    num_total_trials = len(total_durations)
    perf_summary = {
        "mean_duration_s": (sum(total_durations) / num_total_trials) if num_total_trials else 0,
        "mean_turns": (sum(total_turns) / num_total_trials) if num_total_trials else 0,
        "mean_total_tokens": (sum(total_tokens_list) / num_total_trials) if num_total_trials else 0,
        "mean_thinking_tokens": (sum(thinking_tokens_list) / num_total_trials) if num_total_trials else 0,
    }

    report_data = {
        "timestamp": run_iso_timestamp or datetime.datetime.now().isoformat(),
        "run_id": run_timestamp or datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "status": "INTERRUPTED" if is_interrupted else "COMPLETED",
        "run_args": run_args or {},
        "num_samples": num_samples,
        "k_values": k_values,
        "overall_scores": overall_scores,
        "perf_summary": perf_summary,
        "tasks": task_results
    }

    # 1. Primary: Save benchmark summary and report directly inside run_dir
    run_json_path = run_dir / "benchmark_summary.json"
    with open(run_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    run_md_path = run_dir / "benchmark_report.md"
    generate_markdown_report(report_data, run_md_path)

    # 2. Generate tool call frequency and run command frequency statistics inside run_dir
    try:
        generate_tool_call_reports(run_dir)
    except Exception as e:
        print(f"Warning: Failed to generate tool call reports: {e}", file=sys.stderr)

    try:
        generate_run_command_reports(run_dir)
    except Exception as e:
        print(f"Warning: Failed to generate run command reports: {e}", file=sys.stderr)

    try:
        generate_mcp_tool_reports(run_dir)
    except Exception as e:
        print(f"Warning: Failed to generate MCP tool reports: {e}", file=sys.stderr)

    # 3. Update top-level latest pointer and convenience copies in eval_dir
    try:
        latest_link = eval_dir / "latest"
        if latest_link.is_symlink() or latest_link.is_file():
            latest_link.unlink()
        elif latest_link.is_dir():
            shutil.rmtree(latest_link)
        latest_link.symlink_to(run_dir.name, target_is_directory=True)
    except Exception:
        pass

    try:
        shutil.copy2(run_json_path, eval_dir / "benchmark_summary.json")
        shutil.copy2(run_md_path, eval_dir / "benchmark_report.md")
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Evaluate pass@k for course-flake-generator")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=["input/nl_instruction_inputs.jsonl"],
        help="One or more input files (.jsonl) or project directories with existing code"
    )
    parser.add_argument("-n", "--num-samples", type=int, default=3, help="Number of samples per problem (n)")
    parser.add_argument("-k", "--k-values", nargs="+", type=int, default=[1, 3], help="Values of k for pass@k")
    parser.add_argument("--output-dir", default="eval_results", help="Directory for trial workspaces and results")
    parser.add_argument(
        "-i", "--task-index", "--index",
        type=int,
        default=None,
        help="Run only a specific 0-based task index (e.g., 0 for the first task)"
    )
    parser.add_argument(
        "-m", "--num-tasks", "--limit", "--max-tasks",
        type=int,
        default=None,
        help="Maximum number of tasks to run from the input file/directories"
    )
    parser.add_argument(
        "--start-index", "--offset",
        type=int,
        default=0,
        help="Starting 0-based task index when running tasks (default: 0)"
    )
    parser.add_argument("--print-timeout", default="15m0s", help="Timeout passed to agy -p (default 15m0s)")
    parser.add_argument("--model", default=None, help="Model override for agy")
    parser.add_argument(
        "--keep-scratch",
        action="store_true",
        help="Do not delete the ~/.gemini/antigravity-cli/scratch directory before trials"
    )
    parser.add_argument(
        "--no-skill", "--without-skill", "--no-custom-skill", "--without-custom-skill", "--disable-skill",
        dest="no_skill",
        action="store_true",
        default=False,
        help="Do not provide the custom course-flake-generator skill to the agent"
    )
    parser.add_argument(
        "--with-skill",
        dest="no_skill",
        action="store_false",
        help="Provide the custom course-flake-generator skill to the agent (default: True)"
    )
    args = parser.parse_args()

    eval_dir = Path(args.output_dir).resolve()
    eval_dir.mkdir(parents=True, exist_ok=True)

    if not args.keep_scratch:
        clean_scratch_directory()

    tasks = discover_tasks(args.inputs)
    if not tasks:
        print("Error: No tasks discovered from the provided --inputs.", file=sys.stderr)
        sys.exit(1)

    if args.task_index is not None and args.num_tasks is not None:
        print("Error: Cannot specify both --task-index and --num-tasks simultaneously.", file=sys.stderr)
        sys.exit(1)

    if args.task_index is not None:
        if args.task_index < 0 or args.task_index >= len(tasks):
            print(f"Error: --task-index {args.task_index} out of range [0, {len(tasks)-1}]. Total available tasks: {len(tasks)}", file=sys.stderr)
            sys.exit(1)
        tasks_to_run = [(args.task_index, tasks[args.task_index])]
    else:
        if args.start_index < 0 or args.start_index >= len(tasks):
            print(f"Error: --start-index {args.start_index} out of range [0, {len(tasks)-1}]. Total available tasks: {len(tasks)}", file=sys.stderr)
            sys.exit(1)
        if args.num_tasks is not None:
            if args.num_tasks <= 0:
                print(f"Error: --num-tasks must be a positive integer (got {args.num_tasks}).", file=sys.stderr)
                sys.exit(1)
            end_index = min(args.start_index + args.num_tasks, len(tasks))
        else:
            end_index = len(tasks)
        tasks_to_run = list(enumerate(tasks))[args.start_index:end_index]

    now = datetime.datetime.now()
    run_timestamp = now.strftime("%Y%m%d_%H%M%S")
    run_iso_timestamp = now.isoformat()

    eval_dir = Path(args.output_dir).resolve()
    eval_dir.mkdir(parents=True, exist_ok=True)

    run_dir = eval_dir / run_timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    command_str = f"python3 {Path(sys.argv[0]).name} " + " ".join(sys.argv[1:]) if sys.argv[1:] else f"python3 {Path(sys.argv[0]).name}"
    run_args = {
        "command": command_str,
        "raw_args": sys.argv[1:],
        "inputs": args.inputs,
        "num_samples": args.num_samples,
        "k_values": args.k_values,
        "output_dir": str(eval_dir),
        "run_dir": str(run_dir),
        "task_index": args.task_index,
        "num_tasks": args.num_tasks,
        "start_index": args.start_index,
        "print_timeout": args.print_timeout,
        "model": args.model,
        "keep_scratch": args.keep_scratch,
        "provide_skill": not args.no_skill
    }

    print("=" * 75)
    print("ANTIGRAVITY pass@k BENCHMARK RUNNER")
    print(f"Run Timestamp: {run_timestamp} ({run_iso_timestamp})")
    print(f"Tasks to Run: {len(tasks_to_run)} (of {len(tasks)} total) | Samples per task (n): {args.num_samples} | k: {args.k_values}")
    if args.task_index is not None:
        print(f"Target Task Index: {args.task_index} (0-based)")
    elif args.num_tasks is not None or args.start_index > 0:
        print(f"Task Range: indices {args.start_index} to {args.start_index + len(tasks_to_run) - 1} (0-based)")
    print(f"Provide Custom Skill: {not args.no_skill}")
    print(f"Run Directory: {run_dir}")
    print("=" * 75)

    task_results = []
    total_durations = []
    total_turns = []
    total_tokens_list = []
    thinking_tokens_list = []

    def flush_progress(interrupted: bool = False):
        save_reports(
            eval_dir=eval_dir,
            run_dir=run_dir,
            task_results=task_results,
            num_samples=args.num_samples,
            k_values=args.k_values,
            total_durations=total_durations,
            total_turns=total_turns,
            total_tokens_list=total_tokens_list,
            thinking_tokens_list=thinking_tokens_list,
            is_interrupted=interrupted,
            run_timestamp=run_timestamp,
            run_iso_timestamp=run_iso_timestamp,
            run_args=run_args
        )

    def sig_handler(signum, frame):
        print(f"\n\n⚠️ Process caught signal {signum}. Generating report before exit...")
        flush_progress(interrupted=True)
        print(f"Partial results successfully saved to: {run_dir / 'benchmark_report.md'}")
        sys.exit(130 if signum == signal.SIGINT else 143)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        for task_idx, task in tasks_to_run:
            ttype = task.get("task_type", "greenfield")
            title = task.get("title", f"Task {task_idx+1}")
            
            print(f"\n[Task {task_idx + 1}/{len(tasks)}] [{ttype.upper()}] {title}")
            if ttype == "brownfield":
                print(f"Project Path: {task['project_path']}")
                print(f"Detected Modules: {len(task.get('modules', []))} ({', '.join(m.get('module_name', '.') for m in task.get('modules', [])[:5])})")
            else:
                print(f"Prompt: {task['instruction'][:90]}...")
                print(f"Expected Dependencies: {task.get('dependency_list', [])}")

            samples = []
            c = 0

            for sample_idx in range(args.num_samples):
                trial_dir = run_dir / f"task_{task_idx:02d}" / f"sample_{sample_idx:02d}"
                print(f"  -> Sample {sample_idx + 1}/{args.num_samples}... ", end="", flush=True)

                if ttype == "brownfield":
                    res = run_brownfield_trial(
                        task=task,
                        trial_dir=trial_dir,
                        print_timeout=args.print_timeout,
                        model=args.model,
                        keep_scratch=args.keep_scratch,
                        provide_skill=not args.no_skill
                    )
                else:
                    res = run_greenfield_trial(
                        instruction=task["instruction"],
                        dependencies=task.get("dependency_list", []),
                        trial_dir=trial_dir,
                        print_timeout=args.print_timeout,
                        model=args.model,
                        keep_scratch=args.keep_scratch,
                        provide_skill=not args.no_skill
                    )

                samples.append(res)
                status_tag = "PASS" if res["passed"] else f"FAIL ({res['reason']})"
                print(f"[{status_tag}] | {res['duration_seconds']:.1f}s | {res['total_tokens']:,} tokens | cid: {res['conversation_id']}")

                if res["passed"]:
                    c += 1

                total_durations.append(res["duration_seconds"])
                total_turns.append(res["num_turns"])
                total_tokens_list.append(res["total_tokens"])
                thinking_tokens_list.append(res["thinking_tokens"])

            task_scores = {
                f"pass@{k}": compute_pass_at_k(args.num_samples, c, k)
                for k in args.k_values if k <= args.num_samples
            }

            task_record = dict(task)
            task_record.update({
                "task_idx": task_idx,
                "n": args.num_samples,
                "c": c,
                "scores": task_scores,
                "samples": samples
            })
            task_results.append(task_record)

            # Auto-save after every task so progress is never lost if stopped later
            flush_progress(interrupted=False)

    except (KeyboardInterrupt, SystemExit):
        flush_progress(interrupted=True)
        raise
    finally:
        is_partial = len(task_results) < len(tasks_to_run)
        flush_progress(interrupted=is_partial)

    # Print summary to console
    print("\n" + "=" * 75)
    print("BENCHMARK SUMMARY")
    print("=" * 75)
    overall_scores = {}
    for k in args.k_values:
        if k <= args.num_samples and task_results:
            mean_score = sum(t["scores"][f"pass@{k}"] for t in task_results) / len(task_results)
            overall_scores[f"pass@{k}"] = mean_score
            print(f"  {f'pass@{k}':<10}: {mean_score * 100:.2f}%")

    num_total_trials = len(total_durations)
    if num_total_trials > 0:
        avg_dur = sum(total_durations) / num_total_trials
        avg_tok = sum(total_tokens_list) / num_total_trials
        print(f"  Avg Duration: {avg_dur:.1f}s")
        print(f"  Avg Tokens  : {avg_tok:,.0f}")

    print(f"\nTimestamped run directory created at:")
    print(f"  - {run_dir}")
    print(f"Artifacts and statistics stored inside:")
    print(f"  - Tasks & Samples: {run_dir}/task_XX/sample_YY")
    print(f"  - Summary JSON   : {run_dir / 'benchmark_summary.json'}")
    print(f"  - Markdown Report: {run_dir / 'benchmark_report.md'}")
    print(f"  - Tool Telemetry : {run_dir / 'tool_call_frequency.csv'}")
    print(f"  - Command Log    : {run_dir / 'run_command_log.csv'}")
    print(f"Latest links updated at:")
    print(f"  - {eval_dir / 'latest'} -> {run_timestamp}")
    print(f"  - {eval_dir / 'benchmark_summary.json'}")
    print(f"  - {eval_dir / 'benchmark_report.md'}")
    print("=" * 75)

if __name__ == "__main__":
    main()
