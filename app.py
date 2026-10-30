from collections import deque
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
import pipeline
from executor import connect_readonly

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)   # lets the limiter see the visitor's real IP on Render
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

conn = connect_readonly()
history = deque(maxlen=20)

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify(ok=False, error="Too many questions. Please wait a minute and try again."), 429

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/ask")
@limiter.limit("10 per minute")
def api_ask():
    question = (request.get_json(silent=True) or {}).get("question", "").strip()
    if not question or len(question) > 500:
        return jsonify(ok=False, error="Enter a question (max 500 characters)."), 400
    try:
        result = pipeline.ask(question, conn=conn, explain=False)
    except Exception as e:
        return jsonify(ok=False, error=f"Server error: {type(e).__name__}: {e}"), 500
    history.appendleft({"question": question, "ok": result["ok"], "sql": result.get("sql")})
    return jsonify(result)

@app.get("/api/history")
def api_history():
    return jsonify(list(history))

if __name__ == "__main__":
    app.run(debug=True)