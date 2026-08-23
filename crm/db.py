import sqlite3, json, os, datetime
from schema import MODULES

# Allow deployments and tests to place the SQLite file outside the source tree.
# Existing installations continue to use crm/crm.db when CRM_DB_PATH is omitted.
DB_PATH = os.path.abspath(os.path.expanduser(
    os.environ.get("CRM_DB_PATH") or os.path.join(os.path.dirname(__file__), "crm.db")
))

BASE_COLS = """
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT, updated_at TEXT,
  created_by INTEGER, owner_id INTEGER,
  deleted INTEGER DEFAULT 0,
  tags TEXT DEFAULT ''
"""

TYPE_SQL = {"number": "REAL", "currency": "REAL"}


def connect():
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # A small busy timeout prevents normal concurrent web requests from failing
    # immediately while another request is committing a SQLite transaction.
    con = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init():
    con = connect()
    c = con.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT,
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
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, module TEXT, trigger TEXT,
        field TEXT, operator TEXT, value TEXT, action TEXT, action_value TEXT,
        active INTEGER DEFAULT 1, runs INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT,
        body TEXT, read INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY, value TEXT)""")

    for mod, meta in MODULES.items():
        cols = [BASE_COLS]
        for f in meta["fields"]:
            if f["name"] == "owner_id":
                continue
            cols.append(f'"{f["name"]}" {TYPE_SQL.get(f["type"], "TEXT")}')
        c.execute(f'CREATE TABLE IF NOT EXISTS "{mod}" ({", ".join(cols)})')
        # additive migration
        existing = {r["name"] for r in c.execute(f'PRAGMA table_info("{mod}")')}
        for f in meta["fields"]:
            if f["name"] not in existing:
                c.execute(f'ALTER TABLE "{mod}" ADD COLUMN "{f["name"]}" {TYPE_SQL.get(f["type"],"TEXT")}')
    con.commit()
    return con


def now():
    # Keep the existing UTC-naive storage format for SQLite compatibility while
    # avoiding the deprecated datetime.utcnow() API on modern Python.
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds")


def log(con, module, rid, action, changes, uid):
    con.execute("INSERT INTO audit(module,record_id,action,changes,user_id,created_at) VALUES(?,?,?,?,?,?)",
                (module, rid, action, json.dumps(changes, ensure_ascii=False), uid, now()))
