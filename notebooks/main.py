# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "altair>=5.0.0",
#     "marimo",
#     "pandas>=2.0.0",
# ]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path
    import altair as alt
    import marimo as mo
    import pandas as pd

    return Path, alt, json, mo, pd


@app.cell
def _(Path, mo):
    # Resolve project root and base eval_results directory robustly
    try:
        _base_dir = Path(__file__).resolve().parent.parent 
    except NameError:
        _base_dir = Path.cwd()
        if _base_dir.name == "notebooks":
            _base_dir = _base_dir.parent

    eval_base_dir = _base_dir / "eval_results"

    # Discover candidate evaluation run directories
    _dir_options = {}
    if eval_base_dir.exists():
        for _p in sorted(eval_base_dir.iterdir(), reverse=True):
            if _p.is_dir() and not _p.is_symlink() and not _p.name.startswith(".") and not _p.name.startswith("task_"):
                _has_data = (
                    (_p / "benchmark_summary.json").exists()
                    or (_p / "tool_call_frequency.csv").exists()
                    or (_p / "run_command_frequency.csv").exists()
                    or any(_p.glob("task_*"))
                )
                if _has_data:
                    _dir_options[_p.name] = _p.name

        # Include root eval_results if it contains benchmark data
        if (
            (eval_base_dir / "benchmark_summary.json").exists()
            or (eval_base_dir / "tool_call_frequency.csv").exists()
            or any(eval_base_dir.glob("task_*"))
        ):
            _dir_options["eval_results (root)"] = "."

    if not _dir_options:
        _dir_options["20260929_001840"] = "20260929_001840"

    # Default to 20260929_001840 if present, else first discovered directory
    _default_key = (
        "20260929_001840"
        if "20260929_001840" in _dir_options
        else next(iter(_dir_options.keys()))
    )

    eval_dir_dropdown = mo.ui.dropdown(
        options=_dir_options,
        value=_default_key,
        label="Evaluation Run Directory:",
    )
    return eval_base_dir, eval_dir_dropdown


