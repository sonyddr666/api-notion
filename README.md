# api-notion

API que recebe qualquer conteúdo, processa via LLM e salva estruturado no Notion.

O dado salvo é separado em dois blocos claros:
- **📥 Conteúdo Original Recebido** — exatamente o que chegou na API
- **🤖 Dados Processados pela LLM** — resumo, tags, tipo, pontos-chave etc.

## Endpoints

### `POST /save`
Recebe qualquer conteúdo (string, JSON, código, mensagem) e salva no Notion.

```json
{
  "content": "qualquer coisa aqui",
  "origin": "telegram"
}
```

Resposta:
```json
{
  "ok": true,
  "notion_url": "https://notion.so/...",
  "original": "preview do que chegou...",
  "llm": {
    "title": "...",
    "type": "codigo",
    "summary_short": "...",
    "tags": ["..."],
    "language": "javascript",
    "importance": 8,
    "has_code": true
  }
}
```

### `POST /query`
Filtra o database do Notion por tipo, linguagem ou tag.

```json
{
  "type": "codigo",
  "language": "python"
}
```

### `GET /health`
Status da API.

## Setup

```bash
cp .env.example .env
# preenche as variáveis
docker compose up -d
```

## Schema Notion Database

| Propriedade | Tipo |
|---|---|
| Título | Title |
| Tipo | Select |
| Resumo | Rich Text |
| Tags | Multi-select |
| Linguagem | Select |
| Importância | Number |
| Tem Código | Checkbox |
