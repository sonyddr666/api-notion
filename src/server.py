import os
from dotenv import load_dotenv
load_dotenv()  # deve rodar antes dos imports locais que leem env vars no nível do módulo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional
from .llm_processor import process_content
from .notion_client import create_page, query_database

app = FastAPI(title="api-notion", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class SaveRequest(BaseModel):
    """
    Aceita qualquer coisa no campo 'content'.
    Pode ser string, dict, código, mensagem, qualquer formato.
    """
    content: Any
    origin: str = "api"

class QueryRequest(BaseModel):
    type: Optional[str] = None
    language: Optional[str] = None
    tag: Optional[str] = None

def normalize_content(content: Any) -> str:
    """Converte qualquer tipo de entrada para string para processar."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict) or isinstance(content, list):
        import json
        return json.dumps(content, ensure_ascii=False, indent=2)
    return str(content)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-notion"}

@app.post("/save")
async def save(req: SaveRequest):
    if not req.content:
        raise HTTPException(400, "Conteúdo vazio")

    # conteúdo original normalizado
    original_str = normalize_content(req.content)

    try:
        # LLM processa e estrutura
        llm_meta = await process_content(original_str)
        llm_meta["origin"] = req.origin

        # Notion recebe os dois separados:
        # - original_str: o que chegou na API
        # - llm_meta: o que a LLM gerou
        page = await create_page(original_str, llm_meta)

        return {
            "ok": True,
            "notion_url": page.get("url"),
            "original": original_str[:500],  # preview do que chegou
            "llm": llm_meta                  # tudo que a LLM gerou
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/query")
async def query(req: QueryRequest):
    conditions = []
    if req.type:
        conditions.append({"property": "Tipo", "select": {"equals": req.type}})
    if req.language:
        conditions.append({"property": "Linguagem", "select": {"equals": req.language}})
    if req.tag:
        conditions.append({"property": "Tags", "multi_select": {"contains": req.tag}})

    filters = None
    if len(conditions) == 1:
        filters = conditions[0]
    elif len(conditions) > 1:
        filters = {"and": conditions}

    results = await query_database(filters)
    return {
        "count": len(results),
        "results": [
            {
                "title": r["properties"]["Título"]["title"][0]["text"]["content"]
                         if r["properties"]["Título"]["title"] else "",
                "type": r["properties"]["Tipo"]["select"]["name"]
                        if r["properties"]["Tipo"]["select"] else "",
                "url": r["url"]
            }
            for r in results
        ]
    }