@app.cell
def _(eval_base_dir, eval_dir_dropdown, json, pd):
    # Resolve active evaluation directory from dropdown selection
    _rel_path = eval_dir_dropdown.value
    eval_dir = (eval_base_dir / _rel_path).resolve() if _rel_path and _rel_path != "." else eval_base_dir

    # 1. Primary Tool Call Summary
    _tools_csv = eval_dir / "tool_call_frequency.csv"
    if _tools_csv.exists():
        df_tools_raw = pd.read_csv(_tools_csv)
        total_row = df_tools_raw[df_tools_raw["tool_name"] == "TOTAL"]
        df_tools = df_tools_raw[df_tools_raw["tool_name"] != "TOTAL"].copy()
        df_tools["percentage_num"] = df_tools["percentage_of_total"].str.rstrip("%").astype(float)
        df_tools["trial_prev_num"] = df_tools["trial_prevalence_pct"].str.rstrip("%").astype(float)
    else:
        df_tools = pd.DataFrame(
            columns=[
                "tool_name",
                "call_count",
                "percentage_of_total",
                "trials_using_tool",
                "trial_prevalence_pct",
                "mean_calls_per_trial",
                "percentage_num",
                "trial_prev_num",
            ]
        )
        total_row = pd.DataFrame(
            columns=[
                "tool_name",
                "call_count",
                "percentage_of_total",
                "trials_using_tool",
                "trial_prevalence_pct",
                "mean_calls_per_trial",
            ]
        )

    # 2. Tool Calls by Task
    _task_csv = eval_dir / "tool_call_frequency_by_task.csv"
    if _task_csv.exists():
        df_task_raw = pd.read_csv(_task_csv)
        _tool_cols = [c for c in df_task_raw.columns if c not in ["task", "total_tool_calls"]]
        df_task_long = df_task_raw.melt(
            id_vars=["task"],
            value_vars=_tool_cols,
            var_name="tool_name",
            value_name="call_count",
        )
    else:
        df_task_raw = pd.DataFrame(columns=["task", "total_tool_calls"])
        df_task_long = pd.DataFrame(columns=["task", "tool_name", "call_count"])

    # 3. Exact Command Frequencies
    _cmd_csv = eval_dir / "run_command_frequency.csv"
    if _cmd_csv.exists():
        df_cmd = pd.read_csv(_cmd_csv)
        df_cmd["percentage_num"] = df_cmd["percentage_of_all_run_command"].str.rstrip("%").astype(float)
        df_cmd["trial_prev_num"] = df_cmd["trial_prevalence_pct"].str.rstrip("%").astype(float)
        df_cmd["short_command"] = df_cmd["command"].apply(
            lambda s: s if len(s) <= 48 else s[:45] + "..."
        )
    else:
        df_cmd = pd.DataFrame(
            columns=[
                "command",
                "base_command",
                "execution_count",
                "percentage_of_all_run_command",
                "unique_trials_used",
                "trial_prevalence_pct",
                "percentage_num",
                "trial_prev_num",
                "short_command",
            ]
        )

    # 4. Base Command Frequencies
    _base_csv = eval_dir / "run_command_base_frequency.csv"
    if _base_csv.exists():
        df_base_raw = pd.read_csv(_base_csv)
        df_base = df_base_raw[df_base_raw["base_command"] != "TOTAL"].copy()
        df_base["percentage_num"] = df_base["percentage_of_all_run_command"].str.rstrip("%").astype(float)
        df_base["trial_prev_num"] = df_base["trial_prevalence_pct"].str.rstrip("%").astype(float)
    else:
        df_base = pd.DataFrame(
            columns=[
                "base_command",
                "execution_count",
                "percentage_of_all_run_command",
                "unique_trials_used",
                "trial_prevalence_pct",
                "percentage_num",
                "trial_prev_num",
            ]
        )

    # 5. Raw Command Invocations Log
    log_csv_path = eval_dir / "run_command_log.csv"
    if log_csv_path.exists():
        df_log = pd.read_csv(log_csv_path)
    else:
        df_log = pd.DataFrame(
            columns=[
                "task",
                "sample",
                "step_index",
                "created_at",
                "cwd",
                "base_command",
                "command",
                "tool_action",
                "tool_summary",
            ]
        )

    # 6. Benchmark Summary JSON
    summary_json_path = eval_dir / "benchmark_summary.json"
    summary_data = {}
    if summary_json_path.exists():
        try:
            with open(summary_json_path) as _f:
                summary_data = json.load(_f)
        except Exception:
            pass

    # 7. MCP Tool Invocations Log & Query Frequencies
    mcp_log_csv_path = eval_dir / "mcp_tool_log.csv"
    mcp_freq_csv_path = eval_dir / "mcp_tool_frequency.csv"
    if mcp_log_csv_path.exists() and mcp_freq_csv_path.exists():
        df_mcp_log = pd.read_csv(mcp_log_csv_path).fillna("")
        df_mcp_queries = pd.read_csv(mcp_freq_csv_path).fillna("")
    else:
        _mcp_records = []
        _transcript_files = sorted(eval_dir.glob("task_*/sample_*/transcript.jsonl"))
        for _tf in _transcript_files:
            _task = _tf.parent.parent.name
            _sample = _tf.parent.name
            try:
                with open(_tf, "r", encoding="utf-8") as _f:
                    for _line in _f:
                        try:
                            _d = json.loads(_line)
                        except Exception:
                            continue
                        _step = _d.get("step_index", "")
                        _created = _d.get("created_at", "")
                        for _tc in _d.get("tool_calls", []):
                            if _tc.get("name") == "call_mcp_tool":
                                _r_args = _tc.get("args", {})
                                _s_name = str(_r_args.get("ServerName", "")).strip("\"'")
                                _t_name = str(_r_args.get("ToolName", "")).strip("\"'")
                                _t_act = str(_r_args.get("toolAction", "")).strip("\"'")
                                _t_sum = str(_r_args.get("toolSummary", "")).strip("\"'")
                                _i_args = _r_args.get("Arguments", {})
                                if isinstance(_i_args, str):
                                    try:
                                        _i_args = json.loads(_i_args)
                                    except Exception:
                                        _i_args = {"raw": _i_args}
                                if not isinstance(_i_args, dict):
                                    _i_args = {"raw": str(_i_args)}

                                _mcp_records.append({
                                    "task": _task,
                                    "sample": _sample,
                                    "step_index": _step,
                                    "created_at": _created,
                                    "server_name": _s_name,
                                    "mcp_tool": _t_name,
                                    "action": _i_args.get("action", ""),
                                    "query": _i_args.get("query", ""),
                                    "type": _i_args.get("type", ""),
                                    "channel": _i_args.get("channel", ""),
                                    "limit": _i_args.get("limit", ""),
                                    "tool_action": _t_act,
                                    "tool_summary": _t_sum,
                                    "arguments_json": json.dumps(_i_args, sort_keys=True),
                                })
            except Exception:
                pass

        df_mcp_log = pd.DataFrame(_mcp_records)
        if not df_mcp_log.empty:
            _q_agg = (
                df_mcp_log.groupby(["action", "query", "type"])
                .agg(
                    call_count=("step_index", "count"),
                    unique_trials_used=("task", lambda s: len(set(zip(s, df_mcp_log.loc[s.index, "sample"])))),
                    sample_arguments=("arguments_json", "first"),
                )
                .reset_index()
                .sort_values(by="call_count", ascending=False)
            )
            _tot_m = len(df_mcp_log)
            _num_tr = len(_transcript_files) or 1
            _q_agg["percentage_of_all_mcp_calls"] = _q_agg["call_count"].apply(
                lambda c: f"{(c / _tot_m) * 100:.2f}%"
            )
            _q_agg["trial_prevalence_pct"] = _q_agg["unique_trials_used"].apply(
                lambda u: f"{(u / _num_tr) * 100:.2f}%"
            )
            df_mcp_queries = _q_agg[
                [
                    "action",
                    "query",
                    "type",
                    "call_count",
                    "percentage_of_all_mcp_calls",
                    "unique_trials_used",
                    "trial_prevalence_pct",
                    "sample_arguments",
                ]
            ]
        else:
            df_mcp_queries = pd.DataFrame(
                columns=[
                    "action",
                    "query",
                    "type",
                    "call_count",
                    "percentage_of_all_mcp_calls",
                    "unique_trials_used",
                    "trial_prevalence_pct",
                    "sample_arguments",
                ]
            )

    # Extract all dynamic metrics
    total_tool_calls = (
        int(total_row["call_count"].values[0])
        if not total_row.empty
        else int(df_tools["call_count"].sum())
    )
    total_trials = (
        int(total_row["trials_using_tool"].values[0])
        if not total_row.empty
        else len(df_task_raw) * 3
    )
    mean_calls_per_trial = (
        float(total_row["mean_calls_per_trial"].values[0])
        if not total_row.empty
        else (total_tool_calls / total_trials if total_trials else 0.0)
    )

    tasks_list = summary_data.get("tasks", [])
    num_tasks = len(tasks_list) or len(df_task_raw)
    num_samples = summary_data.get("num_samples", 3)
    pass1_pct = summary_data.get("overall_scores", {}).get("pass@1", 0.0) * 100
    pass3_pct = summary_data.get("overall_scores", {}).get("pass@3", 0.0) * 100

    passed_trials = (
        sum(t.get("c", 0) for t in tasks_list)
        if tasks_list
        else int(round(pass1_pct / 100 * total_trials))
    )
    solved_tasks = (
        sum(1 for t in tasks_list if t.get("c", 0) > 0)
        if tasks_list
        else num_tasks
    )

    perf = summary_data.get("perf_summary", {})
    mean_duration_s = perf.get("mean_duration_s", 0.0)
    mean_total_tokens = perf.get("mean_total_tokens", 0.0)
    mean_thinking_tokens = perf.get("mean_thinking_tokens", 0.0)

    total_run_command_calls = int(df_cmd["execution_count"].sum())
    unique_commands_count = len(df_cmd)
    num_base_commands = len(df_base)

    top1_tool = df_tools.iloc[0]["tool_name"] if len(df_tools) > 0 else "run_command"
    top1_pct = df_tools.iloc[0]["percentage_num"] if len(df_tools) > 0 else 0.0
    top2_tool = df_tools.iloc[1]["tool_name"] if len(df_tools) > 1 else "view_file"
    top2_pct = df_tools.iloc[1]["percentage_num"] if len(df_tools) > 1 else 0.0
    top2_combined_pct = top1_pct + top2_pct

    def _get_tool_stat(name, col, default="0.0%"):
        match = df_tools.loc[df_tools["tool_name"] == name, col]
        return match.values[0] if not match.empty else default

    grep_prev = _get_tool_stat("grep_search", "trial_prevalence_pct")
    find_prev = _get_tool_stat("find_by_name", "trial_prevalence_pct")
    write_pct = _get_tool_stat("write_to_file", "percentage_of_total")

    # Base command categories
    fs_cmds = ["ls", "pwd", "find"]
    nix_cmds = ["nix"]
    git_cmds = ["git"]

    def _get_base_group_stats(cmd_list):
        match = df_base[df_base["base_command"].isin(cmd_list)]
        cnt = int(match["execution_count"].sum())
        pct = float(match["percentage_num"].sum())
        return cnt, pct

    fs_cnt, fs_pct = _get_base_group_stats(fs_cmds)
    nix_cnt, nix_pct = _get_base_group_stats(nix_cmds)
    git_cnt, git_pct = _get_base_group_stats(git_cmds)
    other_cnt = max(0, total_run_command_calls - (fs_cnt + nix_cnt + git_cnt))
    other_pct = max(0.0, 100.0 - (fs_pct + nix_pct + git_pct))

    top3_base = df_base.head(3)
    top3_base_names = ", ".join(top3_base["base_command"].tolist())
    top3_base_pct = top3_base["percentage_num"].sum()

    top5_base = df_base.head(5)
    top5_base_names = ", ".join(top5_base["base_command"].tolist())

    git_status_row = df_cmd[df_cmd["command"] == "git status"]
    git_status_count = (
        int(git_status_row["execution_count"].values[0])
        if not git_status_row.empty
        else 0
    )
    git_status_prev = (
        git_status_row["trial_prevalence_pct"].values[0]
        if not git_status_row.empty
        else "0%"
    )

    nix_base_row = df_base[df_base["base_command"] == "nix"]
    nix_overall_pct = (
        nix_base_row["percentage_of_all_run_command"].values[0]
        if not nix_base_row.empty
        else "0%"
    )
    nix_prev = (
        nix_base_row["trial_prevalence_pct"].values[0]
        if not nix_base_row.empty
        else "0%"
    )

    git_base_row = df_base[df_base["base_command"] == "git"]
    git_overall_pct = (
        git_base_row["percentage_of_all_run_command"].values[0]
        if not git_base_row.empty
        else "0%"
    )

    stats = {
        "total_trials": total_trials,
        "num_tasks": num_tasks,
        "num_samples": num_samples,
        "pass1_pct": pass1_pct,
        "pass3_pct": pass3_pct,
        "passed_trials": passed_trials,
        "solved_tasks": solved_tasks,
        "total_tool_calls": total_tool_calls,
        "mean_calls_per_trial": mean_calls_per_trial,
        "mean_duration_s": mean_duration_s,
        "mean_total_tokens": mean_total_tokens,
        "mean_thinking_tokens": mean_thinking_tokens,
        "total_run_command_calls": total_run_command_calls,
        "unique_commands_count": unique_commands_count,
        "num_base_commands": num_base_commands,
        "top1_tool": top1_tool,
        "top1_pct": top1_pct,
        "top2_tool": top2_tool,
        "top2_pct": top2_pct,
        "top2_combined_pct": top2_combined_pct,
        "grep_prev": grep_prev,
        "find_prev": find_prev,
        "write_pct": write_pct,
        "fs_cnt": fs_cnt,
        "fs_pct": fs_pct,
        "nix_cnt": nix_cnt,
        "nix_pct": nix_pct,
        "git_cnt": git_cnt,
        "git_pct": git_pct,
        "other_cnt": other_cnt,
        "other_pct": other_pct,
        "top3_base_names": top3_base_names,
        "top3_base_pct": top3_base_pct,
        "top5_base_names": top5_base_names,
        "git_status_count": git_status_count,
        "git_status_prev": git_status_prev,
        "nix_overall_pct": nix_overall_pct,
        "nix_prev": nix_prev,
        "git_overall_pct": git_overall_pct,
        "total_mcp_calls": len(df_mcp_log),
        "unique_mcp_queries": len(df_mcp_queries),
    }
    return (
        df_base,
        df_cmd,
        df_log,
        df_mcp_log,
        df_mcp_queries,
        df_task_long,
        df_tools,
        stats,
    )


