#!/usr/bin/env bash
# Start a local MariaDB service for NebrasCRM using Docker Compose.
# Usage: ./setup-mariadb.sh
set -Eeuo pipefail

trap 'echo "✗ فشل إعداد MariaDB عند السطر ${LINENO}." >&2' ERR

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "✗ Docker / Docker Desktop مطلوب لتشغيل MariaDB محلياً." >&2
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

ENV_FILE=".env.mariadb"
if [ ! -f "$ENV_FILE" ]; then
  cp .env.mariadb.example "$ENV_FILE"
  echo "▶ تم إنشاء $ENV_FILE. ضع كلمات مرور قوية فيه ثم أعد تشغيل السكربت." >&2
  exit 1
fi

"${COMPOSE[@]}" --env-file "$ENV_FILE" -f docker-compose.mariadb.yml up -d

echo "▶ انتظار MariaDB حتى يصبح جاهزاً..."
# The password expands inside the MariaDB container, not in this host shell.
# shellcheck disable=SC2016
HEALTHCHECK_CMD='mariadb-admin ping -h localhost -u root -p"$MARIADB_ROOT_PASSWORD" --silent'
for ((attempt=1; attempt<=30; attempt++)); do
  if "${COMPOSE[@]}" --env-file "$ENV_FILE" -f docker-compose.mariadb.yml exec -T mariadb \
      sh -ec "$HEALTHCHECK_CMD" >/dev/null 2>&1; then
    echo "✅ MariaDB جاهز."
    echo
    echo "استخدم القيم التالية لتشغيل NebrasCRM:"
    echo "  CRM_DB_ENGINE=mariadb"
    echo "  CRM_DB_HOST=127.0.0.1"
    echo "  CRM_DB_PORT=3306"
    echo "  CRM_DB_NAME=nebrascrm"
    echo "  CRM_DB_USER=nebrascrm"
    echo "  CRM_DB_PASSWORD=<قيمة MARIADB_PASSWORD في .env.mariadb>"
    echo
    echo "لترحيل قاعدة SQLite الحالية:"
    echo "  CRM_DB_ENGINE=mariadb ... python3 migrate_mariadb.py --source crm.db --replace"
    exit 0
  fi
  sleep 2
done

echo "✗ لم تصبح MariaDB جاهزة خلال 60 ثانية. راجع: ${COMPOSE[*]} -f docker-compose.mariadb.yml logs" >&2
exit 1
