import os
import json
import httpx

FLUXO_CODEX_URL = os.getenv("FLUXO_CODEX_URL", "http://fluxo-codex:3000/v1/chat/completions")
MODEL_FULL = os.getenv("LLM_MODEL_FULL", "gpt-5.4")
MODEL_MINI = os.getenv("LLM_MODEL_MINI", "gpt-5.4-mini")

SYSTEM_PROMPT = """
Você é um classificador de conteúdo técnico.
Analise o conteúdo recebido e devolva SOMENTE um JSON válido com estes campos:

- title (string)
- type: codigo | snippet | ideia | bug | explicacao | referencia
- summary_short (string, máx 100 chars)
- summary_detailed (string, máx 500 chars)
- tags (array de strings, máx 5)
- language: javascript | typescript | python | go | bash | none
- importance (inteiro 1-10)
- has_code (bool)
- key_points (array de strings, máx 3)
- search_terms (array de strings, máx 5)
"""

def pick_model(content: str) -> str:
    """gpt-5.4 pra conteúdo longo ou com código, gpt-5.4-mini pro resto."""
    return MODEL_FULL if len(content) > 1500 or "```" in content else MODEL_MINI

async def process_content(content: str) -> dict:
    model = pick_model(content)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        "temperature": 0.2
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(FLUXO_CODEX_URL, json=payload)
        r.raise_for_status()
        data = r.json()

    raw = data["choices"][0]["message"]["content"].strip()

    # codex às vezes envolve em ```json ... ```
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