@app.cell
def _(eval_dir_dropdown, mo, stats):
    _header = mo.vstack([
        mo.md("# Autonomous Agent Telemetry & Tool Call Analysis"),
        mo.hstack(
            [
                eval_dir_dropdown,
                mo.md(
                    f"**Trials:** {stats['total_trials']} &nbsp;|&nbsp; "
                    f"**Tasks:** {stats['num_tasks']} ($n={stats['num_samples']}$) &nbsp;|&nbsp; "
                    f"**pass@1:** {stats['pass1_pct']:.1f}%"
                ),
            ],
            justify="start",
            align="center",
        ),
        mo.md(f"""

        ### Benchmark Summary Metrics
        - **Overall Success Rate**: **pass@1 = {stats['pass1_pct']:.2f}%** ({stats['passed_trials']}/{stats['total_trials']} trials passed), **pass@3 = {stats['pass3_pct']:.2f}%** ({stats['solved_tasks']}/{stats['num_tasks']} tasks solved)
        - **Total Tool Invocations**: **{stats['total_tool_calls']:,} calls** (mean **{stats['mean_calls_per_trial']:.2f} calls/trial**)
        - **Total `run_command` Executions**: **{stats['total_run_command_calls']:,} commands** across {stats['unique_commands_count']} unique command invocations
        - **Mean Trial Duration**: **{stats['mean_duration_s']:.2f} seconds**
        - **Mean Tokens / Trial**: **{stats['mean_total_tokens']:,.0f} tokens** ({stats['mean_thinking_tokens']:,.0f} thinking tokens)
        """),
    ])
    _header
    return


