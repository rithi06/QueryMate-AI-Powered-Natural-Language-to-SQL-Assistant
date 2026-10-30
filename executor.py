"""Runs validated SQL on a read-only connection with a row cap and a hard timeout."""
import sqlite3, time
from config import DB_PATH, MAX_ROWS, QUERY_TIMEOUT_S

def connect_readonly(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)
    conn.execute("PRAGMA query_only = ON")
    return conn

class QueryTimeout(Exception):
    pass

def run_query(conn: sqlite3.Connection, sql: str, max_rows: int = MAX_ROWS, timeout_s: float = QUERY_TIMEOUT_S) -> dict:
    deadline = time.monotonic() + timeout_s
    # SQLite calls this every N VM steps; returning non-zero aborts the query.
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10_000)
    try:
        cur = conn.execute(sql)
        columns = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchmany(max_rows + 1)
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            raise QueryTimeout(f"Query exceeded {timeout_s}s and was stopped.")
        raise
    finally:
        conn.set_progress_handler(None, 0)
    truncated = len(rows) > max_rows
    return {"columns": columns, "rows": [list(r) for r in rows[:max_rows]], "truncated": truncated}
