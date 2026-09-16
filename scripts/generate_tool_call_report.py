#!/usr/bin/env python3
"""
Generates CSV reports for tool call frequencies across all transcript.jsonl files
in the evaluation results directory.
"""

import csv
import glob
import json
from collections import Counter, defaultdict
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    eval_dir = base_dir / "eval_results"
    
    transcript_files = sorted(eval_dir.glob("task_*/sample_*/transcript.jsonl"))
    print(f"Found {len(transcript_files)} transcript files.")
    
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
                with open(meta_file, "r") as mf:
                    meta = json.load(mf)
            except Exception:
                pass
        
        trial_tool_counts = Counter()
        with open(tf, "r") as f:
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

    # Sort tools by frequency descending
    sorted_tools = [tool for tool, _ in total_tool_counts.most_common()]
    total_calls_all = sum(total_tool_counts.values())
    num_trials = len(transcript_files)

    # 1. Primary Report: Tool Call Frequency Summary
    summary_csv = eval_dir / "tool_call_frequency.csv"
    with open(summary_csv, "w", newline="") as f:
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
            f"{(total_calls_all / num_trials):.2f}"
        ])
    print(f"Generated {summary_csv}")

    # 2. Detailed Report: Tool Call Breakdown by Trial
    by_trial_csv = eval_dir / "tool_call_frequency_by_trial.csv"
    with open(by_trial_csv, "w", newline="") as f:
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
    print(f"Generated {by_trial_csv}")

    # 3. Aggregated Report: Tool Call Breakdown by Task
    task_counts = defaultdict(lambda: Counter())
    task_totals = Counter()
    for td in trial_data:
        task = td["task"]
        for tool, cnt in td["tool_counts"].items():
            task_counts[task][tool] += cnt
            task_totals[task] += cnt

    by_task_csv = eval_dir / "tool_call_frequency_by_task.csv"
    with open(by_task_csv, "w", newline="") as f:
        writer = csv.writer(f)
        header = ["task", "total_tool_calls"] + sorted_tools
        writer.writerow(header)
        for task in sorted(task_counts.keys()):
            row = [task, task_totals[task]] + [task_counts[task].get(tool, 0) for tool in sorted_tools]
            writer.writerow(row)
    print(f"Generated {by_task_csv}")

if __name__ == "__main__":
    main()
