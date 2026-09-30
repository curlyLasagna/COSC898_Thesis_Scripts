# .NET SDK Development Environment

This repository provides a reproducible development environment for .NET SDK projects managed via Nix Flakes.

## Requirements

- [Nix](https://nixos.org/download.html) with Flakes enabled.

## Quickstart

To enter the isolated .NET SDK environment:

```bash
nix develop
```

## Included Tooling

- .NET SDK (`pkgs.dotnet-sdk` v8.0)
- Git (`pkgs.git`)

## Building and Running

```bash
# Verify .NET environment and SDK
dotnet --info

# Restore dependencies
dotnet restore

# Build project
dotnet build

# Run application
dotnet run
```
