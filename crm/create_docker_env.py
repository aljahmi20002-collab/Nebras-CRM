#!/usr/bin/env python3
"""Create a private, secure local environment file for Docker Compose.

Usage:
    python3 create_docker_env.py [.env.docker] [--force]

The generated values are URL-safe and contain no shell interpolation characters.
It never prints credentials, and refuses to overwrite a file unless --force is
explicitly supplied.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from secrets import token_urlsafe


def build_environment() -> str:
    """Return a complete Compose environment with independent random secrets."""
    secret = lambda: token_urlsafe(48)
    password = lambda: token_urlsafe(32)
    return (
        "# Generated locally. Keep this file private and do not commit it.\n"
        "NEBRAS_PORT=8008\n"
        "CRM_ENV=production\n"
        f"CRM_SECRET={secret()}\n"
        f"CRM_PORTAL_SECRET={secret()}\n"
        f"CRM_AGENT_PORTAL_SECRET={secret()}\n"
        f"CRM_WEBHOOK_SECRET={secret()}\n"
        "CRM_BOOTSTRAP_ADMIN_EMAIL=admin@nebrascrm.local\n"
        "CRM_BOOTSTRAP_ADMIN_NAME=NebrasCRM Administrator\n"
        f"CRM_BOOTSTRAP_ADMIN_PASSWORD={password()}\n"
        "CRM_CORS_ORIGINS=\n"
        "CRM_RESEND_API_KEY=\n\n"
        "MYSQL_DATABASE=nebrascrm\n"
        "MYSQL_USER=nebrascrm\n"
        f"MYSQL_PASSWORD={password()}\n"
        f"MYSQL_ROOT_PASSWORD={password()}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a secure local .env.docker file.")
    parser.add_argument("path", nargs="?", default=".env.docker", help="output environment file")
    parser.add_argument("--force", action="store_true", help="replace an existing file")
    args = parser.parse_args()

    path = Path(args.path).expanduser().resolve()
    if path.exists() and not args.force:
        parser.error(f"refusing to overwrite existing file: {path} (use --force)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_environment(), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        # Windows permissions are managed by the account/NTFS ACL instead.
        pass
    print(f"Created private Docker environment: {path}")


if __name__ == "__main__":
    main()
