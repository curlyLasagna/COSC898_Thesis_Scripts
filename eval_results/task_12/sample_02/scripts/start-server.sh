#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASEDIR="$DIR/.mysql"
DATADIR="$BASEDIR/data"
CNF="$BASEDIR/my.cnf"
PIDFILE="$BASEDIR/mysql.pid"
SOCK="$BASEDIR/mysql.sock"
LOGFILE="$BASEDIR/mysqld.log"

if [ ! -d "$DATADIR" ] || [ -z "$(ls -A "$DATADIR" 2>/dev/null)" ]; then
  "$DIR/scripts/init-server.sh"
fi

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "MySQL is already running (PID: $(cat "$PIDFILE"))."
  exit 0
fi

echo "Starting MySQL server daemon..."
mysqld --defaults-file="$CNF" &
SERVER_PID=$!

echo "Waiting for MySQL server to be ready on socket $SOCK..."
attempts=0
while ! mysqladmin --socket="$SOCK" ping 2>/dev/null; do
  sleep 0.3
  attempts=$((attempts + 1))
  if [ $attempts -ge 30 ]; then
    echo "Error: Timed out waiting for MySQL server to start."
    echo "Check error log at: $LOGFILE"
    exit 1
  fi
done

echo "MySQL server started successfully (PID: $SERVER_PID, Port: 3308)."
