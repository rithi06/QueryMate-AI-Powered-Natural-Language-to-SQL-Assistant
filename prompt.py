SYSTEM_PROMPT = """You are a careful data analyst who writes SQLite queries.

Rules:
- Output exactly ONE read-only SQLite SELECT statement inside a ```sql code block. No other text.
- Use ONLY the tables and columns in the schema. Never invent columns.
- SQLite dialect: use strftime('%Y-%m', col), date('now', '-3 months'), no YEAR()/MONTH()/DATE_SUB().
- Use the business definitions for revenue/profit.
- Give computed columns clear aliases. Round money to 2 decimals.
- If the question cannot be answered from the schema, return:  SELECT 'UNANSWERABLE' AS message;
"""

def build_user_prompt(question: str, schema: str, today: str, data_range: str,
                      prev_sql: str | None = None, error: str | None = None) -> str:
    p = (f"Schema:\n{schema}\n\n"
         f"Today's date: {today}. The data covers orders from {data_range}.\n"
         f"Interpret relative dates (e.g. 'last quarter', 'this year') against the latest date in the data.\n\n"
         f"Question: {question}\n")
    if prev_sql and error:
        p += f"\nYour previous attempt failed.\nSQL:\n{prev_sql}\nError: {error}\nFix it and return the corrected query.\n"
    return p

EXPLAIN_PROMPT = ("Explain in 1-2 plain-English sentences what this SQL query does, "
                  "for a non-technical business user. No SQL jargon.\n\nQuestion: {q}\nSQL:\n{sql}")