@app.cell
def _(alt, df_tools, stats):
    # Chart 1A: Total Tool Call Count (Horizontal Bar Chart)
    _bars = (
        alt.Chart(df_tools)
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            y=alt.Y(
                "tool_name:N",
                sort="-x",
                title="Agent Tool",
                axis=alt.Axis(labelFontSize=12, titleFontSize=13),
            ),
            x=alt.X(
                "call_count:Q",
                title=f"Total Calls Across {stats['total_trials']} Trials",
                axis=alt.Axis(labelFontSize=11, titleFontSize=13),
            ),
            color=alt.Color(
                "tool_name:N",
                legend=None,
                scale=alt.Scale(scheme="tableau10"),
            ),
            tooltip=[
                alt.Tooltip("tool_name:N", title="Tool Name"),
                alt.Tooltip("call_count:Q", title="Total Calls"),
                alt.Tooltip("percentage_of_total:N", title="% of Total Tool Calls"),
                alt.Tooltip("trials_using_tool:Q", title="Trials Using Tool"),
                alt.Tooltip("trial_prevalence_pct:N", title="Trial Prevalence"),
                alt.Tooltip("mean_calls_per_trial:Q", title="Mean Calls / Trial", format=".2f"),
            ],
        )
    )

    _text = _bars.mark_text(
        align="left",
        baseline="middle",
        dx=6,
        fontSize=11,
        fontWeight="bold",
    ).encode(
        text=alt.Text("call_count:Q", format=",d")
    )

    chart_tool_frequency = (
        (_bars + _text)
        .properties(
            width=680,
            height=280,
            title=alt.TitleParams(
                text="Tool Call Frequency Across All Evaluation Trials",
                subtitle=f"Source: eval_results/tool_call_frequency.csv ({stats['total_tool_calls']:,} total tool invocations across {stats['total_trials']} trials)",
                fontSize=15,
                subtitleFontSize=12,
            ),
        )
    )
    chart_tool_frequency
    return


