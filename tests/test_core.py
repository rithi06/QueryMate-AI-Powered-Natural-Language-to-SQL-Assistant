import os, sys, json, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import seed_db, pipeline, schema
from validator import validate_sql, UnsafeSQL
from executor import connect_readonly, run_query, QueryTimeout

TABLES = {"customers", "products", "orders", "order_items"}

@pytest.fixture(scope="module")
def conn():
    seed_db.main()
    return connect_readonly()

def test_accepts_select_join_cte_union():
    validate_sql("SELECT * FROM orders o JOIN customers c ON c.customer_id=o.customer_id", TABLES)
    validate_sql("WITH t AS (SELECT * FROM orders) SELECT COUNT(*) FROM t", TABLES)
    validate_sql("SELECT 1 UNION SELECT 2", TABLES)

@pytest.mark.parametrize("bad", [
    "DROP TABLE orders", "DELETE FROM orders", "UPDATE orders SET ship_mode='x'",
    "INSERT INTO customers VALUES (1,'a','b','c','d','e')", "PRAGMA table_info(orders)",
    "SELECT 1; DROP TABLE orders", "ATTACH DATABASE 'x.db' AS x", "SELECT * FROM sqlite_master",
    "SELECT * FROM secret_table", "",
])
def test_blocks_unsafe(bad):
    with pytest.raises(UnsafeSQL):
        validate_sql(bad, TABLES)

def test_readonly_connection_blocks_writes(conn):
    with pytest.raises(Exception):
        conn.execute("DELETE FROM orders")

def test_row_cap_and_truncation(conn):
    r = run_query(conn, "SELECT * FROM order_items", max_rows=10)
    assert len(r["rows"]) == 10 and r["truncated"]

def test_timeout(conn):
    slow = ("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<100000000) "
            "SELECT COUNT(*) FROM n")
    with pytest.raises(QueryTimeout):
        run_query(conn, slow, timeout_s=0.5)

def test_gold_queries_all_run(conn):
    cases = json.load(open(os.path.join(os.path.dirname(__file__), "..", "eval", "questions.json")))
    for c in cases:
        assert run_query(conn, c["gold"], max_rows=10_000)["rows"], c["q"]

class FakeLLM:
    """First answer references a bad column -> pipeline must retry with the error and succeed."""
    def generate_sql(self, q, schema_text, today, rng, prev_sql=None, error=None):
        return "SELECT COUNT(*) FROM orders" if error else "SELECT COUNT(nope) FROM orders"
    def explain_sql(self, q, sql): return "Counts orders."

def test_pipeline_self_corrects(conn):
    out = pipeline.ask("how many orders?", conn=conn, llm=FakeLLM())
    assert out["ok"] and out["attempts"] == 2 and out["rows"][0][0] == 2500

def test_pipeline_blocks_malicious_llm_output(conn):
    class Evil(FakeLLM):
        def generate_sql(self, *a, **k): return "DROP TABLE orders"
    out = pipeline.ask("x", conn=conn, llm=Evil())
    assert not out["ok"] and "Blocked" in out["error"]
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 2500

def test_schema_text_mentions_all_tables(conn):
    text = schema.get_schema_text(conn)
    assert all(t in text for t in TABLES) and "Revenue" in text
