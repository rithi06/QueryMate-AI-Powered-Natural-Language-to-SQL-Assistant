# AI-Powered Natural Language to SQL Assistant

Ask questions about a retail sales database in plain English. The app generates SQL with an LLM,
validates it, runs it safely (read-only), and shows the **SQL, a plain-English explanation, a results table and a chart**.

## Architecture

```
question → schema.py (tables, columns, sample rows, business rules)
         → prompt.py + llm.py (LLM generates SQLite SELECT)
         → validator.py (sqlglot AST check: single SELECT, known tables only)
         → executor.py (read-only connection, row cap, timeout)
         → on error: feed error back to the LLM, retry once
         → app.py (Flask API) → templates/index.html (table + Chart.js)
```

## Safety (defence in depth)

1. **Prompt rules**: SELECT only, schema-only.
2. **AST validation** (`sqlglot`): rejects multi-statement input, any INSERT/UPDATE/DELETE/DROP/ALTER/PRAGMA/ATTACH, and unknown tables (including `sqlite_master`).
3. **Read-only DB connection** (`mode=ro` + `PRAGMA query_only`): even if 1 and 2 failed, writes are impossible.
4. **Limits**: max 200 rows returned, 5-second hard timeout, 500-character question cap.

## Run it

```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key                   # Windows: set ANTHROPIC_API_KEY=your-key
python seed_db.py                                   # builds data/retail.db (synthetic, 4 related tables)
python app.py                                       # open http://127.0.0.1:5000
```

## Tests and evaluation

```bash
python -m pytest tests -q          # 18 tests, no API key needed (uses a fake LLM)
python -m eval.run_eval            # execution accuracy on 12 gold questions (needs API key)
```

`eval/run_eval.py` runs each question through the full pipeline and checks that the result rows match the
gold SQL's rows. Record your accuracy number here after running it:

| Model | Execution accuracy |
|-------|--------------------|
| (fill in) | (fill in)/12 |

Add more questions to `eval/questions.json` (aim for 30+, including joins, date logic and unanswerable questions).

## Use your own data

Load any CSV into SQLite with pandas (`df.to_sql("table", conn)`), save it as `data/retail.db`
(or set `NL2SQL_DB`), and update `BUSINESS_NOTES` in `schema.py` with your metric definitions.
The Superstore or Olist datasets work well.

## Ideas to extend

- Conversation memory ("now break that down by region")
- Few-shot examples retrieved per question
- Schema pruning for large databases (only send relevant tables)
- Auth + per-user query logs; deploy on Render/Railway
