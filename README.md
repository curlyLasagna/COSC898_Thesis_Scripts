# Autonomous Nix Flake Generation & Evaluation Suite

This repository contains the implementation, benchmark harness, and evaluation framework for evaluating autonomous AI agents (powered by Google Antigravity and the [`course-flake-generator`](file:///Users/luis/Code/Thesis_Implementation/.agents/skills/course-flake-generator/SKILL.md) skill) in generating reproducible Nix flake development environments for computer science coursework and software projects.

---

## Table of Contents

- [Overview](#overview)
- [Pass@k Evaluation Runner (`evaluate_pass_at_k.py`)](#passk-evaluation-runner-evaluate_pass_at_kpy)
  - [Command-Line Flags Reference](#command-line-flags-reference)
  - [Usage Examples](#usage-examples)
  - [Task Types Supported](#task-types-supported)
  - [Evaluation Pipeline & Verification Criteria](#evaluation-pipeline--verification-criteria)
- [RQ2: Clean-Host Reproducibility Replay](#rq2-clean-host-reproducibility-replay)
- [Results & Artifact Structure](#results--artifact-structure)
- [Telemetry & Tool Call Reporting Scripts](#telemetry--tool-call-reporting-scripts)
  - [Tool Call Frequency Analysis](#tool-call-frequency-analysis)
  - [Executed Command Frequency Analysis](#executed-command-frequency-analysis)
- [Interactive Prompt Runner](#interactive-prompt-runner)
- [Benchmark Datasets & Workloads](#benchmark-datasets--workloads)
- [Development Environment](#development-environment)

---

## Overview

Configuring reproducible software development environments for computer science coursework is notoriously challenging due to cross-platform inconsistencies, differing operating systems, and missing dependencies. This project evaluates whether autonomous coding agents can automatically synthesize valid, isolated Nix flake development environments (`flake.nix`) given either:

1. **Greenfield Tasks**: Natural language instructions (e.g. syllabus excerpts or setup guides) requiring specific compilers, interpreters, runtimes, and CLI tools.
2. **Brownfield Tasks**: Existing codebases and multi-module project directories requiring dependency and language auto-detection.

Evaluations measure functional correctness using the unbiased $pass@k$ metric (Chen et al., 2021) alongside performance telemetry (runtime duration, agent conversation turns, total tokens, and thinking tokens).

---

## Pass@k Evaluation Runner (`evaluate_pass_at_k.py`)

[`evaluate_pass_at_k.py`](file:///Users/luis/Code/Thesis_Implementation/evaluate_pass_at_k.py) is the primary automated benchmarking harness. It orchestrates trials, isolates workspaces, invokes the Antigravity agent CLI (`agy`), records telemetry, verifies the generated Nix environments, and computes $pass@k$ scores.

### Command-Line Flags Reference

| Flag | Aliases | Type | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `--inputs` | — | `str` (list) | `["input/nl_instruction_inputs.jsonl"]` | One or more input paths: either `.jsonl` benchmark files (greenfield tasks) or directories containing project code (brownfield tasks). |
| `-n` | `--num-samples` | `int` | `3` | Number of independent samples/trials to execute per task ($n$). |
| `-k` | `--k-values` | `int` (list) | `[1, 3]` | Values of $k$ for calculating unbiased $pass@k$ estimators ($k \le n$). |
| `--output-dir` | — | `str` | `"eval_results"` | Directory where trial workspaces, generated flakes, transcripts, and reports are saved. |
| `-i` | `--task-index`, `--index` | `int` | `None` | Run only a specific 0-based task index (e.g. `-i 0` for task 1). Mutually exclusive with `-m` / `--num-tasks`. |
| `-m` | `--num-tasks`, `--limit`, `--max-tasks` | `int` | `None` | Maximum number of tasks to run from the discovered inputs. Mutually exclusive with `-i` / `--task-index`. |
| `--start-index` | `--offset` | `int` | `0` | Starting 0-based task index when running a slice of tasks (default starts at the beginning). |
| `--print-timeout` | — | `str` | `"15m0s"` | Execution timeout passed directly to `agy -p` (e.g. `"10m0s"`, `"20m0s"`). |
| `--model` | — | `str` | `None` | Model override passed to `agy --model` (e.g. `gemini-2.5-pro`). If omitted, uses Antigravity's configured default model. |
| `--keep-scratch` | — | flag | `False` | When set, disables automatic purging of `~/.gemini/antigravity-cli/scratch` before trials to preserve existing scratch files. |
| `-h` | `--help` | flag | — | Displays the command-line help message and exits. |

> [!NOTE]
> `--task-index` (`-i`) and `--num-tasks` (`-m`) cannot be specified simultaneously. To run a contiguous range of tasks, combine `--start-index` and `--num-tasks`.

---

### Usage Examples

#### 1. Default Benchmark Run
Run all greenfield tasks from [`input/nl_instruction_inputs.jsonl`](file:///Users/luis/Code/Thesis_Implementation/input/nl_instruction_inputs.jsonl) with 3 samples per task:
```bash
uv run evaluate_pass_at_k.py
```

#### 2. Run Single Task by Index
Execute only the first task (index `0`) with 5 samples and calculate $pass@1$, $pass@3$, and $pass@5$:
```bash
uv run evaluate_pass_at_k.py -i 0 -n 5 -k 1 3 5
```

#### 3. Task Slicing / Batching
Run tasks 3 through 6 (4 tasks starting at index `2`):
```bash
uv run evaluate_pass_at_k.py --start-index 2 -m 4
```

#### 4. Brownfield Project Evaluation
Run the evaluation against existing project repositories (e.g. COSC336 Java assignments):
```bash
uv run evaluate_pass_at_k.py \
  --inputs input/COSC336-Assignments \
  --output-dir eval_results/cosc336 \
  -n 3 -k 1 3
```

#### 5. Combined Inputs (Greenfield & Brownfield)
Evaluate multiple inputs in a single benchmark suite:
```bash
uv run evaluate_pass_at_k.py \
  --inputs input/nl_instruction_inputs.jsonl input/AI-Assignments input/COSC336-Assignments \
  --output-dir eval_results/full_suite \
  -n 3 -k 1 3
```

#### 6. Custom Model & Extended Timeout
Override the model and timeout:
```bash
uv run evaluate_pass_at_k.py \
  --model gemini-2.5-pro \
  --print-timeout 20m0s \
  -n 3 -k 1 3
```

---

### Task Types Supported

1. **Greenfield Tasks (`.jsonl`)**:
   - Input format: JSON Lines containing `instruction` (prompt text), `dependency_list` (list of expected CLI tool binaries), and optional `track` (e.g., `computer science`, `data science`).
   - The harness creates an empty git repository in an isolated workspace, prompts the agent to generate a Nix flake for the instruction, and verifies that the generated `devShell` contains all required binaries.

2. **Brownfield Tasks (Project Directories)**:
   - Input format: Paths to directories containing existing source code (e.g. Java, Python, Rust, C++).
   - Scans projects and submodules using `detect-project-requirements.py`.
   - Copies code into an isolated workspace (clearing prior `.git`, `flake.nix`, build artifacts).
   - Initializes a fresh git repository and prompts the agent to migrate the codebase to Nix flake development environments.
   - Evaluates whether each module's `flake.nix` builds, activates, and supplies necessary language toolchains.

---

### Evaluation Pipeline & Verification Criteria

For every sample, the harness executes:
```
Isolated Workspace Setup -> Agent Invocation (`agy -p ...`) -> Artifact Collection -> 3-Stage Verification
```

Verification checks:
1. **Flake Syntax & Purity**: Runs `nix flake check --extra-experimental-features "nix-command flakes"` (with `NIXPKGS_ALLOW_UNFREE=1`).
2. **Environment Activation**: Runs `nix develop --command true` to ensure the derivation builds and shell hooks run without failure.
3. **Tool Assertion**: For each required tool binary $T$, runs `nix develop --command sh -c "command -v $T"` inside the shell to ensure binaries are correctly exported to `PATH`.

Unbiased $pass@k$ is computed using the standard HumanEval formulation:
$$\text{pass@}k = \mathbb{E}\left[1 - \frac{\binom{n - c}{k}}{\binom{n}{k}}\right]$$
where $n$ is the total samples per task and $c$ is the number of passing samples.

---

## RQ2: Clean-Host Reproducibility Replay

RQ2 asks whether environments that passed the host-side RQ1 verifier reproduce on a clean Linux system. The replay harness uses a pinned, unmounted `aarch64-linux` NixOS guest managed by Lima. It replays only samples that passed RQ1 and contain both `flake.nix` and `flake.lock`; for the current `20260929_001840` run, that cohort contains 41 samples.

The guest is prepared once and saved as a `clean-baseline` snapshot. Before every sample, the harness restores that snapshot, transfers a compressed copy of the trial with `limactl copy`, and unpacks it into guest-local `/tmp/thesis-clean-eval` storage. The guest therefore has no mounted project directory, host Nix store, or state left by an earlier replay. Network access remains available so the first-use environment can retrieve the flake's pinned inputs and cached packages; network failures are recorded separately instead of being treated as invalid configurations.

For every replayed sample, the harness runs:

1. `nix flake check` with the original lock file and lock-file writes disabled.
2. `nix develop --command true` to verify shell activation.
3. A `command -v` assertion for each tool required by the RQ1 benchmark.
4. A curated, task-specific headless command list from [`config/clean_vm_tasks.json`](config/clean_vm_tasks.json), such as compiler version checks, builds, or language-specific tests when a project manifest is present.

GUI workflows, interactive credential prompts, and persistent database-service setup are outside the headless metric. They are documented per task in the manifest. The result for each sample is classified as `reproduced`, `flake_failure`, `activation_failure`, `missing_dependency`, `functional_failure`, or `infrastructure_failure`.

### Running RQ2

Install [Lima](https://lima-vm.io/) so `limactl` is available, then prepare the clean guest and baseline snapshot:

```bash
uv run scripts/replay_clean_vm.py prepare
```

Replay a completed RQ1 run:

```bash
uv run scripts/replay_clean_vm.py run \
  --source-run eval_results/20260929_001840
```

The replay writes a new timestamped directory under `eval_results/clean_vm/`; it never changes the source RQ1 run. Its `clean_vm_summary.json` reports the clean-host reproduction rate as `reproduced / eligible locally passing trials`, while `clean_vm_report.md`, `clean_vm_trials.csv`, and per-command logs provide the evidence behind each outcome. Stop or explicitly remove the guest after the run:

```bash
uv run scripts/replay_clean_vm.py teardown
uv run scripts/replay_clean_vm.py teardown --delete
```

See [`docs/clean-vm-replay.md`](docs/clean-vm-replay.md) for the same operational procedure.

---

## Results & Artifact Structure

Outputs are organized into isolated, timestamped directories under `--output-dir` (default: `eval_results/<YYYYMMDD_HHMMSS>/`), ensuring consecutive runs never overwrite prior task samples:

```text
eval_results/
├── latest -> 20260928_130512          # Symlink to the most recent evaluation run
├── benchmark_summary.json             # Convenience copy of latest summary data (JSON)
├── benchmark_report.md                # Convenience copy of latest markdown report
└── 20260928_130512/                   # Isolated run directory titled with run timestamp
    ├── benchmark_summary.json         # Run benchmark summary data (JSON)
    ├── benchmark_report.md            # Run formatted markdown report
    ├── tool_call_frequency.csv        # Overall tool call frequency & trial prevalence
    ├── tool_call_frequency_by_trial.csv # Per-trial tool call breakdown matrix
    ├── tool_call_frequency_by_task.csv  # Per-task aggregated tool call breakdown
    ├── run_command_frequency.csv      # Exact shell command execution frequency
    ├── run_command_base_frequency.csv # Base executable frequency (e.g. nix, git, python3)
    ├── run_command_log.csv            # Sequential log of every command executed across trials
    └── task_XX/
        ├── sample_00/
        │   ├── flake.nix              # Generated Nix flake
        │   ├── flake.lock             # Generated Nix lockfile
        │   ├── trial_meta.json        # Outcome, runtime, turn count, token usage
        │   ├── agent_response.md      # Final markdown response from Antigravity
        │   └── transcript.jsonl       # Complete step-by-step agent trajectory
        ├── sample_01/
        └── sample_02/
```

> [!TIP]
> Each trial records its Antigravity conversation ID in `trial_meta.json` and the markdown report. You can inspect or resume any trial directly in your terminal using:
> ```bash
> agy --conversation <conversation_id>
> ```

---

## Telemetry & Tool Call Reporting Scripts

Telemetry statistics (`tool_call_frequency*.csv` and `run_command_*.csv`) are automatically generated and updated inside each run directory upon task completion. 

You can also run or re-run the reporting scripts in [`scripts/`](file:///Users/luis/Code/Thesis_Implementation/scripts/) manually on any specific evaluation directory:

### Tool Call Frequency Analysis

Run [`scripts/generate_tool_call_report.py`](file:///Users/luis/Code/Thesis_Implementation/scripts/generate_tool_call_report.py) (defaults to `eval_results/latest` or target folder):
```bash
uv run scripts/generate_tool_call_report.py [optional_path_to_run_dir]
```
Generated CSVs:
- `tool_call_frequency.csv`: Overall tool call counts, percentage of total calls, trial prevalence (how many trials used the tool), and mean calls per trial.
- `tool_call_frequency_by_trial.csv`: Matrix of tool call invocations broken down per task and sample.
- `tool_call_frequency_by_task.csv`: Aggregated tool call distribution per task.

### Executed Command Frequency Analysis

Run [`scripts/generate_run_command_report.py`](file:///Users/luis/Code/Thesis_Implementation/scripts/generate_run_command_report.py) (defaults to `eval_results/latest` or target folder):
```bash
uv run scripts/generate_run_command_report.py [optional_path_to_run_dir]
```
Generated CSVs:
- `run_command_frequency.csv`: Exact shell commands executed by the agent, sorted by frequency.
- `run_command_base_frequency.csv`: Base executable frequency (e.g. `nix`, `git`, `python3`, `cat`).
- `run_command_log.csv`: Chronological log of every command executed across all benchmark trials with working directory, timestamp, and step index.

---

## Interactive Prompt Runner

For manual, interactive step-through of instructions in [`input/nl_instruction_inputs.jsonl`](file:///Users/luis/Code/Thesis_Implementation/input/nl_instruction_inputs.jsonl), use [`input/run_instructions.sh`](file:///Users/luis/Code/Thesis_Implementation/input/run_instructions.sh):

```bash
./input/run_instructions.sh [optional_path_to_jsonl]
```
This script iterates through instructions, invokes `agy -i` in interactive mode, and prompts before proceeding to the next instruction.

---

## Benchmark Datasets & Workloads

The `input/` directory provides diverse evaluation workloads:

| Dataset / Path | Type | Description |
| :--- | :---: | :--- |
| [`input/nl_instruction_inputs.jsonl`](file:///Users/luis/Code/Thesis_Implementation/input/nl_instruction_inputs.jsonl) | Greenfield | 14 natural language instructions spanning Java JDK 17/VS Code, Flutter/Dart, Python 3.12/uv, GCC/Clang C/C++, Node.js LTS, Rust, Go, .NET SDK, Ruby/Bundler, R, RStudio, MySQL Server, MySQL Workbench. |
| [`input/COSC336-Assignments`](file:///Users/luis/Code/Thesis_Implementation/input/COSC336-Assignments) | Brownfield | Java data structures and graph algorithms (Assignment 7 graph processing, adjacency lists). |
| [`input/Neural_Network_Course`](file:///Users/luis/Code/Thesis_Implementation/input/Neural_Network_Course) | Brownfield | PyTorch and Python machine learning projects (Project 3 TV script generation with `uv.lock` and Jupyter notebooks). |
| [`input/AI-Assignments`](file:///Users/luis/Code/Thesis_Implementation/input/AI-Assignments) | Brownfield | Multi-assignment artificial intelligence coursework codebase. |
| [`input/flutter-dev-env`](file:///Users/luis/Code/Thesis_Implementation/input/flutter-dev-env) | Brownfield | Mobile development project environment. |
| [`input/java17-vscode-env`](file:///Users/luis/Code/Thesis_Implementation/input/java17-vscode-env) | Brownfield | Java 17 enterprise & editor tooling configuration. |

---

## Development Environment

### Local Development via Devenv
This repository uses [devenv](https://devenv.sh/) to provide Nix and schema tools (`nixfmt`, `jq`, `d2`, `nixd`):
```bash
devenv shell
```
Or if using `direnv`:
```bash
direnv allow
```
