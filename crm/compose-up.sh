#!/usr/bin/env bash
# Build and start the complete NebrasCRM + MySQL 8.4 Docker Compose stack.
# Usage: ./compose-up.sh [--reset-data] [docker compose up options]
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

RESET_DATA=0
if [[ "${1:-}" == "--reset-data" ]]; then
  RESET_DATA=1
  shift
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "✗ Docker / Docker Desktop مطلوب لتشغيل المنظومة عبر Docker Compose." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "✗ Docker Compose غير متاح." >&2
  exit 1
fi

ENV_FILE="${COMPOSE_ENV_FILE:-$SCRIPT_DIR/.env.docker}"
if [ ! -f "$ENV_FILE" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "✗ يلزم python3 لإنشاء إعدادات Docker الآمنة أول مرة." >&2
    exit 1
  fi
  umask 077
  python3 "$SCRIPT_DIR/create_docker_env.py" "$ENV_FILE"
  echo "▶ تم إنشاء إعدادات Docker محلية آمنة: $ENV_FILE"
fi

# Compose substitutes ${...} before it applies a service's env_file. Validate
# the required values here so a damaged file produces an actionable message
# rather than a less clear Compose interpolation error.
required_vars=(
  CRM_SECRET
  CRM_PORTAL_SECRET
  CRM_AGENT_PORTAL_SECRET
  CRM_WEBHOOK_SECRET
  MYSQL_DATABASE
  MYSQL_USER
  MYSQL_PASSWORD
  MYSQL_ROOT_PASSWORD
)
# A reset deliberately creates an empty database, so it also requires an
# explicit first-admin configuration. Existing deployments remain compatible
# when they start without the new bootstrap variables.
if (( RESET_DATA )); then
  required_vars+=(
    CRM_BOOTSTRAP_ADMIN_EMAIL
    CRM_BOOTSTRAP_ADMIN_NAME
    CRM_BOOTSTRAP_ADMIN_PASSWORD
  )
fi

missing=()
for key in "${required_vars[@]}"; do
  value="$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -n 1 | cut -d= -f2- || true)"
  compact="${value//$'\r'/}"
  compact="${compact//[[:space:]]/}"
  if [[ -z "$compact" || "$compact" == '""' || "$compact" == "''" || "$compact" == *replace-with-* ]]; then
    missing+=("$key")
  fi
done
if ((${#missing[@]})); then
  echo "✗ ملف الإعدادات $ENV_FILE غير مكتمل: ${missing[*]}" >&2
  echo "  أضف قيماً حقيقية غير فارغة، ولا تشغّل Compose بدون --env-file $ENV_FILE." >&2
  if [[ "$ENV_FILE" == "$SCRIPT_DIR/.env.docker" ]]; then
    echo "  للتكوين التجريبي فقط: rm -f .env.docker && bash ./compose-up.sh --reset-data" >&2
  fi
  exit 1
fi

if (( RESET_DATA )); then
  echo "▶ حذف قاعدة بيانات MySQL التجريبية المحلية وإعادة إنشائها..."
  "${COMPOSE[@]}" --env-file "$ENV_FILE" -f docker-compose.yml down -v --remove-orphans || true
fi

if ! "${COMPOSE[@]}" --env-file "$ENV_FILE" -f docker-compose.yml up -d --build --remove-orphans "$@"; then
  echo >&2
  echo "✗ تعذّر تشغيل Docker Compose. آخر سجل لحاوية MySQL:" >&2
  "${COMPOSE[@]}" --env-file "$ENV_FILE" -f docker-compose.yml logs --tail=120 mysql >&2 || true
  echo >&2
  echo "  إذا كانت البيانات تجريبية فقط، أعد إنشاء قاعدة Docker المحلية:" >&2
  echo "    bash ./compose-up.sh --reset-data" >&2
  exit 1
fi

admin_email="$(grep -E '^CRM_BOOTSTRAP_ADMIN_EMAIL=' "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
echo
echo "✅ NebrasCRM يعمل عبر Docker Compose مع MySQL 8.4."
echo "   التطبيق: http://localhost:$(grep -E '^NEBRAS_PORT=' "$ENV_FILE" | tail -n 1 | cut -d= -f2 || printf '8008')/app"
echo "   دخول أول قاعدة جديدة: ${admin_email:-admin@nebrascrm.local}"
echo "   كلمة المرور الأولى محفوظة محلياً في CRM_BOOTSTRAP_ADMIN_PASSWORD داخل .env.docker"
echo "   الحالة:  ${COMPOSE[*]} --env-file $ENV_FILE -f docker-compose.yml ps"
echo "   السجل:    ${COMPOSE[*]} --env-file $ENV_FILE -f docker-compose.yml logs -f app"
