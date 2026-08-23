"""Small, dependency-free security primitives used by all NebrasCRM auth realms.

The project intentionally avoids a heavyweight authentication dependency, but it
still needs modern password derivation, signed expiring tokens and predictable
production configuration.  Keeping those primitives here prevents the staff,
customer and partner portals from drifting apart.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from collections import defaultdict
from threading import Lock
from typing import Iterable, Optional


PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 310_000
_MIN_PASSWORD_LENGTH = 8


def is_production() -> bool:
    """Whether strict deployment safeguards should be enforced."""
    return os.environ.get("CRM_ENV", "").strip().lower() in {"prod", "production"}


def configured_secret(env_name: str, development_default: str, label: str) -> str:
    """Read a signing secret and fail closed when production is misconfigured.

    Development keeps deterministic demo credentials working, while production
    must explicitly configure a sufficiently long secret.  This makes accidental
    deployment with a repository default much harder.
    """
    value = os.environ.get(env_name, "").strip()
    if not value:
        if is_production():
            raise RuntimeError(
                f"{env_name} must be configured when CRM_ENV=production ({label})."
            )
        return development_default
    if is_production() and len(value) < 32:
        raise RuntimeError(f"{env_name} must contain at least 32 characters in production.")
    return value


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("invalid base64 value")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, iterations: int = PASSWORD_ITERATIONS) -> str:
    """Return a salted PBKDF2-SHA256 password record.

    PBKDF2 is part of Python's standard library, so fresh deployments do not
    depend on an optional native package simply to store passwords safely.
    """
    if not isinstance(password, str):
        raise TypeError("password must be text")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{PASSWORD_SCHEME}${iterations}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(
    password: str,
    stored: Optional[str],
    *,
    legacy_secrets: Iterable[str] = (),
) -> tuple[bool, bool]:
    """Verify a password and return ``(valid, should_upgrade)``.

    Older database snapshots used SHA-256(password + secret).  They remain
    readable just long enough for a successful login to transparently replace
    the weak record with a salted PBKDF2 one.
    """
    if not isinstance(password, str) or not isinstance(stored, str) or not stored:
        return False, False

    try:
        scheme, raw_iterations, raw_salt, raw_digest = stored.split("$", 3)
        iterations = int(raw_iterations)
        if scheme != PASSWORD_SCHEME or not 100_000 <= iterations <= 2_000_000:
            raise ValueError("unsupported password record")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _b64decode(raw_salt), iterations
        )
        valid = hmac.compare_digest(_b64encode(digest), raw_digest)
        return valid, valid and iterations < PASSWORD_ITERATIONS
    except (TypeError, ValueError):
        pass

    for secret in dict.fromkeys(s for s in legacy_secrets if s):
        candidate = hashlib.sha256((password + secret).encode("utf-8")).hexdigest()
        if hmac.compare_digest(candidate, stored):
            return True, True
    return False, False


def password_error(password: str) -> Optional[str]:
    """Return a user-facing validation message, or ``None`` when valid."""
    if not isinstance(password, str) or len(password) < _MIN_PASSWORD_LENGTH:
        return f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."
    if len(password) > 1024:
        return "Password is too long."
    return None


def make_token(subject: int, secret: str, ttl_seconds: int) -> str:
    """Create a compact HMAC-signed, expiring bearer token."""
    now = int(time.time())
    ttl = max(60, int(ttl_seconds))
    payload = json.dumps(
        {"sub": int(subject), "iat": now, "exp": now + ttl},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded = _b64encode(payload)
    signature = _b64encode(hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def parse_token(token: str, secret: str) -> Optional[int]:
    """Return the signed subject for a valid, unexpired token; otherwise None."""
    try:
        encoded, supplied = token.split(".", 1)
        expected = _b64encode(
            hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(supplied, expected):
            return None
        payload = json.loads(_b64decode(encoded))
        subject = payload.get("sub")
        issued_at = payload.get("iat")
        expires_at = payload.get("exp")
        now = int(time.time())
        if isinstance(subject, bool) or not isinstance(subject, int) or subject <= 0:
            return None
        if not isinstance(issued_at, int) or not isinstance(expires_at, int):
            return None
        if issued_at > now + 300 or expires_at <= now or expires_at <= issued_at:
            return None
        return subject
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
        return None


class LoginThrottle:
    """Small in-memory login lockout shared by the independent auth realms."""
    def __init__(self, tries: int = 5, window_seconds: int = 900):
        self.tries = tries
        self.window_seconds = window_seconds
        self._failures: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def wait_minutes(self, key: str) -> int:
        now = time.time()
        with self._lock:
            failures = [at for at in self._failures[key] if now - at < self.window_seconds]
            self._failures[key] = failures
            if len(failures) < self.tries:
                return 0
            return max(1, int((self.window_seconds - (now - failures[0])) / 60) + 1)

    def fail(self, key: str) -> int:
        with self._lock:
            self._failures[key].append(time.time())
            return max(0, self.tries - len(self._failures[key]))

    def clear(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


def client_ip(request) -> str:
    """Return a client address without trusting spoofable proxy headers by default."""
    if os.environ.get("CRM_TRUST_PROXY_HEADERS", "").lower() in {"1", "true", "yes"}:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if getattr(request, "client", None) else "unknown"
