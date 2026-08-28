#!/usr/bin/env bash
# تشغيل خادم NebrasCRM
# الاستخدام: ./run.sh  (أو PORT=9000 ./run.sh)
set -Eeuo pipefail

trap 'echo "✗ فشل التشغيل عند السطر ${LINENO}." >&2' ERR

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

find_python3() {
  local candidate
  for candidate in "${PYTHON_BIN:-}" python3 py; do
    [ -n "$candidate" ] || continue
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

# Do not install packages into the OS-managed Python. Modern Debian/Ubuntu
# installations intentionally reject that with PEP 668. A project-local venv
# keeps NebrasCRM dependencies isolated and needs no --break-system-packages.
BOOTSTRAP_PYTHON="$(find_python3)" || {
  echo "✗ لم يُعثر على Python 3. ثبّت Python 3.10 أو أحدث، أو اضبط PYTHON_BIN." >&2
  exit 1
}
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"
VENV_PYTHON="$VENV_DIR/bin/python3"
if [ ! -x "$VENV_PYTHON" ]; then
  echo "▶ إنشاء بيئة Python افتراضية محلية: $VENV_DIR"
  "$BOOTSTRAP_PYTHON" -m venv "$VENV_DIR" || {
    echo "✗ تعذّر إنشاء البيئة الافتراضية." >&2
    echo "  Debian/Ubuntu: sudo apt install python3-venv" >&2
    echo "  ثم أعد تشغيل ./run.sh" >&2
    exit 1
  }
fi
PYTHON="$VENV_PYTHON"

PORT="${PORT:-8008}"
if ! [[ "$PORT" =~ ^[0-9]{1,5}$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  echo "✗ PORT يجب أن يكون رقماً بين 1 و65535 (القيمة الحالية: $PORT)." >&2
  exit 1
fi

DB_ENGINE="$(printf '%s' "${CRM_DB_ENGINE:-sqlite}" | tr '[:upper:]' '[:lower:]')"
# MySQL speaks the same supported PyMySQL dialect as MariaDB in NebrasCRM.
[ "$DB_ENGINE" = "mysql" ] && DB_ENGINE="mariadb"

"$PYTHON" -c "import fastapi, uvicorn, multipart" 2>/dev/null || {
  echo "▶ تثبيت متطلبات Python..."
  "$PYTHON" -m pip install -r requirements.txt
}
if [ "$DB_ENGINE" = "mariadb" ]; then
  "$PYTHON" -c "import pymysql" 2>/dev/null || {
    echo "▶ تثبيت PyMySQL لدعم MySQL / MariaDB..."
    "$PYTHON" -m pip install 'PyMySQL>=1.1.0'
  }
elif [ "$DB_ENGINE" = "postgresql" ] || [ "$DB_ENGINE" = "postgres" ]; then
  "$PYTHON" -c "import psycopg" 2>/dev/null || {
    echo "▶ تثبيت Psycopg لدعم PostgreSQL..."
    "$PYTHON" -m pip install 'psycopg[binary]>=3.2.0'
  }
fi

preflight_mariadb() {
  local error_file
  error_file="$(mktemp)"
  if "$PYTHON" - <<'PY' >/dev/null 2>"$error_file"
import db
import sys
try:
    connection = db.connect()
except Exception as exc:
    print(exc, file=sys.stderr)
    raise SystemExit(1)
else:
    connection.close()
PY
  then
    rm -f "$error_file"
    return 0
  fi

  echo "✗ تعذّر الاتصال بـ MySQL / MariaDB قبل بدء الخادم." >&2
  sed -n '1p' "$error_file" >&2
  rm -f "$error_file"
  echo >&2
  echo "  تأكد من تشغيل MySQL أو MariaDB ومن صحة CRM_DB_HOST / CRM_DB_PORT / CRM_DB_NAME / CRM_DB_USER / CRM_DB_PASSWORD." >&2
  echo "  لتشغيل MySQL/MariaDB محلياً بأمر واحد: ./run-mysql.sh" >&2
  echo "  لإعداد MariaDB محلياً عبر Docker: ./setup-mariadb.sh" >&2
  echo "  لتشغيل النسخة المحلية بـ SQLite بدلاً منها:" >&2
  echo "    unset CRM_DB_ENGINE CRM_DB_HOST CRM_DB_PORT CRM_DB_NAME CRM_DB_USER CRM_DB_PASSWORD" >&2
  echo "    CRM_DB_ENGINE=sqlite ./run.sh" >&2
  return 1
}

preflight_postgresql() {
  local error_file
  error_file="$(mktemp)"
  if "$PYTHON" - <<'PY' >/dev/null 2>"$error_file"
import db
import sys
try:
    connection = db.connect()
except Exception as exc:
    print(exc, file=sys.stderr)
    raise SystemExit(1)
else:
    connection.close()
PY
  then
    rm -f "$error_file"
    return 0
  fi

  echo "✗ تعذّر الاتصال بـ PostgreSQL قبل بدء الخادم." >&2
  sed -n '1p' "$error_file" >&2
  rm -f "$error_file"
  echo >&2
  echo "  تأكد من تشغيل PostgreSQL ومن صحة CRM_DB_HOST / CRM_DB_PORT / CRM_DB_NAME / CRM_DB_USER / CRM_DB_PASSWORD." >&2
  echo "  لتشغيل PostgreSQL محلياً بدون Docker: sudo systemctl start postgresql && ./run-postgresql-local.sh" >&2
  echo "  لإعداد PostgreSQL عبر Docker: ./setup-postgresql.sh" >&2
  echo "  لتشغيل النسخة المحلية بـ SQLite بدلاً منها:" >&2
  echo "    unset CRM_DB_ENGINE CRM_DB_HOST CRM_DB_PORT CRM_DB_NAME CRM_DB_USER CRM_DB_PASSWORD CRM_DB_SSLMODE" >&2
  echo "    CRM_DB_ENGINE=sqlite ./run.sh" >&2
  return 1
}

case "$DB_ENGINE" in
  sqlite)
    # db.DB_PATH performs the same CRM_DB_PATH normalization used by the app.
    DB_FILE="$("$PYTHON" -c 'import db; print(db.DB_PATH)')"
    if [ ! -f "$DB_FILE" ]; then
      echo "▶ إنشاء قاعدة SQLite والبيانات التجريبية..."
      for seed in seed.py seed_intel.py seed_extra.py seed_geo.py seed_portal.py; do
        [ -f "$seed" ] && "$PYTHON" "$seed"
      done
    fi
    ;;
  mariadb)
    echo "▶ وضع MySQL / MariaDB: ${CRM_DB_HOST:-127.0.0.1}:${CRM_DB_PORT:-3306}/${CRM_DB_NAME:-nebrascrm}"
    preflight_mariadb || exit 1
    echo "  تم التحقق من الاتصال؛ سيتم إنشاء الجداول تلقائياً عند بدء الخادم."
    if [ "${SEED_DEMO:-0}" = "1" ]; then
      echo "▶ تحميل بيانات تجريبية إلى MySQL / MariaDB..."
      for seed in seed.py seed_intel.py seed_extra.py seed_geo.py seed_portal.py; do
        [ -f "$seed" ] && "$PYTHON" "$seed"
      done
    fi
    ;;
  postgresql|postgres)
    echo "▶ وضع PostgreSQL: ${CRM_DB_HOST:-127.0.0.1}:${CRM_DB_PORT:-5432}/${CRM_DB_NAME:-nebrascrm}"
    preflight_postgresql || exit 1
    echo "  تم التحقق من الاتصال؛ سيتم إنشاء الجداول تلقائياً عند بدء الخادم."
    if [ "${SEED_DEMO:-0}" = "1" ]; then
      echo "▶ تحميل بيانات تجريبية إلى PostgreSQL..."
      for seed in seed.py seed_intel.py seed_extra.py seed_geo.py seed_portal.py; do
        [ -f "$seed" ] && "$PYTHON" "$seed"
      done
    fi
    ;;
  *)
    echo "✗ CRM_DB_ENGINE يجب أن يكون sqlite أو mariadb/mysql أو postgresql." >&2
    exit 1
    ;;
esac

echo "▶ الخادم يعمل على http://localhost:${PORT}"
exec "$PYTHON" -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
