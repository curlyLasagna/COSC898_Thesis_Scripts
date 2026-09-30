#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOCK="$DIR/.mysql/mysql.sock"

NEW_PASSWORD="${1:-}"

if [ -z "$NEW_PASSWORD" ]; then
  read -s -p "Enter new MySQL root password: " NEW_PASSWORD
  echo ""
fi

if [ -z "$NEW_PASSWORD" ]; then
  echo "Error: Password cannot be empty."
  exit 1
fi

echo "Setting root password..."
if mysql --socket="$SOCK" -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$NEW_PASSWORD'; FLUSH PRIVILEGES;" 2>/dev/null; then
  echo "Root password updated successfully!"
else
  echo "Direct update failed (a password might already be set). Prompting for current password..."
  mysql --socket="$SOCK" -u root -p -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$NEW_PASSWORD'; FLUSH PRIVILEGES;"
  echo "Root password updated successfully!"
fi
