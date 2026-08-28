#!/usr/bin/env python3
"""Copy an existing NebrasCRM SQLite database into configured PostgreSQL.

Usage:
    CRM_DB_ENGINE=postgresql ... python3 migrate_postgresql.py --source crm.db --replace

The target PostgreSQL schema is initialized automatically. Global geography is not
copied from SQLite: it is rebuilt from NebrasCRM's bundled GeoNames dataset.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Migrate NebrasCRM SQLite data to PostgreSQL")
    parser.add_argument("--source", default="crm.db", help="path to source SQLite database")
    parser.add_argument(
        "--replace", action="store_true",
        help="delete existing importable PostgreSQL data before importing (required for a clean migration)",
    )
    return parser.parse_args()


def sqlite_tables(source):
    return {
        row["name"]
        for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not row["name"].startswith("sqlite_") and not row["name"].startswith("geo_")
    }


def main():
    args = parse_args()
    source_path = Path(args.source).expanduser().resolve()
    if not source_path.is_file():
        raise SystemExit(f"Source SQLite database not found: {source_path}")
    if os.environ.get("CRM_DB_ENGINE", "").lower() not in {"postgresql", "postgres"}:
        raise SystemExit("Set CRM_DB_ENGINE=postgresql and CRM_DB_HOST/PORT/NAME/USER/PASSWORD first.")
    if not args.replace:
        raise SystemExit("Pass --replace after backing up PostgreSQL to avoid mixing existing data.")

    # Import after configuration validation so main.py creates the PostgreSQL schema.
    import db as D
    import main as APP

    source = sqlite3.connect(source_path)
    source.row_factory = sqlite3.Row
    target = APP.con
    source_tables = sqlite_tables(source)
    target_tables = D.list_tables(target)
    tables = sorted(source_tables & target_tables)
    if not tables:
        raise SystemExit("No importable tables were found in the source database.")

    # No foreign keys are declared in NebrasCRM's metadata schema, but deleting
    # children first is still clearer in administrative logs.
    if args.replace:
        for table in reversed(tables):
            target.execute(f'DELETE FROM "{table}"')
        target.commit()

    total_rows = 0
    for table in tables:
        source_columns = [row["name"] for row in source.execute(f'PRAGMA table_info("{table}")')]
        target_columns = D.table_columns(target, table)
        columns = [column for column in source_columns if column in target_columns]
        if not columns:
            continue
        quoted = ",".join(f'"{column}"' for column in columns)
        placeholders = ",".join("?" for _ in columns)
        insert_sql = f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})'
        rows = source.execute(f'SELECT {quoted} FROM "{table}"').fetchall()
        if rows:
            cursor = target.cursor()
            cursor.executemany(insert_sql, [[row[column] for column in columns] for row in rows])
            total_rows += len(rows)
            print(f"  {table}: {len(rows)} rows")

    target.commit()
    # SQLite exports explicit id values. PostgreSQL serial sequences must be
    # advanced afterwards or the next insert would try to reuse id=1.
    D.sync_identity(target, tables)
    target.commit()
    source.close()
    print(f"Migration complete: {total_rows} rows copied into PostgreSQL.")
    print("Global geography was initialized from data/geonames/ and was not copied from SQLite.")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
