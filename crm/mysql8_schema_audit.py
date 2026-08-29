#!/usr/bin/env python3
"""Audit generated NebrasCRM schema SQL for MySQL 8 without a running server.

This is a developer/release check. It records every schema statement emitted by
all initializers through the real MySQL compatibility layer and rejects known
SQLite-only constructs before a Docker build is shipped.
"""
from __future__ import annotations

import re
import sys

import agentportal as AP
import db as D
import geo as GEO
import loyalty as LOY
import mailer as M
import partners as PT
import payments as PAY
import platform_ext as PF
import portal as P
import pos as POS

PROHIBITED = (
    re.compile(r"\bON\s+CONFLICT\b", re.IGNORECASE),
    re.compile(r"\bAUTOINCREMENT\b", re.IGNORECASE),
    re.compile(r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\b", re.IGNORECASE),
    re.compile(r"\bCOLLATE\s+NOCASE\b", re.IGNORECASE),
    re.compile(r"\bdate\s*\(\s*'now'\s*\)", re.IGNORECASE),
    re.compile(r"\bCAST\s*\([^)]*\s+AS\s+INTEGER\s*\)", re.IGNORECASE),
)


class RecorderCursor:
    def __init__(self, connection):
        self.connection = connection
        self.lastrowid = 0
        self.rowcount = 0

    def execute(self, sql, params=()):
        self.connection.statements.append(sql)
        self.rowcount = 1

    def executemany(self, sql, params):
        self.connection.statements.append(sql)
        self.rowcount = 1

    def fetchone(self):
        # An empty metadata result asks each initializer to emit all safe
        # ALTER/CREATE paths, maximizing the audit coverage.
        return None

    def fetchall(self):
        return []

    def __iter__(self):
        return iter(())

    def close(self):
        pass


class RecorderConnection:
    def __init__(self):
        self.statements: list[str] = []

    def cursor(self):
        return RecorderCursor(self)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def main() -> int:
    raw = RecorderConnection()
    original_connect = D.connect
    original_engine = D.DB_ENGINE
    original_mysql8_mode = D.MYSQL8_MODE
    original_import = GEO.import_world_dataset
    try:
        D.DB_ENGINE = "mariadb"
        D.MYSQL8_MODE = True
        D.connect = lambda: D.MariaConnection(raw)
        # Geography import has 235k rows and is covered by its own data tests;
        # this schema audit focuses on emitted SQL definitions and migrations.
        GEO.import_world_dataset = lambda connection, force=False: {"ok": True}

        con = D.init()
        P.init_tables(con)
        M.init_tables(con)
        PAY.init_tables(con)
        POS.init_tables(con)
        GEO.init_tables(con)
        PT.init_tables(con)
        LOY.init_tables(con)
        AP.init_tables(con)
        PF.init_tables(con)
    finally:
        D.connect = original_connect
        D.DB_ENGINE = original_engine
        D.MYSQL8_MODE = original_mysql8_mode
        GEO.import_world_dataset = original_import

    if len(raw.statements) < 100:
        raise RuntimeError(f"Schema audit unexpectedly saw only {len(raw.statements)} statements.")
    for statement in raw.statements:
        for pattern in PROHIBITED:
            if pattern.search(statement):
                raise RuntimeError(f"MySQL 8 incompatibility: {statement}")
        if "?" in statement:
            raise RuntimeError(f"Untranslated qmark placeholder: {statement}")

    pos_ddl = next((sql for sql in raw.statements if "CREATE TABLE IF NOT EXISTS pos_sales" in sql), "")
    if "created_at VARCHAR(40)" not in pos_ddl:
        raise RuntimeError("POS created_at is not indexable under MySQL 8.")
    if not any("ix_pos_sales_created" in sql for sql in raw.statements):
        raise RuntimeError("POS created_at index was not emitted.")

    print(f"MySQL 8 schema audit passed: {len(raw.statements)} translated statements.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"MySQL 8 schema audit failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
