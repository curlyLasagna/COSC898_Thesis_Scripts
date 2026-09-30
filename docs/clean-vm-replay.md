# Clean NixOS Replay

This experiment tests whether flakes that passed the host-side RQ1 verifier also
work on a fresh `aarch64-linux` NixOS guest. It does not modify the source RQ1
run or mount it into the guest.

## Prerequisites

Install Lima so `limactl` is available on the host. The guest image and digest
are pinned in `vm/nixos-clean-eval.yaml`. The initial target is Apple Silicon;
the replay runner records the guest system in its summary.

## Run the experiment

Prepare the unmounted guest and save the baseline snapshot once:

```bash
uv run scripts/replay_clean_vm.py prepare
```

Replay every locally passing artifact from the selected RQ1 run:

```bash
uv run scripts/replay_clean_vm.py run \
  --source-run eval_results/20260929_001840
```

Each sample restores `clean-baseline`, transfers an archive through `limactl
copy`, unpacks it beneath `/tmp/thesis-clean-eval`, and runs the same flake
checks from guest-local storage. The command writes a new timestamped directory
under `eval_results/clean_vm/` with JSON, CSV, Markdown, and per-command logs.

The task-specific commands and documented exclusions are in
`config/clean_vm_tasks.json`. GUI workflows, interactive credentials, and
persistent database-service setup are excluded from the headless metric.

Stop the guest when finished, or remove it and its snapshot explicitly:

```bash
uv run scripts/replay_clean_vm.py teardown
uv run scripts/replay_clean_vm.py teardown --delete
```

Run the local harness checks with:

```bash
uv run python -m unittest tests/test_replay_clean_vm.py -v
```
