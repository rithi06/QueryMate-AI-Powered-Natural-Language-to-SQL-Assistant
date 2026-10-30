"""Execution-accuracy evaluation: does the generated SQL return the same rows as the gold SQL?

Usage:  python -m eval.run_eval
Needs ANTHROPIC_API_KEY. Comparison ignores row order and column names (rounds floats to 2dp).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pipeline
from executor import connect_readonly, run_query

def norm(rows):
    return sorted(tuple(round(v, 2) if isinstance(v, float) else v for v in r) for r in rows)

def main():
    conn = connect_readonly()
    cases = json.load(open(os.path.join(os.path.dirname(__file__), "questions.json")))
    results, correct = [], 0
    for c in cases:
        gold = run_query(conn, c["gold"], max_rows=10_000)["rows"]
        out = pipeline.ask(c["q"], conn=conn, explain=False)
        ok = out["ok"] and norm(out["rows"]) == norm(gold)
        correct += ok
        results.append({"question": c["q"], "correct": ok, "attempts": out.get("attempts"),
                        "generated_sql": out.get("sql"), "error": out.get("error")})
        print(("PASS" if ok else "FAIL"), "-", c["q"])
    acc = correct / len(cases)
    print(f"\nExecution accuracy: {correct}/{len(cases)} = {acc:.0%}")
    json.dump({"accuracy": acc, "results": results}, open(os.path.join(os.path.dirname(__file__), "results.json"), "w"), indent=2)

if __name__ == "__main__":
    main()
