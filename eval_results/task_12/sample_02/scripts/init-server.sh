#!/usr/bin/env bash
set -euo pipefail

BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.mysql"
DATADIR="$BASEDIR/data"
CNF="$BASEDIR/my.cnf"

mkdir -p "$BASEDIR"

if [ ! -f "$CNF" ]; then
  cat << EOF > "$CNF"
[mysqld]
datadir=$DATADIR
socket=$BASEDIR/mysql.sock
pid-file=$BASEDIR/mysql.pid
log-error=$BASEDIR/mysqld.log
port=3308
bind-address=127.0.0.1
mysqlx=0

[client]
socket=$BASEDIR/mysql.sock
port=3308
EOF
fi

if [ -d "$DATADIR" ] && [ "$(ls -A "$DATADIR" 2>/dev/null)" ]; then
  echo "MySQL data directory already initialized at $DATADIR"
  exit 0
fi

echo "Initializing MySQL data directory in $DATADIR..."
mkdir -p "$DATADIR"
mysqld --defaults-file="$CNF" --initialize-insecure
echo "MySQL initialized successfully. (Root user created with empty password)."
