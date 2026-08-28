"""Database layer for NebrasCRM.

SQLite remains the zero-configuration default. Set ``CRM_DB_ENGINE=mariadb``
or ``CRM_DB_ENGINE=postgresql`` to use a network database server. The small
compatibility layer below lets the metadata-driven application keep its
SQLite-style ``?`` parameters and row access with MariaDB or PostgreSQL.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sqlite3
from typing import Iterable

from schema import MODULES

def normalize_engine(value: str | None) -> str:
    """Normalize public database engine names to the internal dialect names."""
    engine = (value or "sqlite").strip().lower()
    # Friendly aliases preserve one SQL dialect per server family. Documentation
    # uses ``mariadb`` and ``postgresql`` as the canonical configuration values.
    engine = {"mysql": "mariadb", "postgres": "postgresql"}.get(engine, engine)
    if engine not in {"sqlite", "mariadb", "postgresql"}:
        raise RuntimeError("CRM_DB_ENGINE must be 'sqlite', 'mariadb'/'mysql', or 'postgresql'.")
    return engine


DB_ENGINE = normalize_engine(os.environ.get("CRM_DB_ENGINE", "sqlite"))

# SQLite setting (the default)
DB_PATH = os.path.abspath(os.path.expanduser(
    os.environ.get("CRM_DB_PATH") or os.path.join(os.path.dirname(__file__), "crm.db")
))

# MariaDB/MySQL setting. The password is intentionally allowed to be empty for a
# local development server, but production should use a dedicated passworded account.
MARIADB_HOST = os.environ.get("CRM_DB_HOST", "127.0.0.1")
MARIADB_PORT = int(os.environ.get("CRM_DB_PORT", "3306"))
MARIADB_NAME = os.environ.get("CRM_DB_NAME", "nebrascrm")
MARIADB_USER = os.environ.get("CRM_DB_USER", "nebrascrm")
MARIADB_PASSWORD = os.environ.get("CRM_DB_PASSWORD", "")
MARIADB_CHARSET = os.environ.get("CRM_DB_CHARSET", "utf8mb4")

# PostgreSQL uses the same CRM_DB connection variables, with its conventional
# default port and optional SSL mode.
POSTGRES_HOST = os.environ.get("CRM_DB_HOST", "127.0.0.1")
POSTGRES_PORT = int(os.environ.get("CRM_DB_PORT", "5432"))
POSTGRES_NAME = os.environ.get("CRM_DB_NAME", "nebrascrm")
POSTGRES_USER = os.environ.get("CRM_DB_USER", "nebrascrm")
POSTGRES_PASSWORD = os.environ.get("CRM_DB_PASSWORD", "")
POSTGRES_SSLMODE = os.environ.get("CRM_DB_SSLMODE", "prefer")

BASE_COLS = """
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT, updated_at TEXT,
  created_by INTEGER, owner_id INTEGER,
  deleted INTEGER DEFAULT 0,
  tags TEXT DEFAULT ''
