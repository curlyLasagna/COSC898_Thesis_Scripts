# Nix dev shells

This repo provides two Nix dev shells:

## `default` (CLI toolchains)

Includes: JDK 17 (+ Maven), Flutter/Dart, Python 3.12 + `uv`, GCC/Clang + CMake/Make, Node.js LTS, Rust (`rustup`/`rustc`/`cargo`), Go, .NET SDK 8, Ruby + Bundler, R, MySQL server/client.

Enter:

```bash
NIXPKGS_ALLOW_UNFREE=1 nix develop
```

## `gui` (optional GUIs)

Includes: VS Code, RStudio, and (Linux only) MySQL Workbench.

Enter:

```bash
NIXPKGS_ALLOW_UNFREE=1 nix develop .#gui
```

## Notes

- `JAVA_HOME` is set to the JDK 17 directory and `$JAVA_HOME/bin` is added to `PATH`.
- Unfree packages are enabled (`allowUnfree = true`) for things like VS Code.
- This flake permits an Electron version that nixpkgs may mark insecure (`electron-38.8.4`) to keep some GUI tooling evaluatable on unstable.
- Platform caveat: `mysql-workbench` is not available on `aarch64-darwin`, so it is only included on Linux.
