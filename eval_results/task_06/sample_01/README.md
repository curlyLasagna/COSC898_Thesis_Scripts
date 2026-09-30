# Rust Development Environment

A reproducible development environment providing `rustup`, `rustc`, and `cargo` via Nix flakes.

## Environment Activation

Enter the reproducible Nix development shell:
```bash
nix develop
```

## Verify Installed Tools

Verify that `rustc`, `cargo`, and `rustup` are available:
```bash
rustc --version
cargo --version
rustup --version
```

## Build and Run

Build the starter project:
```bash
cargo build
```

Run the compiled executable:
```bash
cargo run
# or directly:
./target/debug/rust_starter
```
