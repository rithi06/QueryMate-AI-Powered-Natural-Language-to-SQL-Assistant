"""SQL safety layer. The LLM output is untrusted: parse it, don't regex it."""
import sqlglot
from sqlglot import exp

class UnsafeSQL(ValueError):
    pass

# Any of these node types anywhere in the tree means the query can write or alter state.
FORBIDDEN = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
             exp.Command, exp.Pragma, exp.Attach, exp.Detach, exp.Transaction,
             exp.Commit, exp.Rollback, exp.Merge)

def validate_sql(sql: str, allowed_tables: set[str]) -> str:
    """Return the cleaned SQL if it is a single read-only SELECT over known tables, else raise UnsafeSQL."""
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise UnsafeSQL("Empty query.")
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as e:
        raise UnsafeSQL(f"Could not parse SQL: {str(e)[:200]}")
    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise UnsafeSQL("Only a single statement is allowed.")
    tree = statements[0]

    if not isinstance(tree, (exp.Select, exp.Union)):
        raise UnsafeSQL("Only SELECT queries are allowed.")
    for node in tree.walk():
        if isinstance(node, FORBIDDEN):
            raise UnsafeSQL(f"Forbidden operation: {type(node).__name__}.")

    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    allowed = {t.lower() for t in allowed_tables}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name not in allowed and name not in cte_names:
            raise UnsafeSQL(f"Unknown table: {table.name}.")
    return sql
