#!/usr/bin/env python3
"""
Parses all transcript.jsonl files in eval_results and generates comprehensive CSV reports
on the commands executed via run_command.
"""

import csv
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

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
    # skip leading environment variable assignments like NIXPKGS_ALLOW_UNFREE=1
    while idx < len(parts) and "=" in parts[idx] and not parts[idx].startswith("-"):
        idx += 1
    if idx < len(parts):
        token = parts[idx].strip(";\"'")
        # if path like /usr/bin/env or /Applications/... or ./...
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

def main():
    base_dir = Path(__file__).resolve().parent.parent
    eval_dir = base_dir / "eval_results"
    transcript_files = sorted(eval_dir.glob("task_*/sample_*/transcript.jsonl"))

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
    print(f"Total run_command calls: {total_rc} across {total_trials} trials.")

    # 1. Exact Command Frequency CSV
    exact_csv = eval_dir / "run_command_frequency.csv"
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
    print(f"Generated {exact_csv}")

    # 2. Base Command Frequency CSV (e.g., nix, git, ls, ps, python3)
    base_csv = eval_dir / "run_command_base_frequency.csv"
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
            f"{(len({t for ts in base_cmd_trials.values() for t in ts}) / total_trials) * 100:.2f}%"
        ])
    print(f"Generated {base_csv}")

    # 3. Complete Sequential Command Log CSV
    log_csv = eval_dir / "run_command_log.csv"
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
    print(f"Generated {log_csv}")

if __name__ == "__main__":
    main()
