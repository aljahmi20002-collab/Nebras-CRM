#!/usr/bin/env python3
"""Prepare the complete NebrasCRM MySQL 8 Docker deployment.

This cross-platform helper is intentionally idempotent. It validates local
settings, starts MySQL 8, makes the application database/account match those
settings, starts NebrasCRM so it creates its schema and first staff admin, then
prints the non-sensitive list of CRM users.

Usage:
    python3 setup_mysql8.py
    python3 setup_mysql8.py --reset-data   # deletes the Docker MySQL volume
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
COMPOSE_FILE = ROOT / "docker-compose.yml"
DEFAULT_ENV_FILE = ROOT / ".env.docker"
REQUIRED_VALUES = (
    "CRM_SECRET",
    "CRM_PORTAL_SECRET",
    "CRM_AGENT_PORTAL_SECRET",
    "CRM_WEBHOOK_SECRET",
    "CRM_BOOTSTRAP_ADMIN_EMAIL",
    "CRM_BOOTSTRAP_ADMIN_NAME",
    "CRM_BOOTSTRAP_ADMIN_PASSWORD",
    "MYSQL_DATABASE",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_ROOT_PASSWORD",
)
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]{1,64}$")
SAFE_USERNAME = re.compile(r"^[A-Za-z0-9_]{1,32}$")


class SetupError(RuntimeError):
    """An actionable setup failure that should not print credentials."""


def run(command: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command in the CRM directory without using a shell."""
    return subprocess.run(
        command,
        cwd=ROOT,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )


def find_compose() -> tuple[str, list[str]]:
    """Return the Docker executable and its supported Compose command prefix."""
    docker = shutil.which("docker")
    if not docker:
        raise SetupError("Docker / Docker Desktop غير متاح. ثبّته وشغّله أولاً.")
    candidate = [docker, "compose"]
    if run(candidate + ["version"], capture=True).returncode == 0:
        return docker, candidate
    legacy = shutil.which("docker-compose")
    if legacy and run([legacy, "version"], capture=True).returncode == 0:
        return docker, [legacy]
    raise SetupError("Docker Compose غير متاح. شغّل Docker Desktop أو ثبّت Docker Compose.")


def parse_environment(path: Path) -> dict[str, str]:
    """Read the small .env.docker format without evaluating it as shell code."""
    values: dict[str, str] = {}
    for original in path.read_text(encoding="utf-8-sig").splitlines():
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def missing_required_values(values: dict[str, str]) -> list[str]:
    """Return required configuration names that are blank or still templates."""
    return [
        key for key in REQUIRED_VALUES
        if not values.get(key, "").strip() or "replace-with-" in values.get(key, "").lower()
    ]


def validate_environment(values: dict[str, str]) -> None:
    missing = missing_required_values(values)
    if missing:
        raise SetupError("ملف .env.docker غير مكتمل: " + ", ".join(missing))
    if not SAFE_IDENTIFIER.fullmatch(values["MYSQL_DATABASE"]):
        raise SetupError("MYSQL_DATABASE يجب أن يحتوي أحرفاً إنجليزية أو أرقاماً أو underscore فقط.")
    if not SAFE_USERNAME.fullmatch(values["MYSQL_USER"]):
        raise SetupError("MYSQL_USER يجب أن يحتوي أحرفاً إنجليزية أو أرقاماً أو underscore فقط.")
    email = values["CRM_BOOTSTRAP_ADMIN_EMAIL"].strip()
    if len(email) > 320 or "@" not in email or "\n" in email or "\r" in email:
        raise SetupError("CRM_BOOTSTRAP_ADMIN_EMAIL غير صالح.")
    if not 1 <= len(values["CRM_BOOTSTRAP_ADMIN_NAME"].strip()) <= 200:
        raise SetupError("CRM_BOOTSTRAP_ADMIN_NAME يجب أن يكون بين 1 و200 حرف.")
    if len(values["CRM_BOOTSTRAP_ADMIN_PASSWORD"]) < 8:
        raise SetupError("CRM_BOOTSTRAP_ADMIN_PASSWORD يجب ألا يقل عن 8 أحرف.")


