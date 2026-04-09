import os
import json
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

async def process_content(content: str) -> dict:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    return json.loads(response.choices[0].message.content)
