{
  description = "Node.js (LTS) Development Environment";

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
            nodejs_22
            git
          ];

          shellHook = ''
            echo "Entering environment for Node.js (LTS) Development"
            echo "Node.js version: $(node --version 2>&1)"
            echo "npm version:     $(npm --version 2>&1)"
          '';
        };

        formatter = pkgs.nixfmt-rfc-style;
      }
    );
}