@app.cell
def _(alt, df_tools, stats):
    # Chart 1B: Trial Prevalence Percentage
    _bars_prev = (
        alt.Chart(df_tools)
        .mark_bar(cornerRadiusEnd=5, color="#3b82f6")
        .encode(
            y=alt.Y(
                "tool_name:N",
                sort="-x",
                title="Agent Tool",
                axis=alt.Axis(labelFontSize=12, titleFontSize=13),
            ),
            x=alt.X(
                "trial_prev_num:Q",
                title="Trial Prevalence (%)",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(labelFontSize=11, titleFontSize=13, format="d"),
            ),
            tooltip=[
                alt.Tooltip("tool_name:N", title="Tool Name"),
                alt.Tooltip("trial_prevalence_pct:N", title="Trial Prevalence"),
                alt.Tooltip("trials_using_tool:Q", title=f"Trials (out of {stats['total_trials']})"),
                alt.Tooltip("call_count:Q", title="Total Calls"),
            ],
        )
    )

    _text_prev = _bars_prev.mark_text(
        align="left",
        baseline="middle",
        dx=6,
        fontSize=11,
        fontWeight="bold",
    ).encode(
        text=alt.Text("trial_prevalence_pct:N")
    )

    chart_tool_prevalence = (
        (_bars_prev + _text_prev)
        .properties(
            width=680,
            height=260,
            title=alt.TitleParams(
                text="Tool Trial Prevalence: Percentage of Trials Utilizing Each Tool",
                subtitle=f"High prevalence in grep_search ({stats['grep_prev']}) and find_by_name ({stats['find_prev']}) demonstrates diagnostic adoption despite lower call volume",
                fontSize=14,
                subtitleFontSize=11,
            ),
        )
    )
    chart_tool_prevalence
    return


