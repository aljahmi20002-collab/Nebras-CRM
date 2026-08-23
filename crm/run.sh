#!/usr/bin/env bash
# تشغيل خادم NebrasCRM
# الاستخدام: ./run.sh  (أو PORT=9000 ./run.sh)
set -Eeuo pipefail

trap 'echo "✗ فشل التشغيل عند السطر ${LINENO}." >&2' ERR

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

find_python() {
  local candidate
  for candidate in "${PYTHON_BIN:-}" python3 python py; do
    [ -n "$candidate" ] || continue
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON="$(find_python)" || {
  echo "✗ لم يُعثر على Python 3. ثبّت Python 3.10 أو أحدث، أو اضبط PYTHON_BIN." >&2
  exit 1
}

PORT="${PORT:-8008}"
if ! [[ "$PORT" =~ ^[0-9]{1,5}$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  echo "✗ PORT يجب أن يكون رقماً بين 1 و65535 (القيمة الحالية: $PORT)." >&2
  exit 1
fi

"$PYTHON" -c "import fastapi, uvicorn, multipart" 2>/dev/null || {
  echo "▶ تثبيت متطلبات Python..."
  "$PYTHON" -m pip install -r requirements.txt
}

# db.DB_PATH performs the same CRM_DB_PATH normalization used by the app.
DB_FILE="$("$PYTHON" -c 'import db; print(db.DB_PATH)')"
if [ ! -f "$DB_FILE" ]; then
  echo "▶ إنشاء قاعدة البيانات والبيانات التجريبية..."
  for seed in seed.py seed_intel.py seed_extra.py seed_geo.py seed_portal.py; do
    [ -f "$seed" ] && "$PYTHON" "$seed"
  done
fi

echo "▶ الخادم يعمل على http://localhost:${PORT}"
exec "$PYTHON" -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