"""

TYPE_SQL = {"number": "REAL", "currency": "REAL"}
IntegrityError = sqlite3.IntegrityError


def is_sqlite() -> bool:
    return DB_ENGINE == "sqlite"


def is_mariadb() -> bool:
    return DB_ENGINE == "mariadb"


def is_postgresql() -> bool:
    return DB_ENGINE == "postgresql"


def _load_pymysql():
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError(
            "MySQL/MariaDB support requires PyMySQL. Run: python3 -m pip install PyMySQL"
        ) from exc
    return pymysql


def _load_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL support requires Psycopg. Run: python3 -m pip install 'psycopg[binary]'"
        ) from exc
    return psycopg, dict_row


def _translate_sql(sql: str) -> str:
    """Translate the SQLite dialect subset used by MariaDB and PostgreSQL."""
    if is_sqlite():
        return sql

    translated = sql
    if is_postgresql():
        # PostgreSQL accepts the application's double-quoted identifiers and
        # qmark parameters only need conversion to Psycopg's %s form.
        translated = re.sub(
            r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
            "BIGSERIAL PRIMARY KEY",
            translated,
            flags=re.IGNORECASE,
        )
        translated = re.sub(r"\bAUTOINCREMENT\b", "", translated, flags=re.IGNORECASE)
        # Business dates are stored as ISO text for SQLite compatibility. Keep
        # comparison types aligned on PostgreSQL instead of comparing text to date.
        translated = re.sub(r"\bdate\(\s*'now'\s*\)", "CURRENT_DATE::text", translated, flags=re.IGNORECASE)
        # PostgreSQL already supports ON CONFLICT (...) DO UPDATE and excluded.
        return translated.replace("?", "%s")

    # The application uses double quotes exclusively for identifiers. MariaDB
    # uses backticks unless ANSI_QUOTES is globally enabled.
    translated = translated.replace('"', '`')
    translated = re.sub(
        r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
        "BIGINT AUTO_INCREMENT PRIMARY KEY",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(
        r"\bINTEGER\s+PRIMARY\s+KEY\b", "BIGINT PRIMARY KEY", translated, flags=re.IGNORECASE
    )
    translated = re.sub(r"\bAUTOINCREMENT\b", "AUTO_INCREMENT", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\bREAL\b", "DOUBLE", translated, flags=re.IGNORECASE)
    # Key columns cannot be TEXT/BLOB in MariaDB without an index prefix.
    translated = re.sub(
        r"\bTEXT\s+PRIMARY\s+KEY\b", "VARCHAR(255) PRIMARY KEY", translated, flags=re.IGNORECASE
    )
    translated = re.sub(
        r"\bTEXT\s+UNIQUE\b", "VARCHAR(320) UNIQUE", translated, flags=re.IGNORECASE
    )
    translated = re.sub(r"\bTEXT\s+DEFAULT\b", "VARCHAR(255) DEFAULT", translated,
                        flags=re.IGNORECASE)
    translated = re.sub(r"\bdate\(\s*'now'\s*\)", "CURRENT_DATE", translated, flags=re.IGNORECASE)
    translated = re.sub(
        r"CAST\(([^)]+)\s+AS\s+INTEGER\)", r"CAST(\1 AS SIGNED)", translated, flags=re.IGNORECASE
    )
    translated = re.sub(r"\bINSERT\s+OR\s+REPLACE\b", "REPLACE", translated, flags=re.IGNORECASE)
    translated = re.sub(
        r"ON\s+CONFLICT\s*\([^)]*\)\s*DO\s+UPDATE\s+SET",
        "ON DUPLICATE KEY UPDATE",
        translated,
        flags=re.IGNORECASE,
    )
    translated = re.sub(r"\bexcluded\.([A-Za-z_][A-Za-z0-9_]*)", r"VALUES(\1)", translated)
    translated = re.sub(r"CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS", "CREATE INDEX", translated,
                        flags=re.IGNORECASE)
    translated = re.sub(r"CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS", "CREATE UNIQUE INDEX", translated,
                        flags=re.IGNORECASE)
    # All application SQL uses qmark placeholders. Static SQL does not contain
    # literal question marks, so this conversion is safe and keeps call sites simple.
    return translated.replace("?", "%s")


class MariaRow(dict):
    """Dict row with SQLite Row-compatible numeric indexing."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class MariaCursor:
    def __init__(self, connection, raw=None):
        self._connection = connection
        self._raw = raw or connection._raw.cursor()

    def execute(self, sql: str, params=None):
        translated = _translate_sql(sql)
        # SQLite has a partial unique index for commission posting. MariaDB has
        # no equivalent partial-index syntax; the application also checks this
        # invariant before insert, so skip this optional hardening index there.
        if re.match(r"^CREATE\s+UNIQUE\s+INDEX.*\bWHERE\b", translated, re.IGNORECASE | re.DOTALL):
            return self
        try:
            self._raw.execute(translated, params or ())
        except Exception as exc:
            # MariaDB before 10.5 does not understand IF NOT EXISTS for indexes.
            # Duplicate index errors are harmless during idempotent startup.
            args = getattr(exc, "args", ())
            code = args[0] if args else None
            if (isinstance(code, int) and code in {1061, 1831}) and re.match(
                r"^CREATE\s+(UNIQUE\s+)?INDEX", translated, re.IGNORECASE
            ):
                return self
            raise
        return self

    def executemany(self, sql: str, params):
        self._raw.executemany(_translate_sql(sql), params)
        return self

    def fetchone(self):
        row = self._raw.fetchone()
        return MariaRow(row) if row is not None else None

    def fetchall(self):
        return [MariaRow(row) for row in self._raw.fetchall()]

    def __iter__(self):
        for row in self._raw:
            yield MariaRow(row)

    @property
    def lastrowid(self):
        return self._raw.lastrowid

    @property
    def rowcount(self):
        return self._raw.rowcount

    def close(self):
        self._raw.close()


class MariaConnection:
    def __init__(self, raw):
        self._raw = raw

    def cursor(self):
        return MariaCursor(self)

    def execute(self, sql: str, params=None):
        return MariaCursor(self).execute(sql, params)

    def executemany(self, sql: str, params):
        return MariaCursor(self).executemany(sql, params)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


