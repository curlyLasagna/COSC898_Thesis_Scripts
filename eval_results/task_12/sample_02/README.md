# MySQL Server & Client Development Environment

A reproducible Nix flake development shell providing MySQL 8.4 Server and Client (`mysqld`, `mysql`, `mysqladmin`) configured for user-space, rootless operation.

---

## Quick Start

### 1. Enter the Environment
```bash
nix develop
```

### 2. Start MySQL Server
Initializes `.mysql/data` on first run and starts `mysqld` daemon:
```bash
mysql-start
# or ./scripts/start-server.sh
```

### 3. Set Root Password
```bash
mysql-set-password 'YourSecurePasswordHere'
# or ./scripts/set-root-password.sh 'YourSecurePasswordHere'
```

### 4. Connect & Verify
Connect with the `mysql` client:
```bash
mysql -u root -p
```
Enter your password, then run:
```sql
SELECT VERSION();
```

Expected output:
```text
+-----------+
| VERSION() |
+-----------+
| 8.4.11    |
+-----------+
1 row in set (0.00 sec)
```

Exit the client:
```sql
EXIT;
```

### 5. Stop MySQL Server
```bash
mysql-stop
# or ./scripts/stop-server.sh
```

---

## Configuration Details
- **Data directory**: `.mysql/data`
- **Socket**: `.mysql/mysql.sock` (set via `$MYSQL_UNIX_PORT`)
- **Port**: `3308` (avoids conflict with default port 3306)
- **Error Log**: `.mysql/mysqld.log`
- **Config file**: `.mysql/my.cnf`
