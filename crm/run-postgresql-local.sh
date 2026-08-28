#!/usr/bin/env bash
# Run NebrasCRM against a native/local PostgreSQL service (not Docker).
# Configuration is read from .env.postgresql.local by default.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

CONFIG_FILE="${POSTGRESQL_LOCAL_ENV:-$SCRIPT_DIR/.env.postgresql.local}"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "✗ لم يُعثر على إعداد PostgreSQL المحلي: $CONFIG_FILE" >&2
  echo "  انسخ .env.postgresql.local.example إليه أو اضبط POSTGRESQL_LOCAL_ENV." >&2
  exit 1
fi

# This source-able file contains only local CRM_DB_* exports. Keep it mode 600
# and do not commit it.
# shellcheck disable=SC1090
source "$CONFIG_FILE"

if [ "${CRM_DB_ENGINE:-}" != "postgresql" ] && [ "${CRM_DB_ENGINE:-}" != "postgres" ]; then
  echo "✗ يجب أن يضبط $CONFIG_FILE قيمة CRM_DB_ENGINE=postgresql." >&2
  exit 1
fi

# Invoke Bash explicitly so this launcher still works if a ZIP extraction or
# shared filesystem has removed the executable bit from run.sh.
exec bash "$SCRIPT_DIR/run.sh"
