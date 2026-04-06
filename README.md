# Rust Development Environment with MySQL

This project uses [Nix Flakes](https://nixos.wiki/wiki/Flakes) to provide a reproducible development environment with Rust and MySQL.

## Prerequisites

- [Nix package manager](https://nixos.org/download.html) with flakes enabled

To enable flakes, add the following to your Nix configuration (`~/.config/nix/nix.conf` or `/etc/nix/nix.conf`):

```
experimental-features = nix-command flakes
```

## Getting Started

### Enter the Development Shell

```bash
nix develop
```

This command downloads and configures all necessary tools. The first run may take a few minutes.

### Available Tools

| Tool | Version | Description |
|------|---------|-------------|
| `rustc` | 1.94.0 | Rust compiler |
| `cargo` | 1.94.0 | Rust package manager |
| `clippy` | 1.94.0 | Rust linter |
| `rustfmt` | 1.94.0 | Rust code formatter |
| `rust-analyzer` | - | Rust language server for IDE support |
| `mysql` | 8.4.8 | MySQL database server and client |
| `sqlx-cli` | 0.8.6 | SQLx database CLI (migrations, queries) |
| `diesel-cli` | 2.3.7 | Diesel ORM CLI (migrations, schema) |

### Build Dependencies

The environment includes these build dependencies required by various Rust crates:

- `pkg-config` - Helper tool for compiling applications
- `openssl` - TLS/SSL library

**macOS-specific dependencies** (automatically included on Darwin systems):
- `apple-sdk_15` - Apple SDK for macOS development
- `libiconv` - Character encoding conversion library

## Environment Variables

The following environment variables are automatically set when entering the shell:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | `mysql://root:root@localhost:3306/devdb` | MySQL connection string |
| `RUST_BACKTRACE` | `1` | Enables Rust backtraces for debugging |

## MySQL Setup

MySQL is available but not running by default. Follow these steps to set up a local MySQL instance:

### 1. Initialize the Database

Create a data directory and initialize MySQL:

```bash
mysqld --initialize-insecure --datadir=./mysqldata
```

> **Note:** `--initialize-insecure` creates a root user without a password. For development only.

### 2. Start MySQL Server

```bash
mysqld --datadir=./mysqldata --socket=./mysql.sock &
```

This starts MySQL in the background using a Unix socket file in the current directory.

### 3. Connect to MySQL

```bash
mysql -u root --socket=./mysql.sock
```

### 4. Create the Development Database

Once connected to MySQL:

```sql
CREATE DATABASE devdb;
```

### 5. Stop MySQL Server

```bash
mysqladmin -u root --socket=./mysql.sock shutdown
```

## Using SQLx

[SQLx](https://github.com/launchbadge/sqlx) is a compile-time checked SQL toolkit.

### Create a Migration

```bash
sqlx migrate add <migration_name>
```

### Run Migrations

```bash
sqlx migrate run
```

### Prepare for Offline Mode

```bash
cargo sqlx prepare
```

## Using Diesel

[Diesel](https://diesel.rs/) is a safe, extensible ORM and query builder.

### Setup Diesel

```bash
diesel setup
```

### Generate a Migration

```bash
diesel migration generate <migration_name>
```

### Run Migrations

```bash
diesel migration run
```

### Print Schema

```bash
diesel print-schema
```

## Common Rust Commands

```bash
# Build the project
cargo build

# Run the project
cargo run

# Run tests
cargo test

# Check code without building
cargo check

# Lint with Clippy
cargo clippy

# Format code
cargo fmt
```

## IDE Support

`rust-analyzer` is included for IDE integration. Configure your editor to use the rust-analyzer from the Nix shell:

**VS Code:** Install the "rust-analyzer" extension. It should automatically detect the toolchain.

**Neovim/Vim:** Use a LSP client like `nvim-lspconfig` with rust-analyzer.

## Troubleshooting

### "MySQL socket file not found"

Ensure MySQL is running and the socket path matches:

```bash
ls ./mysql.sock
```

### "Permission denied" on MySQL data directory

Remove and reinitialize the data directory:

```bash
rm -rf ./mysqldata
mysqld --initialize-insecure --datadir=./mysqldata
```

### Changes to `flake.nix` not taking effect

Exit the shell and re-enter:

```bash
exit
nix develop
```

### Verify the flake

```bash
nix flake check
```

## Project Structure

```
.
├── flake.nix          # Nix flake configuration
├── flake.lock         # Locked dependency versions
├── README.md          # This file
├── mysqldata/         # MySQL data directory (gitignored)
└── mysql.sock         # MySQL socket file (gitignored)
```

## Additional Resources

- [Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [SQLx Documentation](https://docs.rs/sqlx/latest/sqlx/)
- [Diesel Documentation](https://diesel.rs/guides/)
- [MySQL 8.4 Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/)
- [Nix Flakes Wiki](https://nixos.wiki/wiki/Flakes)
