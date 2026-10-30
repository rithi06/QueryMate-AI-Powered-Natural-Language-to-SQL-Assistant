import os

DB_PATH = os.getenv("NL2SQL_DB", os.path.join(os.path.dirname(__file__), "data", "retail.db"))
MAX_ROWS = 200          # rows returned to the UI
QUERY_TIMEOUT_S = 5     # hard timeout per query
MAX_RETRIES = 1         # LLM self-correction attempts after a failed query
