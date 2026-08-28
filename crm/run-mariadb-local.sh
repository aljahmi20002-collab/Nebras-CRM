#!/usr/bin/env bash
# Run NebrasCRM against a native/local MariaDB service (not Docker).
# Configuration is read from .env.mariadb.local by default.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

DEFAULT_CONFIG="$SCRIPT_DIR/.env.mariadb.local"
CONFIG_FILE="${MARIADB_LOCAL_ENV:-$DEFAULT_CONFIG}"
if [ ! -f "$CONFIG_FILE" ]; then
  if [ "$CONFIG_FILE" != "$DEFAULT_CONFIG" ]; then
    echo "✗ لم يُعثر على إعداد MariaDB المحلي: $CONFIG_FILE" >&2
    exit 1
  fi
  cp .env.mariadb.local.example "$DEFAULT_CONFIG"
  chmod 600 "$DEFAULT_CONFIG"
  echo "▶ تم إنشاء .env.mariadb.local. عدّل كلمة مرور MariaDB ثم شغّل ./run-mariadb-local.sh مرة أخرى." >&2
  exit 1
fi

# This file is intentionally a shell export file generated for the native
# MariaDB setup. Keep it mode 600 and do not commit it.
# shellcheck disable=SC1090
source "$CONFIG_FILE"

if [ "${CRM_DB_ENGINE:-}" != "mariadb" ]; then
  echo "✗ يجب أن يضبط $CONFIG_FILE قيمة CRM_DB_ENGINE=mariadb." >&2
  exit 1
fi

# Start common native service names when a local service is installed but not
# running. Any failure is followed by run.sh's connection preflight message.
if command -v systemctl >/dev/null 2>&1 \
   && ! systemctl is-active --quiet mariadb \
   && ! systemctl is-active --quiet mysql \
   && ! systemctl is-active --quiet mysqld; then
  echo "▶ محاولة تشغيل خدمة MariaDB المحلية..."
  sudo systemctl start mariadb 2>/dev/null \
    || sudo systemctl start mysql 2>/dev/null \
    || sudo systemctl start mysqld 2>/dev/null \
    || true
fi

# Invoke Bash explicitly so this launcher still works if a ZIP extraction or
# shared filesystem has removed the executable bit from run.sh.
exec bash "$SCRIPT_DIR/run.sh"
