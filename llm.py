
import os
import re
from google import genai
from prompt import SYSTEM_PROMPT, build_user_prompt, EXPLAIN_PROMPT
from dotenv import load_dotenv
load_dotenv()

MODEL = os.getenv("NL2SQL_MODEL", "gemini-3.5-flash-lite")
_client = None



def _complete(system: str, user: str, max_tokens: int = 700) -> str:
    response = _get_client().models.generate_content(
        model=MODEL,
        contents=user,
        config={
            "system_instruction": system,
            "max_output_tokens": max_tokens,
        },
    )
    return response.text or ""


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options={"timeout": 30000},
        )
    return _client

def extract_sql(text: str) -> str:
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    return (m.group(1) if m else text).strip()


def generate_sql(question, schema, today, data_range, prev_sql=None, error=None) -> str:
    user = build_user_prompt(
        question, schema, today, data_range, prev_sql, error
    )
    return extract_sql(_complete(SYSTEM_PROMPT, user))


def explain_sql(question: str, sql: str) -> str:
    return _complete(
        "You explain SQL to business users.",
        EXPLAIN_PROMPT.format(q=question, sql=sql),
        200,
    ).strip()
