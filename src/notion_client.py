import os
import httpx

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
BASE_URL = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

async def create_page(original: str, meta: dict) -> dict:
    """
    Salva no Notion separando claramente:
    - original: conteúdo bruto recebido pela API
    - meta: dados estruturados gerados pela LLM
    """
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Título": {"title": [{"text": {"content": meta.get("title", "Sem título")}}]},
            "Tipo": {"select": {"name": meta.get("type", "snippet")}},
            "Resumo": {"rich_text": [{"text": {"content": meta.get("summary_short", "")[:2000]}}]},
            "Tags": {"multi_select": [{"name": t} for t in meta.get("tags", [])]},
            "Linguagem": {"select": {"name": meta.get("language", "none")}},
            "Importância": {"number": meta.get("importance", 5)},
            "Tem Código": {"checkbox": meta.get("has_code", False)},
        },
        "children": [
            # --- BLOCO 1: dados da LLM ---
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🤖 Dados Processados pela LLM"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": meta.get("summary_detailed", "")[:2000]}}]}
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": "Pontos-chave: " + " | ".join(meta.get("key_points", []))}}],
                    "icon": {"emoji": "💡"}
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": "Termos de busca: " + ", ".join(meta.get("search_terms", []))}}],
                    "icon": {"emoji": "🔍"}
                }
            },
            # --- BLOCO 2: conteúdo original ---
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📥 Conteúdo Original Recebido"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": original[:1900]}}]}
            }
        ]
    }
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/pages", headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.json()

async def query_database(filters: dict = None) -> list:
    body = {"page_size": 20}
    if filters:
        body["filter"] = filters
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE_URL}/databases/{DATABASE_ID}/query", headers=HEADERS, json=body)
        r.raise_for_status()
        return r.json().get("results", [])
