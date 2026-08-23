#!/usr/bin/env bash
# تشغيل خادم NebrasCRM
set -e
cd "$(dirname "$0")"
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
  echo "▶ تثبيت المتطلبات..."; pip install -q -r requirements.txt; }
[ -f crm.db ] || {
  echo "▶ إنشاء قاعدة البيانات والبيانات التجريبية..."
  for s in seed.py seed_intel.py seed_extra.py seed_geo.py seed_portal.py; do
    [ -f "$s" ] && python3 "$s"; done; }
echo "▶ الخادم يعمل على http://localhost:${PORT:-8000}"
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
