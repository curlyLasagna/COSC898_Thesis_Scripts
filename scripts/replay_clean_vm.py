#!/usr/bin/env python3
"""Replay locally successful flake trials in a snapshot-restored NixOS Lima VM.

The script intentionally never edits the source evaluation run.  It copies each
trial into guest-local /tmp storage, restores a baseline snapshot before every
trial, and writes a separate host-side result tree.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = REPO_ROOT / "vm" / "nixos-clean-eval.yaml"
DEFAULT_MANIFEST = REPO_ROOT / "config" / "clean_vm_tasks.json"
SNAPSHOT_TAG = "clean-baseline"
GUEST_ROOT = "/tmp/thesis-clean-eval"
EXCLUDED_NAMES = {".git", ".agents", ".venv", "venv", "result", "result-*", "__pycache__", ".clean-vm-build"}


class ReplayError(RuntimeError):
    pass


@dataclass
class CommandRecord:
    stage: str
    command: str
    returncode: int | None
    duration_seconds: float
    stdout_log: str
    stderr_log: str
    timed_out: bool = False


def run_command(command: list[str], *, timeout: int | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError as error:
        raise ReplayError(f"Required executable not found: {command[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise ReplayError(f"Command timed out after {timeout}s: {' '.join(command)}") from error


def lima(instance: str, *args: str, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return run_command(["limactl", *args], timeout=timeout)


def shell(instance: str, command: str, *, timeout: int) -> subprocess.CompletedProcess[str]:
    return lima(instance, "shell", instance, "--", "sh", "-lc", command, timeout=timeout)


def require_success(proc: subprocess.CompletedProcess[str], action: str) -> None:
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "no output"
        raise ReplayError(f"{action} failed: {detail}")


def preflight(instance: str, require_snapshot: bool) -> dict[str, str]:
    if not shutil.which("limactl"):
        raise ReplayError("limactl is not installed or not on PATH. Install Lima before preparing or replaying trials.")
    version = run_command(["limactl", "--version"])
    require_success(version, "Reading Lima version")
    guest = shell(instance, "nix --version && nix eval --impure --raw --expr builtins.currentSystem", timeout=60)
    require_success(guest, f"Checking Nix in guest '{instance}'")
    snapshot = lima(instance, "snapshot", "list", instance)
    require_success(snapshot, "Listing guest snapshots")
    if require_snapshot and SNAPSHOT_TAG not in snapshot.stdout:
        raise ReplayError(f"Snapshot '{SNAPSHOT_TAG}' is missing for instance '{instance}'. Run the prepare command first.")
    lines = [line.strip() for line in guest.stdout.splitlines() if line.strip()]
    return {"lima_version": version.stdout.strip(), "nix_version": lines[0] if lines else "unknown", "guest_system": lines[-1] if lines else "unknown"}


def wait_for_guest(instance: str, timeout: int = 120) -> None:
    deadline = time.monotonic() + timeout
    last_error = "guest did not answer"
    while time.monotonic() < deadline:
        try:
            proc = shell(instance, "nix --version", timeout=20)
            if proc.returncode == 0:
                return
            last_error = proc.stderr.strip() or proc.stdout.strip() or last_error
        except ReplayError as error:
            last_error = str(error)
        time.sleep(2)
    raise ReplayError(f"Guest '{instance}' did not become ready within {timeout}s: {last_error}")


def prepare(instance: str, template: Path) -> None:
    if not template.is_file():
        raise ReplayError(f"Lima template does not exist: {template}")
    if not shutil.which("limactl"):
        raise ReplayError("limactl is not installed or not on PATH. Install Lima before preparing a guest.")
    listed = lima(instance, "list", "--format", "{{.Name}}")
    require_success(listed, "Listing Lima instances")
    if instance not in listed.stdout.split():
        require_success(lima(instance, "create", "--name", instance, str(template)), "Creating clean evaluation guest")
    require_success(lima(instance, "start", instance), "Starting clean evaluation guest")
    wait_for_guest(instance)
    baseline = shell(instance, "test ! -d /tmp/thesis-clean-eval && nix --version", timeout=60)
    require_success(baseline, "Verifying clean guest baseline")
    snapshots = lima(instance, "snapshot", "list", instance)
    require_success(snapshots, "Listing guest snapshots")
    if SNAPSHOT_TAG not in snapshots.stdout:
        require_success(lima(instance, "snapshot", "create", instance, "--tag", SNAPSHOT_TAG), "Creating clean baseline snapshot")
    print(f"Prepared Lima instance '{instance}' with snapshot '{SNAPSHOT_TAG}'.")


def eligible_trials(source_run: Path) -> list[tuple[int, str, Path, dict[str, Any]]]:
    summary_path = source_run / "benchmark_summary.json"
    if not summary_path.is_file():
        raise ReplayError(f"Source run is missing benchmark_summary.json: {source_run}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    trials: list[tuple[int, str, Path, dict[str, Any]]] = []
    for task in summary.get("tasks", []):
        task_idx = task.get("task_idx")
        for sample_idx, sample in enumerate(task.get("samples", [])):
            if not sample.get("passed"):
                continue
            trial_dir = Path(sample["trial_dir"])
            if not trial_dir.is_absolute():
                trial_dir = source_run / trial_dir
            meta_path = trial_dir / "trial_meta.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if not meta.get("passed") or not (trial_dir / "flake.nix").is_file() or not (trial_dir / "flake.lock").is_file():
                continue
            trials.append((int(task_idx), f"sample_{sample_idx:02d}", trial_dir, {**task, "source_sample": sample, "trial_meta": meta}))
    return trials


def ignored(path: Path) -> bool:
    return any(part in EXCLUDED_NAMES or part.startswith("result-") for part in path.parts)


def archive_trial(trial_dir: Path, destination: Path) -> None:
    with tarfile.open(destination, "w:gz", dereference=False) as archive:
        for item in trial_dir.rglob("*"):
            relative = item.relative_to(trial_dir)
            if ignored(relative):
                continue
            archive.add(item, arcname=relative, recursive=False)


def write_process_logs(trial_output: Path, record_index: int, stage: str, proc: subprocess.CompletedProcess[str], started: float) -> CommandRecord:
    safe_stage = stage.replace("/", "_").replace(" ", "_")
    stdout_path = trial_output / f"{record_index:02d}_{safe_stage}.stdout.log"
    stderr_path = trial_output / f"{record_index:02d}_{safe_stage}.stderr.log"
    stdout_path.write_text(proc.stdout or "", encoding="utf-8")
    stderr_path.write_text(proc.stderr or "", encoding="utf-8")
    return CommandRecord(stage, "", proc.returncode, time.monotonic() - started, stdout_path.name, stderr_path.name)


def guest_validation_commands(dependencies: Iterable[str], task_commands: Iterable[str], guest_trial_dir: str) -> list[tuple[str, str]]:
    prefix = f"cd {guest_trial_dir} && export NIXPKGS_ALLOW_UNFREE=1"
    commands = [
        ("flake_check", f"{prefix} && nix flake check --extra-experimental-features 'nix-command flakes' --no-write-lock-file ."),
        ("activation", f"{prefix} && nix develop --extra-experimental-features 'nix-command flakes' --no-write-lock-file . --command true"),
    ]
    for tool in dependencies:
        commands.append((f"dependency_{tool}", f"{prefix} && nix develop --extra-experimental-features 'nix-command flakes' --no-write-lock-file . --command sh -lc 'command -v {tool}'"))
    for index, command in enumerate(task_commands):
        commands.append((f"task_{index:02d}", f"{prefix} && nix develop --extra-experimental-features 'nix-command flakes' --no-write-lock-file . --command sh -lc {json.dumps(command)}"))
    return commands


def classify(records: list[CommandRecord]) -> str:
    failed = next((record for record in records if record.returncode != 0), None)
    if not failed:
        return "reproduced"
    if failed.stage == "flake_check":
        return "flake_failure"
    if failed.stage == "activation":
        return "activation_failure"
    if failed.stage.startswith("dependency_"):
        return "missing_dependency"
    if failed.stage.startswith("task_"):
        return "functional_failure"
    return "infrastructure_failure"


def run_trial(instance: str, task_idx: int, sample_name: str, source: Path, task: dict[str, Any], manifest: dict[str, Any], output_root: Path, timeout: int) -> dict[str, Any]:
    trial_id = f"task_{task_idx:02d}/{sample_name}"
    trial_output = output_root / "trials" / f"task_{task_idx:02d}" / sample_name
    trial_output.mkdir(parents=True, exist_ok=False)
    started_at = dt.datetime.now(dt.timezone.utc)
    records: list[CommandRecord] = []
    archive_fd, archive_name = tempfile.mkstemp(prefix="clean-vm-", suffix=".tar.gz")
    os.close(archive_fd)
    source_archive = Path(archive_name)
    guest_archive = f"{GUEST_ROOT}/{task_idx:02d}-{sample_name}.tar.gz"
    guest_trial_dir = f"{GUEST_ROOT}/{task_idx:02d}-{sample_name}"
    try:
        archive_trial(source, source_archive)
        require_success(lima(instance, "snapshot", "apply", instance, "--tag", SNAPSHOT_TAG), f"Restoring snapshot for {trial_id}")
        require_success(lima(instance, "start", instance), f"Starting guest for {trial_id}")
        wait_for_guest(instance)
        require_success(shell(instance, f"rm -rf {GUEST_ROOT} && mkdir -p {GUEST_ROOT}", timeout=timeout), f"Preparing guest workspace for {trial_id}")
        require_success(lima(instance, "copy", str(source_archive), f"{instance}:{guest_archive}"), f"Copying {trial_id} to guest")
        require_success(shell(instance, f"mkdir -p {guest_trial_dir} && tar -xzf {guest_archive} -C {guest_trial_dir}", timeout=timeout), f"Unpacking {trial_id} in guest")
        entry = manifest.get(str(task_idx))
        if entry is None:
            raise ReplayError(f"Task manifest has no entry for task index {task_idx}")
        for index, (stage, command) in enumerate(guest_validation_commands(task.get("dependency_list", []), entry.get("headless_commands", []), guest_trial_dir)):
            command_start = time.monotonic()
            proc = shell(instance, command, timeout=timeout)
            record = write_process_logs(trial_output, index, stage, proc, command_start)
            record.command = command
            records.append(record)
            if proc.returncode != 0:
                break
        outcome = classify(records)
    except ReplayError as error:
        log = trial_output / "infrastructure.stderr.log"
        log.write_text(f"{error}\n", encoding="utf-8")
        records.append(CommandRecord("infrastructure", "", None, 0.0, "", log.name))
        outcome = "infrastructure_failure"
    finally:
        source_archive.unlink(missing_ok=True)
    result = {
        "trial_id": trial_id,
        "source_trial_dir": str(source),
        "source_trial_meta": task["trial_meta"],
        "task_idx": task_idx,
        "track": task.get("track"),
        "instruction": task.get("instruction"),
        "excluded_behaviors": manifest.get(str(task_idx), {}).get("excluded_behaviors", []),
        "started_at": started_at.isoformat(),
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "outcome": outcome,
        "commands": [asdict(record) for record in records],
    }
    (trial_output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def write_summary(output_root: Path, source_run: Path, environment: dict[str, str], results: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for result in results:
        counts[result["outcome"]] = counts.get(result["outcome"], 0) + 1
    reproduced = counts.get("reproduced", 0)
    summary = {
        "source_run": str(source_run),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "environment": environment,
        "eligible_trials": len(results),
        "reproduced_trials": reproduced,
        "clean_host_reproduction_rate": reproduced / len(results) if results else 0.0,
        "outcome_counts": counts,
        "results": results,
    }
    (output_root / "clean_vm_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (output_root / "clean_vm_trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["trial_id", "task_idx", "track", "outcome", "failed_stage"])
        for result in results:
            failed = next((item["stage"] for item in result["commands"] if item["returncode"] not in (0, None)), "")
            writer.writerow([result["trial_id"], result["task_idx"], result.get("track", ""), result["outcome"], failed])
    report = ["# Clean NixOS Replay Report", "", f"Source RQ1 run: `{source_run.name}`  ", f"Eligible locally passing trials: **{len(results)}**  ", f"Reproduced: **{reproduced}/{len(results)} ({(reproduced / len(results) * 100) if results else 0:.1f}%)**", "", "## Outcome counts", ""]
    for outcome, count in sorted(counts.items()):
        report.append(f"- `{outcome}`: {count}")
    report.extend(["", "## Guest environment", "", f"- Lima: `{environment.get('lima_version', 'unknown')}`", f"- Nix: `{environment.get('nix_version', 'unknown')}`", f"- System: `{environment.get('guest_system', 'unknown')}`", "", "GUI workflows, interactive credentials, and persistent service setup were excluded according to `config/clean_vm_tasks.json`."])
    (output_root / "clean_vm_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(v.get("headless_commands", []), list) for v in data.values() if isinstance(v, dict)):
        raise ReplayError(f"Invalid task manifest: {path}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay locally passing flake trials in a clean NixOS Lima guest")
    subparsers = parser.add_subparsers(dest="action", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--instance", default="thesis-clean-eval")
    common.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    prepare_parser = subparsers.add_parser("prepare", parents=[common])
    prepare_parser.set_defaults(action="prepare")
    run_parser = subparsers.add_parser("run", parents=[common])
    run_parser.add_argument("--source-run", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, default=None)
    run_parser.add_argument("--task-manifest", type=Path, default=DEFAULT_MANIFEST)
    run_parser.add_argument("--timeout", type=int, default=1200)
    run_parser.set_defaults(action="run")
    teardown_parser = subparsers.add_parser("teardown", parents=[common])
    teardown_parser.add_argument("--delete", action="store_true", help="Delete the named Lima instance after stopping it")
    teardown_parser.set_defaults(action="teardown")
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            prepare(args.instance, args.template.resolve())
            return 0
        if args.action == "teardown":
            if not shutil.which("limactl"):
                raise ReplayError("limactl is not installed or not on PATH.")
            require_success(lima(args.instance, "stop", args.instance), f"Stopping guest '{args.instance}'")
            if args.delete:
                require_success(lima(args.instance, "delete", "--force", args.instance), f"Deleting guest '{args.instance}'")
            return 0
        source_run = args.source_run.resolve()
        manifest = load_manifest(args.task_manifest.resolve())
        environment = preflight(args.instance, require_snapshot=True)
        output_root = args.output_dir.resolve() if args.output_dir else REPO_ROOT / "eval_results" / "clean_vm" / f"{source_run.name}_{dt.datetime.now():%Y%m%d_%H%M%S}"
        output_root.mkdir(parents=True, exist_ok=False)
        results = []
        for task_idx, sample_name, source, task in eligible_trials(source_run):
            print(f"Replaying task_{task_idx:02d}/{sample_name}...", flush=True)
            results.append(run_trial(args.instance, task_idx, sample_name, source, task, manifest, output_root, args.timeout))
        write_summary(output_root, source_run, environment, results)
        print(f"Saved clean-host replay results to {output_root}")
        return 0
    except ReplayError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
