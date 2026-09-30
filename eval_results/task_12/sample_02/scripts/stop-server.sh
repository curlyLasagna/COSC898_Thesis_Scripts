#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOCK="$DIR/.mysql/mysql.sock"
PIDFILE="$DIR/.mysql/mysql.pid"

PASSWORD="${1:-}"

echo "Shutting down MySQL server..."
if [ -n "$PASSWORD" ]; then
  mysqladmin --socket="$SOCK" -u root -p"$PASSWORD" shutdown 2>/dev/null && echo "MySQL server stopped." && exit 0
fi

if mysqladmin --socket="$SOCK" -u root shutdown 2>/dev/null; then
  echo "MySQL server stopped."
  exit 0
fi

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Sent SIGTERM to MySQL server (PID: $PID)."
    exit 0
  fi
fi

echo "MySQL server is not running."
