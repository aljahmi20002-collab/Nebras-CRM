#!/usr/bin/env bash
# Start a local PostgreSQL service for NebrasCRM using Docker Compose.
# Usage: ./setup-postgresql.sh
set -Eeuo pipefail

trap 'echo "✗ فشل إعداد PostgreSQL عند السطر ${LINENO}." >&2' ERR

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "✗ Docker / Docker Desktop مطلوب لتشغيل PostgreSQL عبر Docker." >&2
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

ENV_FILE=".env.postgresql"
if [ ! -f "$ENV_FILE" ]; then
  cp .env.postgresql.example "$ENV_FILE"
  echo "▶ تم إنشاء $ENV_FILE. ضع كلمة مرور قوية فيه ثم أعد تشغيل السكربت." >&2
  exit 1
fi

"${COMPOSE[@]}" --env-file "$ENV_FILE" -f docker-compose.postgresql.yml up -d

echo "▶ انتظار PostgreSQL حتى يصبح جاهزاً..."
# Variables expand inside the container, not in this host shell.
# shellcheck disable=SC2016
HEALTHCHECK_CMD='pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
for ((attempt=1; attempt<=30; attempt++)); do
  if "${COMPOSE[@]}" --env-file "$ENV_FILE" -f docker-compose.postgresql.yml exec -T postgresql \
      sh -ec "$HEALTHCHECK_CMD" >/dev/null 2>&1; then
    echo "✅ PostgreSQL جاهز."
    echo
    echo "استخدم القيم التالية لتشغيل NebrasCRM:"
    echo "  CRM_DB_ENGINE=postgresql"
    echo "  CRM_DB_HOST=127.0.0.1"
    echo "  CRM_DB_PORT=5432"
    echo "  CRM_DB_NAME=nebrascrm"
    echo "  CRM_DB_USER=nebrascrm"
    echo "  CRM_DB_PASSWORD=<قيمة POSTGRES_PASSWORD في .env.postgresql>"
    echo
    echo "لترحيل قاعدة SQLite الحالية:"
    echo "  CRM_DB_ENGINE=postgresql ... python3 migrate_postgresql.py --source crm.db --replace"
    exit 0
  fi
  sleep 2
done

echo "✗ لم يصبح PostgreSQL جاهزاً خلال 60 ثانية. راجع: ${COMPOSE[*]} -f docker-compose.postgresql.yml logs" >&2
exit 1