def ensure_environment(path: Path) -> dict[str, str]:
    """Create the secure local config once, or validate the existing one."""
    if not path.exists():
        generator = ROOT / "create_docker_env.py"
        result = run([sys.executable, str(generator), str(path)])
        if result.returncode:
            raise SetupError("تعذر إنشاء ملف .env.docker الآمن.")
        print(f"✔ تم إنشاء إعدادات Docker محلية: {path.name}")
    values = parse_environment(path)
    validate_environment(values)
    return values


def compose_args(prefix: list[str], env_file: Path, *arguments: str) -> list[str]:
    return [*prefix, "--env-file", str(env_file), "-f", str(COMPOSE_FILE), *arguments]


def service_container(prefix: list[str], env_file: Path, service: str) -> str:
    result = run(compose_args(prefix, env_file, "ps", "-q", service), capture=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def tail_logs(prefix: list[str], env_file: Path, services: Iterable[str]) -> None:
    for service in services:
        print(f"\n--- آخر سجل لخدمة {service} ---", file=sys.stderr)
        run(compose_args(prefix, env_file, "logs", "--tail=120", service))


def wait_for_service(
    docker: str,
    prefix: list[str],
    env_file: Path,
    service: str,
    timeout: int,
) -> None:
    """Wait for a Compose service to report healthy, with useful diagnostics."""
    deadline = time.monotonic() + timeout
    last_status = ""
    while time.monotonic() < deadline:
        container = service_container(prefix, env_file, service)
        if container:
            inspect = run(
                [docker, "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}", container],
                capture=True,
            )
            status = inspect.stdout.strip().lower() if inspect.returncode == 0 else "unknown"
            if status == "healthy":
                print(f"✔ خدمة {service} بحالة healthy.")
                return
            if status in {"unhealthy", "exited", "dead", "removing"}:
                tail_logs(prefix, env_file, (service,))
                raise SetupError(f"الخدمة {service} توقفت أو أصبحت unhealthy ({status}).")
            if status and status != last_status:
                print(f"… انتظار {service}: {status}")
                last_status = status
        time.sleep(2)
    tail_logs(prefix, env_file, (service,))
    raise SetupError(f"انتهت مهلة انتظار الخدمة {service} ({timeout} ثانية).")


def mysql_literal(value: str) -> str:
    """Return a MySQL string literal for stdin-only bootstrap SQL.

    Passwords are sent to the mysql client over stdin, not placed in the host
    command line or emitted in setup output.
    """
    escaped = (
        value.replace("\\", "\\\\")
        .replace("\x00", "\\0")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\x1a", "\\Z")
        .replace("'", "\\'")
    )
    return f"'{escaped}'"


def mysql_provision_sql(values: dict[str, str]) -> str:
    """Build idempotent SQL for the app database and limited app account."""
    database = values["MYSQL_DATABASE"]
    user = mysql_literal(values["MYSQL_USER"])
    password = mysql_literal(values["MYSQL_PASSWORD"])
    return f"""-- Generated by setup_mysql8.py; do not save this stream.
CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS {user}@'%' IDENTIFIED BY {password};
ALTER USER {user}@'%' IDENTIFIED BY {password};
GRANT ALL PRIVILEGES ON `{database}`.* TO {user}@'%';
FLUSH PRIVILEGES;
"""


def mysql_query(prefix: list[str], env_file: Path, sql: str) -> None:
    """Run SQL as MySQL root inside its private Compose container."""
    command = compose_args(
        prefix,
        env_file,
        "exec",
        "-T",
        "mysql",
        "sh",
        "-lc",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" MYSQL_HISTFILE=/dev/null exec mysql --protocol=socket --user=root',
    )
    result = run(command, input_text=sql)
    if result.returncode:
        raise SetupError("تعذر تنفيذ تهيئة MySQL. راجع سجل خدمة mysql.")


def verify_crm_users(prefix: list[str], env_file: Path, database: str) -> None:
    """Print a non-sensitive verification of the CRM staff users table."""
    sql = f"""USE `{database}`;
SELECT id,email,role,active FROM users ORDER BY id;
"""
    print("\nمستخدمو NebrasCRM المجهزون (من دون كلمات مرور):")
    mysql_query(prefix, env_file, sql)


def setup(args: argparse.Namespace) -> None:
    if not COMPOSE_FILE.is_file():
        raise SetupError("ملف docker-compose.yml غير موجود بجوار السكربت.")

    env_file = Path(args.env_file).expanduser()
    if not env_file.is_absolute():
        env_file = (ROOT / env_file).resolve()
    values = ensure_environment(env_file)
    docker, prefix = find_compose()

    if args.reset_data:
        print("⚠ حذف بيانات MySQL Docker المحلية بناءً على --reset-data...")
        result = run(compose_args(prefix, env_file, "down", "-v", "--remove-orphans"))
        if result.returncode:
            print("! لم توجد منظومة سابقة أو لم تُغلق كلياً؛ سيستمر الإعداد.")

    print("▶ تشغيل MySQL 8.4 والانتظار حتى يصبح سليماً...")
    result = run(compose_args(prefix, env_file, "up", "-d", "mysql"))
    if result.returncode:
        tail_logs(prefix, env_file, ("mysql",))
        raise SetupError("تعذر تشغيل خدمة MySQL 8.4.")
    wait_for_service(docker, prefix, env_file, "mysql", args.mysql_timeout)

    print("▶ مزامنة قاعدة البيانات وحساب MySQL الخاص بالتطبيق...")
    mysql_query(prefix, env_file, mysql_provision_sql(values))
    print(f"✔ قاعدة البيانات `{values['MYSQL_DATABASE']}` وحساب التطبيق `{values['MYSQL_USER']}` جاهزان.")

    print("▶ بناء وتشغيل NebrasCRM لإنشاء المخطط والمدير الأول...")
    result = run(compose_args(prefix, env_file, "up", "-d", "--build", "--force-recreate", "app"))
    if result.returncode:
        tail_logs(prefix, env_file, ("app", "mysql"))
        raise SetupError("تعذر تشغيل تطبيق NebrasCRM.")
    wait_for_service(docker, prefix, env_file, "app", args.app_timeout)

    verify_crm_users(prefix, env_file, values["MYSQL_DATABASE"])
    port = values.get("NEBRAS_PORT", "8008") or "8008"
    print("\n✅ اكتملت تهيئة MySQL 8 وNebrasCRM.")
    print(f"   التطبيق: http://localhost:{port}/app")
    print(f"   المدير الأول: {values['CRM_BOOTSTRAP_ADMIN_EMAIL']}")
    print("   كلمة المرور: CRM_BOOTSTRAP_ADMIN_PASSWORD في ملف .env.docker المحلي فقط.")
    print("   أنشئ بقية المستخدمين من: الإعدادات → المستخدمون.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare NebrasCRM + MySQL 8.4 Docker stack.")
    parser.add_argument(
        "--reset-data",
        action="store_true",
        help="delete only the Compose MySQL volume before setup (destructive)",
    )
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="path to .env.docker")
    parser.add_argument("--mysql-timeout", type=int, default=180, help="seconds to wait for MySQL health")
    parser.add_argument("--app-timeout", type=int, default=300, help="seconds to wait for application health")
    args = parser.parse_args()
    if args.mysql_timeout < 10 or args.app_timeout < 10:
        parser.error("timeouts must be at least 10 seconds")
    try:
        setup(args)
    except SetupError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n✗ أُلغي الإعداد.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
