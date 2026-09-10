import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "medikiosk.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db_context():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection):
    expected_columns = {
        "users": [("profile_image_data", "BLOB")],
        "doctors": [
            ("age", "INTEGER"),
            ("license_file", "BLOB"),
            ("license_filename", "TEXT"),
            ("pass_certificate", "BLOB"),
            ("pass_certificate_filename", "TEXT"),
        ],
        "appointments": [
            ("ai_summary", "TEXT"),
            ("ai_chat_history", "TEXT"),
        ],
    }
    for table, columns in expected_columns.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for column, ctype in columns:
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ctype}")
    conn.commit()


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = get_db()
    try:
        with open(schema_path, "r") as f:
            conn.executescript(f.read())
        _migrate(conn)
    finally:
        conn.close()


def execute_query(query: str, params: tuple = (), fetch: bool = False):
    conn = get_db()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        if fetch:
            return cursor.fetchall()
        return cursor.lastrowid
    finally:
        conn.close()


def execute_many(query: str, params_list: list):
    conn = get_db()
    try:
        conn.executemany(query, params_list)
        conn.commit()
    finally:
        conn.close()
