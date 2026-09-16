# CS environment benchmark suite

This repository compares development-environment overhead for two representative
computer-science workloads. The suite deliberately avoids IDE extensions,
services, background processes, and unrelated toolchains so resource
measurements reflect the selected environment and workload.

| Profile | Workload | Toolchain |
| --- | --- | --- |
| `java-graph` | COSC336 Assignment 7 graph processing | JDK 17 |
| `nn-project3` | COSC 750 Project 3 script generation | Python 3.13, `uv` 0.11.6, CPU PyTorch |

The Python environment is resolved from
`input/Neural_Network_Course/Project3/uv.lock`. Project 3 uses CPU PyTorch on
Linux and PyPI's native macOS build, so the suite does not download CUDA
runtimes or require an NVIDIA GPU.

## Nix flake

Enter the profile you want to measure:

```bash
nix develop .#java-graph
nix develop .#nn-project3
```

Verify the flake without entering a shell:

```bash
nix flake check
```

## Dev Container

Open this repository in a Dev Containers-compatible editor and choose **Reopen
in Container**, or build it with the Dev Containers CLI. The container uses
Ubuntu 24.04 and includes headless JDK 17, `uv` 0.11.6, and a `uv`-managed
Python 3.13.

It intentionally has no post-create dependency installation. Run the setup
command you want included in your measurement after the container has started.

## Native baseline

Bootstrap only the selected host-level tools:

```bash
./scripts/bootstrap-native.sh java-graph
./scripts/bootstrap-native.sh nn-project3
```

The script supports macOS with Homebrew and Ubuntu. It does not run `uv sync`,
so dependency-resolution timing remains separate from bootstrap timing.

## Workload commands

Run these commands from the repository root after entering the matching
environment. They are examples and are not a measurement harness.

### Java graph processing

```bash
workload_dir='input/COSC336-Assignments/Assignment 7'
classes_dir="$(mktemp -d)"
javac -d "$classes_dir" "$workload_dir"/Adj_List_Graph.java "$workload_dir"/Text_Adj.java
(cd "$workload_dir" && java -cp "$classes_dir" assignment7.Text_Adj)
```

### Neural-network script generation

```bash
cd input/Neural_Network_Course/Project3
uv sync --locked
uv run python -c 'import torch, torchvision; print(torch.__version__); assert not torch.cuda.is_available()'
uv run jupyter nbconvert --to notebook --execute --inplace tv_script_generation.ipynb
```

The notebook execution updates the notebook file. For repeatable runs, copy it
to a disposable location first or reset that file between trials.

## Measurement boundaries

Measure provisioning/build, dependency synchronization, idle state, and
workload execution as separate phases. Clear or retain caches consistently
across trials and record the OS, CPU architecture, memory allocation, tool
versions, and cache state. On macOS, Docker Desktop runs the Dev Container in a
Linux VM, whereas native and Nix shells run on the host; report that
virtualization boundary with the results.

### Storage measurements

Measure the environment closure/image separately from dependency caches and
the checkout. For the Nix profile, build the development-shell derivation, then
inspect its store closure:

```bash
nix build .#devShells.$(nix eval --impure --raw --expr builtins.currentSystem).nn-project3
nix path-info --closure-size --human-readable ./result
```

For the Java profile, replace `nn-project3` with `java-graph`. `--closure-size`
reports the deduplicated Nix-store closure; `nix path-info -rSh ./result` lists
the individual store paths when a breakdown is useful.

After rebuilding the Dev Container, use Docker's storage report and the actual
container writable layer:

```bash
docker image ls
docker system df -v
docker ps -a --filter label=devcontainer.local_folder="$PWD"
docker container inspect <container-id> --size --format '{{.SizeRootFs}} {{.SizeRw}}'
```

Record Docker's logical image `SIZE`, its `UNIQUE SIZE` from `docker system
df -v`, the read-only image layers (`SizeRootFs`), and the writable layer
(`SizeRw`) separately. Docker Desktop's VM disk and shared base layers are
implementation overhead; do not compare its total virtual-disk allocation
directly to the Nix closure size.
