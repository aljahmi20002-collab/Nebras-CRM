#!/usr/bin/env bash
# Prepare the complete Docker-based NebrasCRM + MySQL 8.4 stack.
# Usage: bash ./setup-mysql8.sh [--reset-data]
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$SCRIPT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ يلزم python3 لتشغيل إعداد MySQL 8." >&2
  exit 1
fi

exec python3 "$SCRIPT_DIR/setup_mysql8.py" "$@"
