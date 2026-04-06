{
  description = "Rust development environment with MySQL";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs =
            with pkgs;
            [
              # Rust toolchain
              rustc
              cargo
              clippy
              rustfmt
              rust-analyzer

              # MySQL
              mysql84

              # Useful CLI tools for database work
              sqlx-cli
              diesel-cli

              # Build dependencies (needed for some Rust crates)
              pkg-config
              openssl
            ]
            ++ pkgs.lib.optionals pkgs.stdenv.isDarwin [
              # macOS specific dependencies
              apple-sdk_15
              libiconv
            ];

          # Environment variables
          env = {
            # MySQL connection string (customize as needed)
            DATABASE_URL = "mysql://root:root@localhost:3306/devdb";

            # Rust backtrace for better error messages
            RUST_BACKTRACE = "1";
          };

          shellHook = ''
            echo "🦀 Rust development environment with MySQL"
            echo ""
            echo "Available tools:"
            echo "  rustc     - $(rustc --version)"
            echo "  cargo     - $(cargo --version)"
            echo "  clippy    - $(cargo clippy --version)"
            echo "  rustfmt   - $(rustfmt --version)"
            echo "  mysql     - $(mysql --version)"
            echo "  sqlx      - $(sqlx --version 2>/dev/null || echo 'installed')"
            echo "  diesel    - $(diesel --version 2>/dev/null || echo 'installed')"
            echo ""
            echo "MySQL tips:"
            echo "  Init:     mysqld --initialize-insecure --datadir=./mysqldata"
            echo "  Start:    mysqld --datadir=./mysqldata --socket=./mysql.sock &"
            echo "  Connect:  mysql -u root --socket=./mysql.sock"
            echo "  Stop:     mysqladmin -u root --socket=./mysql.sock shutdown"
            echo ""
            echo "DATABASE_URL: $DATABASE_URL"
          '';
        };
      }
    );
}
