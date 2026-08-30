import sqlite3
import os
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "qualiq.db")

def get_db_path() -> str:
    os.makedirs(DB_DIR, exist_ok=True)
    return DB_PATH

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Enforces foreign keys, enables WAL mode, and returns sqlite3.Row objects.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
