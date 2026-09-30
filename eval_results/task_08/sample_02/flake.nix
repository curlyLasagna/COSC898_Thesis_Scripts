{
  description = ".NET SDK development environment";

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
            dotnet-sdk
            git
          ];

          DOTNET_ROOT = "${pkgs.dotnet-sdk}";
          DOTNET_CLI_TELEMETRY_OPTOUT = "1";

          shellHook = ''
            echo "Entering environment for .NET SDK"
            echo "dotnet: $(dotnet --version)"
          '';
        };

        formatter = pkgs.nixfmt-rfc-style;
      }
    );
}