@app.cell
def _(alt, df_task_long, stats):
    chart_task_stacked = (
        alt.Chart(df_task_long)
        .mark_bar()
        .encode(
            x=alt.X(
                "task:N",
                title="Benchmark Task ID",
                axis=alt.Axis(labelAngle=0, labelFontSize=11, titleFontSize=13),
            ),
            y=alt.Y(
                "call_count:Q",
                title=f"Total Tool Calls ({stats['num_samples']} trials aggregated)",
                axis=alt.Axis(labelFontSize=11, titleFontSize=13),
            ),
            color=alt.Color(
                "tool_name:N",
                title="Tool Name",
                scale=alt.Scale(scheme="tableau10"),
                legend=alt.Legend(orient="right", titleFontSize=12, labelFontSize=11),
            ),
            order=alt.Order("call_count:Q", sort="descending"),
            tooltip=[
                alt.Tooltip("task:N", title="Task"),
                alt.Tooltip("tool_name:N", title="Tool"),
                alt.Tooltip("call_count:Q", title="Calls in Task"),
            ],
        )
        .properties(
            width=700,
            height=320,
            title=alt.TitleParams(
                text="Tool Call Composition Across Benchmark Tasks",
                subtitle=f"Aggregated across {stats['num_samples']} sample runs per task ({stats['num_tasks']} tasks)",
                fontSize=15,
                subtitleFontSize=12,
            ),
        )
    )
    chart_task_stacked
    return


@app.cell
def _(mo):
    top_n_slider = mo.ui.slider(
        start=5,
        stop=25,
        value=15,
        step=5,
        label="Select Top N Commands to Display",
    )
    top_n_slider
    return (top_n_slider,)


@app.cell
def _(alt, df_cmd, stats, top_n_slider):
    _top_n = top_n_slider.value
    _df_top = df_cmd.head(_top_n).copy()

    _bars_cmd = (
        alt.Chart(_df_top)
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            y=alt.Y(
                "short_command:N",
                sort="-x",
                title="Executed Command Line",
                axis=alt.Axis(labelFontSize=11, titleFontSize=13),
            ),
            x=alt.X(
                "execution_count:Q",
                title="Total Executions",
                axis=alt.Axis(labelFontSize=11, titleFontSize=13),
            ),
            color=alt.Color(
                "base_command:N",
                title="Command Family",
                scale=alt.Scale(scheme="category10"),
                legend=alt.Legend(orient="right", titleFontSize=12, labelFontSize=11),
            ),
            tooltip=[
                alt.Tooltip("command:N", title="Full Command"),
                alt.Tooltip("base_command:N", title="Base Executable"),
                alt.Tooltip("execution_count:Q", title="Execution Count"),
                alt.Tooltip("percentage_of_all_run_command:N", title="% of run_command Calls"),
                alt.Tooltip("unique_trials_used:Q", title="Unique Trials Used"),
                alt.Tooltip("trial_prevalence_pct:N", title="Trial Prevalence"),
            ],
        )
    )

    _text_cmd = _bars_cmd.mark_text(
        align="left",
        baseline="middle",
        dx=5,
        fontSize=11,
        fontWeight="bold",
    ).encode(
        text=alt.Text("execution_count:Q")
    )

    chart_top_commands = (
        (_bars_cmd + _text_cmd)
        .properties(
            width=680,
            height=max(220, _top_n * 22),
            title=alt.TitleParams(
                text=f"Top {_top_n} Shell Commands Executed via run_command",
                subtitle=f"Displaying {_top_n} most frequent commands out of {stats['unique_commands_count']} unique command strings across {stats['total_trials']} trials",
                fontSize=15,
                subtitleFontSize=12,
            ),
        )
    )
    chart_top_commands
    return


@app.cell
def _(mo, stats):
    mo.md(f"""
    ---
    ## 4. Base Command Family Distribution (`run_command_base_frequency.csv`)

    ### Why a Categorical Bar Chart of Base Executables is Most Appropriate
    - While {stats['unique_commands_count']} unique command variations exist, the agent's actions collapse into **{stats['num_base_commands']} primary command-line utilities**.
    - Grouping commands by their base executable reveals the agent's fundamental **triad of operations**:
      1. **Filesystem Inspection & Orientation** (`ls`, `pwd`, `find`): **{stats['fs_cnt']} executions ({stats['fs_pct']:.2f}%)**
      2. **Nix Packaging & Environment Validation** (`nix`): **{stats['nix_cnt']} executions ({stats['nix_pct']:.2f}%)**
      3. **Version Control & Artifact Tracking** (`git`): **{stats['git_cnt']} executions ({stats['git_pct']:.2f}%)**
      4. **Runtime Testing & Diagnostic Execution** (others): **{stats['other_cnt']} executions ({stats['other_pct']:.2f}%)**
    """)
    return


