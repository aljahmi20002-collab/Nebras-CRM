#!/usr/bin/env bash
# One-command NebrasCRM launcher for a native local MySQL or MariaDB server.
# Usage: ./run-mysql.sh  (or PORT=9000 ./run-mysql.sh)
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

CONFIG_FILE="${MYSQL_LOCAL_ENV:-$SCRIPT_DIR/.env.mysql.local}"
# Existing native MariaDB installations can use this one-command launcher too.
if [ ! -f "$CONFIG_FILE" ] && [ -f "$SCRIPT_DIR/.env.mariadb.local" ]; then
  CONFIG_FILE="$SCRIPT_DIR/.env.mariadb.local"
fi
if [ ! -f "$CONFIG_FILE" ]; then
  cp .env.mysql.local.example .env.mysql.local
  chmod 600 .env.mysql.local
  echo "▶ تم إنشاء .env.mysql.local. عدّل كلمة مرور MySQL ثم شغّل ./run-mysql.sh مرة أخرى." >&2
  exit 1
fi

# The config file contains only local CRM_DB_* exports. Keep it private and do
# not commit it.
# shellcheck disable=SC1090
source "$CONFIG_FILE"

case "${CRM_DB_ENGINE:-}" in
  mysql|mariadb) ;;
  *)
    echo "✗ يجب أن يضبط $CONFIG_FILE قيمة CRM_DB_ENGINE=mysql أو mariadb." >&2
    exit 1
    ;;
esac

# Try the common native service names. A server already configured to start at
# boot is left untouched; a failed start is followed by run.sh's full preflight.
if command -v systemctl >/dev/null 2>&1 \
   && ! systemctl is-active --quiet mysql \
   && ! systemctl is-active --quiet mariadb \
   && ! systemctl is-active --quiet mysqld; then
  echo "▶ محاولة تشغيل خدمة MySQL/MariaDB المحلية..."
  sudo systemctl start mysql 2>/dev/null \
    || sudo systemctl start mariadb 2>/dev/null \
    || sudo systemctl start mysqld 2>/dev/null \
    || true
fi

# Invoke Bash explicitly so this launcher works after ZIP extraction even if
# executable bits were removed from run.sh.
exec bash "$SCRIPT_DIR/run.sh"
