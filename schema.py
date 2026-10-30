"""Reads the live database schema and builds the text the LLM sees."""
import sqlite3

# Business definitions the model cannot infer from column names alone.
BUSINESS_NOTES = """\
- Revenue of an order line = order_items.quantity * products.unit_price * (1 - order_items.discount)
- Profit of an order line = revenue - order_items.quantity * products.unit_cost
- Dates are stored as ISO text 'YYYY-MM-DD'. Use strftime()/date() for date logic.
- order_items links orders to products; orders links to customers.
"""

def table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return [r[0] for r in rows]

def table_columns(conn: sqlite3.Connection) -> dict[str, set[str]]:
    return {t: {r[1].lower() for r in conn.execute(f'PRAGMA table_info("{t}")')} for t in table_names(conn)}

def get_schema_text(conn: sqlite3.Connection, sample_rows: int = 3) -> str:
    parts = []
    for t in table_names(conn):
        ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name=?", (t,)).fetchone()[0]
        cur = conn.execute(f'SELECT * FROM "{t}" LIMIT {int(sample_rows)}')
        cols = [c[0] for c in cur.description]
        samples = "\n".join("  " + " | ".join(map(str, r)) for r in cur.fetchall())
        parts.append(f"{ddl.strip()}\n-- sample rows ({' | '.join(cols)}):\n{samples}")
    return "\n\n".join(parts) + "\n\nBusiness definitions:\n" + BUSINESS_NOTES

def get_date_range(conn: sqlite3.Connection) -> str:
    try:
        lo, hi = conn.execute("SELECT MIN(order_date), MAX(order_date) FROM orders").fetchone()
        return f"{lo} to {hi}"
    except sqlite3.Error:
        return "unknown"