@app.cell
def _(alt, df_base):
    _top_base = df_base.head(12).copy()

    _bars_base = (
        alt.Chart(_top_base)
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            y=alt.Y(
                "base_command:N",
                sort="-x",
                title="Base Executable",
                axis=alt.Axis(labelFontSize=12, titleFontSize=13),
            ),
            x=alt.X(
                "execution_count:Q",
                title="Total Executions",
                axis=alt.Axis(labelFontSize=11, titleFontSize=13),
            ),
            color=alt.Color(
                "base_command:N",
                legend=None,
                scale=alt.Scale(scheme="tableau10"),
            ),
            tooltip=[
                alt.Tooltip("base_command:N", title="Base Command"),
                alt.Tooltip("execution_count:Q", title="Total Executions"),
                alt.Tooltip("percentage_of_all_run_command:N", title="% of run_command"),
                alt.Tooltip("unique_trials_used:Q", title="Trials Using Command"),
                alt.Tooltip("trial_prevalence_pct:N", title="Trial Prevalence"),
            ],
        )
    )

    _text_base = _bars_base.mark_text(
        align="left",
        baseline="middle",
        dx=5,
        fontSize=11,
        fontWeight="bold",
    ).encode(
        text=alt.Text("execution_count:Q")
    )

    chart_base_commands = (
        (_bars_base + _text_base)
        .properties(
            width=680,
            height=300,
            title=alt.TitleParams(
                text="Top Executables Invoked via run_command",
                subtitle="",
                fontSize=15,
                subtitleFontSize=12,
            ),
        )
    )
    chart_base_commands
    return


@app.cell
def _(mo, stats):
    mo.md(f"""
    ---
    ### Full Command Invocations for Top 5 Base Executables ({stats['top5_base_names']}) & MCP Tool Queries

    Because specialized executables like `nix` or `find` and external MCP tool queries (`call_mcp_tool`) are often called with task-specific arguments (such as custom build commands, embedded scripts, package searches, or attribute queries), their invocations fragment into many unique parameter strings that don't individually rank in the global top-N bar chart.

    Use the interactive view below to inspect **each invocation, command string, and MCP query payload** for the top base executables and the NixOS MCP server:
    - **Unique Commands / Queries**: Aggregates distinct full command strings and MCP query argument payloads with their invocation counts and trial prevalence.
    - **All Invocations Log**: Chronological audit trail showing every individual execution alongside the task, sample, step, agent action, and raw arguments.
    """)
    return


@app.cell
def _(df_base, df_cmd, df_log, df_mcp_log, df_mcp_queries, mo):
    _top5_bases = df_base["base_command"].head(5).tolist()

    _tabs_dict = {}
    for _base in _top5_bases:
        _df_c = df_cmd[df_cmd["base_command"] == _base][
            [
                "command",
                "execution_count",
                "percentage_of_all_run_command",
                "unique_trials_used",
                "trial_prevalence_pct",
            ]
        ].copy()

        _df_l = df_log[df_log["base_command"] == _base][
            [
                "task",
                "sample",
                "step_index",
                "command",
                "tool_action",
                "cwd",
            ]
        ].copy()

        _table_unique = mo.ui.table(
            _df_c,
            pagination=True,
            page_size=10,
            show_column_summaries=False,
            label=f"Unique Commands ({len(_df_c)})",
        )

        _table_invocations = mo.ui.table(
            _df_l,
            pagination=True,
            page_size=10,
            show_column_summaries=False,
            label=f"All Invocations Log ({len(_df_l)})",
        )

        _sub_tabs = mo.ui.tabs(
            {
                f"Unique Commands ({len(_df_c)})": _table_unique,
                f"All Invocations Log ({len(_df_l)})": _table_invocations,
            }
        )
        _tabs_dict[f"{_base} ({len(_df_l)} calls)"] = _sub_tabs

    if not df_mcp_log.empty:
        _table_mcp_unique = mo.ui.table(
            df_mcp_queries,
            pagination=True,
            page_size=10,
            show_column_summaries=False,
            label=f"Unique Queries & Arguments ({len(df_mcp_queries)})",
        )
        _table_mcp_invocations = mo.ui.table(
            df_mcp_log[
                [
                    "task",
                    "sample",
                    "step_index",
                    "action",
                    "query",
                    "type",
                    "arguments_json",
                    "tool_action",
                    "server_name",
                    "mcp_tool",
                ]
            ],
            pagination=True,
            page_size=10,
            show_column_summaries=False,
            label=f"All Invocations Log ({len(df_mcp_log)})",
        )
        _sub_tabs_mcp = mo.ui.tabs(
            {
                f"Unique Queries & Arguments ({len(df_mcp_queries)})": _table_mcp_unique,
                f"All Invocations Log ({len(df_mcp_log)})": _table_mcp_invocations,
            }
        )
        _tabs_dict[f"call_mcp_tool ({len(df_mcp_log)} calls)"] = _sub_tabs_mcp

    top5_command_breakdown = mo.ui.tabs(_tabs_dict)
    top5_command_breakdown
    return


