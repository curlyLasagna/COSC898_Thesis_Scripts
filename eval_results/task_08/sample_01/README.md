# .NET SDK Development Environment

Reproducible development environment providing the full .NET SDK and runtime using Nix Flakes.

## Getting Started

1. Enter the Nix development environment:
   ```bash
   nix develop
   ```

2. Verify .NET SDK installation:
   ```bash
   dotnet --info
   ```

3. Restore dependencies and build the project:
   ```bash
   dotnet restore
   dotnet build
   ```

4. Run the project:
   ```bash
   dotnet run
   ```
