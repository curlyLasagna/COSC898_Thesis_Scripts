{
  description = "Rust development environment with rustup, rustc, and cargo";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            cargo
            rustc
            rustup
            git
          ];

          RUST_BACKTRACE = "1";

          shellHook = ''
            echo "Entering environment for Rust (rustup, rustc, cargo)"
            echo "rustc: $(rustc --version 2>&1)"
            echo "cargo: $(cargo --version 2>&1)"
            echo "rustup: $(rustup --version 2>&1 | head -n 1)"
          '';
        };

        formatter = pkgs.nixfmt-rfc-style;
      }
    );
}
