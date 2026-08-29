"""Static regression guard for the MySQL 8 SQL dialect.

The application intentionally keeps SQLite-style source SQL so it can run with
SQLite, MariaDB, PostgreSQL, and MySQL. This test inventories every literal SQL
statement sent through the application connection and verifies its MySQL 8
translation has no known SQLite-only syntax left behind.
"""
from __future__ import annotations

import ast
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# These modules intentionally inspect a SQLite source database during migration.
# db.py itself owns the per-engine implementation and is tested separately.
EXCLUDED_MODULES = {
    "db.py",
    "migrate_mariadb.py",
    "migrate_postgresql.py",
}
SQL_START = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|REPLACE)\b", re.IGNORECASE)
SQLITE_REMAINDERS = (
    re.compile(r"\bON\s+CONFLICT\b", re.IGNORECASE),
    re.compile(r"\bAUTOINCREMENT\b", re.IGNORECASE),
    re.compile(r"\bINSERT\s+OR\s+(?:REPLACE|IGNORE)\b", re.IGNORECASE),
    re.compile(r"\bCOLLATE\s+NOCASE\b", re.IGNORECASE),
    re.compile(r"\bdate\s*\(\s*'now'\s*\)", re.IGNORECASE),
    re.compile(r"\bCAST\s*\([^)]*\s+AS\s+INTEGER\s*\)", re.IGNORECASE),
)


def string_expression(node: ast.AST) -> str | None:
    """Resolve string literals and preserve f-string expression locations."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "__DYNAMIC__"
            for part in node.values
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = string_expression(node.left), string_expression(node.right)
        return left + right if left is not None and right is not None else None
    return None


def sql_literals() -> list[tuple[Path, int, str]]:
    """Return literal/f-string SQL passed directly to execute/executemany."""
    statements: list[tuple[Path, int, str]] = []
    for path in sorted(ROOT.glob("*.py")):
        if path.name in EXCLUDED_MODULES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for call in ast.walk(tree):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr in {"execute", "executemany"}
                and call.args
            ):
                continue
            statement = string_expression(call.args[0])
            if statement and SQL_START.match(statement):
                statements.append((path, call.lineno, statement))
    return statements


class MySQL8SQLCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load an isolated copy so this static audit cannot set DB_PATH before
        # the API suite chooses its temporary SQLite test database.
        spec = importlib.util.spec_from_file_location("nebras_mysql8_audit_db", ROOT / "db.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        cls.db = module
        cls.statements = sql_literals()

    def test_inventory_is_nonempty_and_has_no_strict_group_or_nocase_source(self):
        self.assertGreaterEqual(len(self.statements), 100)
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in ROOT.glob("*.py")
            if path.name not in EXCLUDED_MODULES
        )
        self.assertNotRegex(source, r"\bCOLLATE\s+NOCASE\b")
        self.assertNotRegex(source, r"\bGROUP\s+BY\s+(?:1|k)\b")

    def test_every_literal_application_query_translates_without_sqlite_only_syntax(self):
        db = self.db
        original_engine, original_mode = db.DB_ENGINE, db.MYSQL8_MODE
        try:
            db.DB_ENGINE, db.MYSQL8_MODE = "mariadb", True
            for path, line, statement in self.statements:
                translated = db._translate_sql(statement)
                label = f"{path.name}:{line}: {translated!r}"
                for pattern in SQLITE_REMAINDERS:
                    self.assertIsNone(pattern.search(translated), label)
                self.assertNotIn("?", translated, label)
        finally:
            db.DB_ENGINE, db.MYSQL8_MODE = original_engine, original_mode

    def test_mysql8_schema_initializers_emit_only_translated_sql(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "mysql8_schema_audit.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("MySQL 8 schema audit passed", result.stdout)

    def test_every_application_upsert_uses_mysql8_row_alias_syntax(self):
        db = self.db
        upserts = [item for item in self.statements if "ON CONFLICT" in item[2].upper()]
        self.assertGreaterEqual(len(upserts), 5)
        original_engine, original_mode = db.DB_ENGINE, db.MYSQL8_MODE
        try:
            db.DB_ENGINE, db.MYSQL8_MODE = "mariadb", True
            for path, line, statement in upserts:
                translated = db._translate_sql(statement)
                label = f"{path.name}:{line}: {translated!r}"
                self.assertIn("AS new_row ON DUPLICATE KEY UPDATE", translated, label)
                self.assertNotIn("excluded.", translated.lower(), label)
                self.assertNotRegex(translated, r"VALUES\s*\(\s*`?[A-Za-z_]", label)
        finally:
            db.DB_ENGINE, db.MYSQL8_MODE = original_engine, original_mode


if __name__ == "__main__":
    unittest.main()
