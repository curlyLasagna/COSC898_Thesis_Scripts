#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOCK="$DIR/.mysql/mysql.sock"

PASSWORD="${1:-}"

if [ -n "$PASSWORD" ]; then
  mysql --socket="$SOCK" -u root -p"$PASSWORD" -e "SELECT VERSION();"
else
  mysql --socket="$SOCK" -u root -p -e "SELECT VERSION();"
fi
