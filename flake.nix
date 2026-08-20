{
  description = "Dev shells for CS + data-science toolchains (Java/Flutter/Python/C/C++/Node/Rust/Go/.NET/R/MySQL + optional GUIs)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true; # e.g. vscode

            # Some GUI dev tools depend on Electron versions that are sometimes
            # marked insecure after EOL in nixpkgs-unstable.
            permittedInsecurePackages = [
              "electron-38.8.4"
            ];
          };
        };

        jdk = pkgs.openjdk17;
        lib = pkgs.lib;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = (
            with pkgs;
            [
              # Common tooling
              git

              # Java (JDK 17) + build
              jdk
              maven

              # Flutter / Dart
              flutter
              dart

              # Python 3.12 + uv
              python312
              uv

              # C/C++ toolchains + build tools
              gcc
              clang
              cmake
              gnumake
              pkg-config

              # Node.js (LTS)
              nodejs_20

              # Rust
              rustup
              rustc
              cargo

              # Go
              go

              # .NET SDK
              dotnet-sdk_8

              # Ruby + Bundler
              ruby
              bundler

              # R
              R

              # MySQL server + client
              mysql84
            ]
          );

          shellHook = ''
            export JAVA_HOME="${jdk}"
            export PATH="$JAVA_HOME/bin:$PATH"
          '';
        };

        # Optional GUI tools (can be large and/or platform-limited).
        devShells.gui = pkgs.mkShell {
          packages =
            (with pkgs; [
              vscode
              rstudio
            ])
            ++ lib.optionals pkgs.stdenv.isLinux (
              with pkgs;
              [
                mysql-workbench
              ]
            );

          shellHook = ''
            export JAVA_HOME="${jdk}"
            export PATH="$JAVA_HOME/bin:$PATH"
          '';
        };
      }
    );
}
