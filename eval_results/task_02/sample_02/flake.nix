{
  description = "Python 3.12 and uv development environment with Flask and Flask-RESTful";

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
            python312
            uv
            git
          ];

          UV_PYTHON_PREFERENCE = "only-system";

          shellHook = ''
            echo "Entering environment for Python 3.12 + uv"
            echo "Python: $(python3 --version)"
            echo "uv: $(uv --version)"

            if [ -d ".venv" ]; then
              source .venv/bin/activate
            fi
          '';
        };

        formatter = pkgs.nixfmt-rfc-style;
      }
    );
}
