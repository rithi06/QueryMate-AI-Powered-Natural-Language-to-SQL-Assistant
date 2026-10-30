# QueryMate: AI-Powered Natural Language to SQL Assistant

Ask questions about a retail sales database in plain English. QueryMate generates the SQL with an LLM,
validates it, runs it on a read-only connection, and shows the **results table, a chart, and the SQL behind every answer**.

**Live demo:** https://querymate-r1wb.onrender.com
*(The free tier sleeps when idle, so the first load can take up to a minute.)*


## Example questions

- What is the total revenue by year?
- Top 5 product categories by revenue
- Which region has the highest profit?
- Average discount by category

## Tech stack

Python, Flask, SQLite, Google Gemini API (`google-genai`), sqlglot, Chart.js, pytest, gunicorn. Deployed on Render.

## Architecture

```
question → schema.py (tables, columns, sample rows, business rules)
         → prompt.py + llm.py (LLM generates a SQLite SELECT)
         → validator.py (sqlglot AST check: single SELECT, known tables only)
         → executor.py (read-only connection, row cap, timeout)
         → on error: feed the error back to the LLM, retry once
         → app.py (Flask API, rate limited) → templates/index.html (table + chart)
```

## Safety (defence in depth)

1. **Prompt rules**: SELECT only, schema tables only.
2. **AST validation** (`sqlglot`): rejects multi-statement input, any INSERT/UPDATE/DELETE/DROP/ALTER/PRAGMA/ATTACH, and unknown tables (including `sqlite_master`).
3. **Read-only DB connection** (`mode=ro` + `PRAGMA query_only`): even if layers 1 and 2 failed, writes are impossible.
4. **Limits**: max 200 rows returned, 5-second query timeout, 500-character question cap.
5. **Rate limiting**: 10 questions per minute per IP (`flask-limiter`) to protect API usage.

## Run it locally

```bash
python -m venv venv
venv\Scripts\activate                # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Set your Gemini API key (get one at https://aistudio.google.com/apikey):

```bash
set GEMINI_API_KEY=your-key          # PowerShell: $env:GEMINI_API_KEY="your-key"
                                     # Mac/Linux: export GEMINI_API_KEY=your-key
```

Or create a `.env` file containing `GEMINI_API_KEY=your-key`.

```bash
python seed_db.py                    # builds data/retail.db (synthetic, 4 related tables)
python app.py                        # open http://127.0.0.1:5000
```

The model defaults to `gemini-3.5-flash-lite`. Override it with the `NL2SQL_MODEL` environment variable.

## Tests and evaluation

```bash
python -m pytest tests -q            # 18 tests, no API key needed (uses a fake LLM)
python -m eval.run_eval              # execution accuracy on 12 gold questions (needs GEMINI_API_KEY)
```

`eval/run_eval.py` runs each question through the full pipeline and checks that the result rows match the
gold SQL's rows.

| Model | Execution accuracy |
|-------|--------------------|
| gemini-3.5-flash-lite | X / 12 |

## Deploy on Render

1. Push this repo to GitHub.
2. On Render, create a new **Web Service** from the repo.
3. Build command: `pip install -r requirements.txt && python seed_db.py`
4. Start command: `gunicorn app:app`
5. Add the environment variable `GEMINI_API_KEY`.

## Use your own data

Load any CSV into SQLite with pandas (`df.to_sql("table", conn)`), save it as `data/retail.db`
(or set `NL2SQL_DB`), and update `BUSINESS_NOTES` in `schema.py` with your metric definitions.
The Superstore or Olist datasets work well.

## Limitations and future work

- Single-turn questions only; no conversation memory ("now break that down by region")
- Schema is sent in full, so very large databases would need schema pruning
- Accuracy depends on the model and the quality of the business definitions in `schema.py`
- Planned: few-shot examples retrieved per question, per-user query logs