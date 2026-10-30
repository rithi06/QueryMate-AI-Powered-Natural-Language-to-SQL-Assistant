"""question -> schema prompt -> LLM -> validate -> execute (-> retry once on failure)."""
import sqlite3
from datetime import date
import schema as schema_mod
from validator import validate_sql, UnsafeSQL
from executor import connect_readonly, run_query, QueryTimeout
from config import MAX_RETRIES

def ask(question: str, conn=None, llm=None, explain: bool = True) -> dict:
    if llm is None:
        import llm as llm  # lazy import so tests don't need an API key
    conn = conn or connect_readonly()
    schema_text = schema_mod.get_schema_text(conn)
    allowed = set(schema_mod.table_names(conn))
    today, data_range = date.today().isoformat(), schema_mod.get_date_range(conn)

    sql, error, attempts = None, None, 0
    for attempt in range(MAX_RETRIES + 1):
        attempts = attempt + 1
        raw = llm.generate_sql(question, schema_text, today, data_range, prev_sql=sql if error else None, error=error)
        sql = raw
        try:
            sql = validate_sql(raw, allowed)
            result = run_query(conn, sql)
        except UnsafeSQL as e:
            error = f"Blocked by safety check: {e}"
            continue
        except QueryTimeout as e:
            return {"ok": False, "sql": sql, "error": str(e), "attempts": attempts}
        except sqlite3.Error as e:
            error = f"SQLite error: {e}"
            continue
        if result["columns"] == ["message"] and result["rows"] == [["UNANSWERABLE"]]:
            return {"ok": False, "sql": sql, "attempts": attempts,
                    "error": "That question can't be answered from this database's tables."}
        out = {"ok": True, "sql": sql, "attempts": attempts, **result}
        if explain:
            try:
                out["explanation"] = llm.explain_sql(question, sql)
            except Exception:
                out["explanation"] = None
        return out
    return {"ok": False, "sql": sql, "error": error, "attempts": attempts}