@app.cell
def _(mo, stats):
    mo.md(f"""
    ---
    ## 5. MCP Tool Query Breakdown (`call_mcp_tool` &rarr; `nixos:nix`)

    Autonomous flake synthesis relies on the `nixos` Model Context Protocol (MCP) server to query package names and attribute metadata in Nixpkgs without blind guessing.

    Across **{stats['total_mcp_calls']}** total MCP invocations ({stats['unique_mcp_queries']} unique queries/arguments):
    - **`search` action**: Used when discovering package attribute names in Nixpkgs (e.g., `mysql`, `rstudio`, `cmake`, `dotnet-sdk`).
    - **`info` action**: Used to inspect derivations, versions, and build inputs once attribute names are identified (e.g., `mysql84`, `dotnet-sdk_8`, `R`) prior to writing `flake.nix`.
    """)
    return


@app.cell
def _(alt, df_mcp_log, mo):
    if df_mcp_log.empty:
        chart_mcp_queries = mo.md("*No MCP tool calls recorded in this evaluation run.*")
    else:
        _df_m = df_mcp_log.copy()
        _df_m["query_label"] = _df_m["query"].replace("", "(empty/root)")
        _top_queries = _df_m["query_label"].value_counts().head(15).index.tolist()
        _df_top_mcp = (
            _df_m[_df_m["query_label"].isin(_top_queries)]
            .groupby(["query_label", "action"])
            .size()
            .reset_index(name="call_count")
        )

        _bars_mcp = (
            alt.Chart(_df_top_mcp)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                y=alt.Y(
                    "query_label:N",
                    sort=alt.EncodingSortField(field="call_count", op="sum", order="descending"),
                    title="Target Package / Query Term",
                    axis=alt.Axis(labelFontSize=12, titleFontSize=13),
                ),
                x=alt.X(
                    "call_count:Q",
                    title="Invocations Count",
                    axis=alt.Axis(labelFontSize=11, titleFontSize=13),
                ),
                color=alt.Color(
                    "action:N",
                    title="MCP Action",
                    scale=alt.Scale(
                        domain=["search", "info"],
                        range=["#2563eb", "#059669"],
                    ),
                    legend=alt.Legend(orient="bottom-right", titleFontSize=12, labelFontSize=11),
                ),
                tooltip=[
                    alt.Tooltip("query_label:N", title="Query Term"),
                    alt.Tooltip("action:N", title="Action"),
                    alt.Tooltip("call_count:Q", title="Invocations"),
                ],
            )
        )

        chart_mcp_queries = (
            _bars_mcp
            .properties(
                width=680,
                height=350,
                title=alt.TitleParams(
                    text="Top 15 Nixpkgs MCP Queries Broken Down by Action",
                    subtitle="Shows the agent's strategy of searching for candidate packages before querying derivation details via info",
                    fontSize=15,
                    subtitleFontSize=12,
                ),
            )
        )
    chart_mcp_queries
    return


@app.cell
def _(df_mcp_queries, mo):
    mcp_arguments_table = mo.ui.table(
        df_mcp_queries,
        pagination=True,
        page_size=15,
        show_column_summaries=True,
        label=f"All MCP Queries and Parameter Payloads",
    )
    _mcp_section = mo.vstack([
        mcp_arguments_table,
    ])
    _mcp_section
    return


if __name__ == "__main__":
    app.run()