class PostgresRow(dict):
    """Psycopg dict row with the numeric indexing used by sqlite3.Row callers."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class PostgresCursor:
    def __init__(self, connection, raw=None):
        self._connection = connection
        self._raw = raw or connection._raw.cursor()
        self._lastrowid = None
        self._is_insert = False

    def execute(self, sql: str, params=None):
        translated = _translate_sql(sql)
        self._lastrowid = None
        self._is_insert = bool(re.match(r"^\s*INSERT\s+INTO\b", translated, re.IGNORECASE))
        self._raw.execute(translated, params or ())
        return self

    def executemany(self, sql: str, params):
        self._lastrowid = None
        self._is_insert = bool(re.match(r"^\s*INSERT\s+INTO\b", _translate_sql(sql), re.IGNORECASE))
        self._raw.executemany(_translate_sql(sql), params)
        return self

    def fetchone(self):
        row = self._raw.fetchone()
        return PostgresRow(row) if row is not None else None

    def fetchall(self):
        return [PostgresRow(row) for row in self._raw.fetchall()]

    def __iter__(self):
        for row in self._raw:
            yield PostgresRow(row)

    @property
    def lastrowid(self):
        # PostgreSQL does not expose a DB-API lastrowid. LASTVAL() is connection
        # scoped and every NebrasCRM insert that requests this property targets an
        # identity/serial id column, so it preserves the SQLite call-site contract.
        if self._lastrowid is None and self._is_insert:
            cursor = self._connection._raw.cursor()
            try:
                cursor.execute("SELECT LASTVAL() AS id")
                row = cursor.fetchone()
                self._lastrowid = row["id"] if isinstance(row, dict) else row[0]
            finally:
                cursor.close()
        return self._lastrowid

    @property
    def rowcount(self):
        return self._raw.rowcount

    def close(self):
        self._raw.close()


class PostgresConnection:
    def __init__(self, raw):
        self._raw = raw

    def cursor(self):
        return PostgresCursor(self)

    def execute(self, sql: str, params=None):
        return PostgresCursor(self).execute(sql, params)

    def executemany(self, sql: str, params):
        return PostgresCursor(self).executemany(sql, params)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


def connect():
    if is_sqlite():
        parent = os.path.dirname(DB_PATH)
        if parent:
            os.makedirs(parent, exist_ok=True)
        con = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA busy_timeout=10000")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    global IntegrityError
    if is_postgresql():
        psycopg, dict_row = _load_psycopg()
        IntegrityError = psycopg.IntegrityError
        try:
            raw = psycopg.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_NAME,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                sslmode=POSTGRES_SSLMODE,
                connect_timeout=10,
                autocommit=False,
                row_factory=dict_row,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not connect to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_NAME} "
                f"as {POSTGRES_USER}. Check CRM_DB_* environment variables."
            ) from exc
        return PostgresConnection(raw)

    pymysql = _load_pymysql()
    IntegrityError = pymysql.err.IntegrityError
    try:
        raw = pymysql.connect(
            host=MARIADB_HOST,
            port=MARIADB_PORT,
            user=MARIADB_USER,
            password=MARIADB_PASSWORD,
            database=MARIADB_NAME,
            charset=MARIADB_CHARSET,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Could not connect to MySQL/MariaDB at {MARIADB_HOST}:{MARIADB_PORT}/{MARIADB_NAME} "
            f"as {MARIADB_USER}. Check CRM_DB_* environment variables."
        ) from exc
    return MariaConnection(raw)


def table_exists(con, table: str) -> bool:
    if is_sqlite():
        return bool(con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone())
    if is_postgresql():
        return bool(con.execute(
            """SELECT 1 FROM information_schema.tables
               WHERE table_schema=current_schema() AND table_name=?""", (table,)
        ).fetchone())
    return bool(con.execute(
        """SELECT 1 FROM information_schema.tables
           WHERE table_schema=DATABASE() AND table_name=?""", (table,)
    ).fetchone())


def table_columns(con, table: str) -> set[str]:
    if is_sqlite():
        return {row["name"] for row in con.execute(f'PRAGMA table_info("{table}")')}
    if is_postgresql():
        sql = """SELECT column_name AS name FROM information_schema.columns
                 WHERE table_schema=current_schema() AND table_name=?"""
    else:
        sql = """SELECT column_name AS name FROM information_schema.columns
                 WHERE table_schema=DATABASE() AND table_name=?"""
    return {row["name"] for row in con.execute(sql, (table,))}


def list_tables(con) -> set[str]:
    if is_sqlite():
        return {
            row["name"]
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    if is_postgresql():
        sql = "SELECT table_name AS name FROM information_schema.tables WHERE table_schema=current_schema()"
    else:
        sql = "SELECT table_name AS name FROM information_schema.tables WHERE table_schema=DATABASE()"
    return {row["name"] for row in con.execute(sql)}


def reset_identity(con, tables: Iterable[str]):
    """Reset IDs for cleared business tables while preserving users/geography."""
    names = [table for table in tables if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table)]
    if not names:
        return
    if is_sqlite():
        if table_exists(con, "sqlite_sequence"):
            placeholders = ",".join("?" for _ in names)
            con.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})", names)
        return
    if is_postgresql():
        for table in names:
            # pg_get_serial_sequence() returns NULL for tables without an id
            # sequence; setval(NULL, ...) is harmlessly skipped in that case.
            sequence = con.execute("SELECT pg_get_serial_sequence(?, 'id') AS sequence_name", (table,)).fetchone()
            if sequence and sequence["sequence_name"]:
                con.execute("SELECT setval(?, 1, false)", (sequence["sequence_name"],))
        return
    for table in names:
        con.execute(f"ALTER TABLE `{table}` AUTO_INCREMENT = 1")


def sync_identity(con, tables: Iterable[str]):
    """Advance PostgreSQL serial sequences after importing explicit SQLite IDs."""
    if not is_postgresql():
        return
    for table in (name for name in tables if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name)):
        if "id" not in table_columns(con, table):
            continue
        sequence = con.execute("SELECT pg_get_serial_sequence(?, 'id') AS sequence_name", (table,)).fetchone()
        if not sequence or not sequence["sequence_name"]:
            continue
        maximum = con.execute(f'SELECT COALESCE(MAX(id),0) AS maximum FROM "{table}"').fetchone()["maximum"]
        if maximum:
            con.execute("SELECT setval(?, ?, true)", (sequence["sequence_name"], maximum))
        else:
            con.execute("SELECT setval(?, 1, false)", (sequence["sequence_name"],))


def is_integrity_error(exc: Exception) -> bool:
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    if is_mariadb():
        pymysql = _load_pymysql()
        return isinstance(exc, pymysql.err.IntegrityError)
    if is_postgresql():
        psycopg, _ = _load_psycopg()
        return isinstance(exc, psycopg.IntegrityError)
    return False


def init():
    con = connect()
    c = con.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, email VARCHAR(320) UNIQUE, password TEXT,
        name TEXT, role TEXT DEFAULT 'agent', active INTEGER DEFAULT 1,
        avatar TEXT DEFAULT '', target REAL DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, record_id INTEGER,
        body TEXT, user_id INTEGER, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, record_id INTEGER,
        action TEXT, changes TEXT, user_id INTEGER, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS line_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, record_id INTEGER,
        product_id INTEGER, name TEXT, qty REAL DEFAULT 1, price REAL DEFAULT 0,
        discount REAL DEFAULT 0, tax REAL DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS workflows(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, module TEXT, "trigger" TEXT,
        "field" TEXT, "operator" TEXT, "value" TEXT, action TEXT, action_value TEXT,
        active INTEGER DEFAULT 1, runs INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT,
        body TEXT, "read" INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings(
        "key" VARCHAR(255) PRIMARY KEY, "value" TEXT)""")

    for mod, meta in MODULES.items():
        cols = [BASE_COLS]
        for field in meta["fields"]:
            if field["name"] == "owner_id":
                continue
            cols.append(f'"{field["name"]}" {TYPE_SQL.get(field["type"], "TEXT")}')
        c.execute(f'CREATE TABLE IF NOT EXISTS "{mod}" ({", ".join(cols)})')
        existing = table_columns(con, mod)
        for field in meta["fields"]:
            if field["name"] not in existing:
                c.execute(
                    f'ALTER TABLE "{mod}" ADD COLUMN "{field["name"]}" '
                    f'{TYPE_SQL.get(field["type"], "TEXT")}'
                )
    con.commit()
    return con


def now():
    # Keep the existing UTC-naive storage format for SQLite compatibility while
    # avoiding the deprecated datetime.utcnow() API on modern Python.
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def log(con, module, rid, action, changes, uid):
    con.execute("INSERT INTO audit(module,record_id,action,changes,user_id,created_at) VALUES(?,?,?,?,?,?)",
                (module, rid, action, json.dumps(changes, ensure_ascii=False), uid, now()))
