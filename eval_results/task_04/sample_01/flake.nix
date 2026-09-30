{
  description = "Clang (C/C++) and build tools development environment";

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
            clang
            gnumake
            cmake
            git
          ];

          shellHook = ''
            export CC=clang
            export CXX=clang++

            echo "Entering environment for Clang (C/C++) and build tools"
            echo "clang: $(clang --version 2>&1 | head -n 1)"
            echo "clang++: $(clang++ --version 2>&1 | head -n 1)"
            echo "cmake: $(cmake --version 2>&1 | head -n 1)"
            echo "make: $(make --version 2>&1 | head -n 1)"
          '';
        };

        formatter = pkgs.nixfmt-rfc-style;
      }
    );
}
