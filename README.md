# api-notion

API que recebe qualquer conteúdo, processa via LLM (sem API key oficial — usa `fluxo-codex` com auth do ChatGPT) e salva estruturado no Notion.

Cada item salvo é separado em dois blocos claros:
- **📥 Conteúdo Original Recebido** — exatamente o que chegou na API, sem alterar nada
- **🤖 Dados Processados pela LLM** — título, tipo, resumo, tags, pontos-chave, termos de busca

---

## Arquitetura

```
você / skills-chat / qualquer cliente
        ↓
  POST api-notion/save
        ↓
  src/llm_processor.py
        ↓ httpx POST
  fluxo-codex:3000/v1/chat/completions
        ↓ Bearer auth.json (token do ChatGPT)
  chatgpt.com/backend-api/codex/responses
        ↓ gpt-5.4 ou gpt-5.4-mini
  JSON estruturado volta
        ↓
  src/notion_client.py
        ↓
  Notion Database
```

### Por que fluxo-codex e não OpenAI direta?

O [fluxo-codex](https://github.com/sonyddr666/fluxo-codex/tree/chat-skills-code) é um proxy Flask que chama o endpoint interno do ChatGPT:

```
POST https://chatgpt.com/backend-api/codex/responses
Authorization: Bearer <token do auth.json>
```

Isso significa:
- **sem OPENAI_API_KEY**
- **sem custo de API**
- usa o token extraído da sessão do ChatGPT via `auth.json`
- expõe `/v1/chat/completions` compatível com formato OpenAI

---

## Modelos disponíveis via fluxo-codex

| Modelo | Quando usar |
|---|---|
| `gpt-5.4` | conteúdo longo (>1500 chars) ou com blocos de código |
| `gpt-5.4-mini` | texto curto, mensagens simples, classificações rápidas |

A seleção é automática — o `api-notion` decide qual modelo usar baseado no tamanho e tipo do conteúdo.

---

## Endpoints

### `GET /health`

Status da API.

```json
{ "status": "ok", "service": "api-notion" }
```

---

### `POST /save`

Recebe qualquer conteúdo, processa via LLM e salva no Notion.

**Aceita:** string, JSON, código, mensagem, qualquer formato no campo `content`.

**Payload de entrada:**
```json
{
  "content": "qualquer coisa aqui — texto, código, ideia, conversa",
  "origin": "skills-chat"
}
```

- `content` — obrigatório, qualquer tipo
- `origin` — opcional, string livre para identificar de onde veio (`skills-chat`, `telegram`, `bot`, `cli`, `web`)

**Resposta:**
```json
{
  "ok": true,
  "notion_url": "https://notion.so/...",
  "original": "preview dos primeiros 500 chars do que chegou",
  "llm": {
    "title": "Função retry com backoff em Node.js",
    "type": "codigo",
    "summary_short": "Snippet Node.js para retry exponencial com tratamento de erro 429.",
    "summary_detailed": "Implementação de função assíncrona que reexecuta chamadas HTTP com atraso exponencial quando encontra erro temporário. Suporta configuração de máximo de tentativas e delay base.",
    "tags": ["node", "retry", "backoff", "http", "async"],
    "language": "javascript",
    "importance": 8,
    "has_code": true,
    "key_points": [
      "usa exponential backoff",
      "trata erro 429 especificamente",
      "configurável por parâmetro"
    ],
    "search_terms": ["retry", "backoff", "node", "http", "429"],
    "origin": "skills-chat"
  }
}
```

---

### `POST /query`

Consulta o database do Notion com filtros.

**Payload de entrada:**
```json
{
  "type": "codigo",
  "language": "python",
  "tag": "retry"
}
```

Todos os campos são opcionais. Se mandar vazio `{}`, retorna os 20 mais recentes.

**Filtros disponíveis:**

| Campo | Tipo | Valores possíveis |
|---|---|---|
| `type` | string | `codigo` `snippet` `ideia` `bug` `explicacao` `referencia` |
| `language` | string | `javascript` `typescript` `python` `go` `bash` `none` |
| `tag` | string | qualquer tag salva |

**Resposta:**
```json
{
  "count": 2,
  "results": [
    {
      "title": "Função retry com backoff em Node.js",
      "type": "codigo",
      "url": "https://notion.so/..."
    },
    {
      "title": "Implementação de queue com Bull",
      "type": "codigo",
      "url": "https://notion.so/..."
    }
  ]
}
```

---

## O que a LLM gera para cada item salvo

Quando você manda um conteúdo para `/save`, o LLM processa e gera automaticamente:

| Campo | Descrição |
|---|---|
| `title` | título descritivo gerado pelo modelo |
| `type` | classificação: `codigo` `snippet` `ideia` `bug` `explicacao` `referencia` |
| `summary_short` | resumo curto (máx 100 chars) |
| `summary_detailed` | resumo completo (máx 500 chars) |
| `tags` | até 5 tags relevantes |
| `language` | linguagem detectada do código |
| `importance` | nota de 1 a 10 de relevância |
| `has_code` | true se contém código |
| `key_points` | até 3 pontos principais |
| `search_terms` | até 5 termos para busca futura |

---

## Schema do Notion Database

Crie um database no Notion com estas propriedades antes de usar:

| Propriedade | Tipo Notion |
|---|---|
| Título | Title |
| Tipo | Select |
| Resumo | Rich Text |
| Tags | Multi-select |
| Linguagem | Select |
| Importância | Number |
| Tem Código | Checkbox |

Cada página criada tem dois blocos no corpo:
1. **🤖 Dados Processados pela LLM** — resumo detalhado, pontos-chave, termos de busca
2. **📥 Conteúdo Original Recebido** — o que chegou na API exatamente

---

## Como criar uma skill no skills-chat

O [skills-chat](https://github.com/sonyddr666/skills-chat) suporta skills com `action.type: http`.
Você registra via `POST /api/skills` ou pelo painel.

### Skill: salvar no Notion

```json
{
  "id": "notion_save",
  "name": "notion_save",
  "icon": "📥",
  "description": "Salva conteúdo no Notion como memória longa. Use quando o usuário pedir para salvar, guardar, registrar algo importante — código gerado, explicação útil, ideia de projeto, solução encontrada.",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "content": {
        "type": "STRING",
        "description": "O conteúdo a ser salvo. Pode ser código, explicação, ideia ou qualquer texto útil da conversa."
      },
      "origin": {
        "type": "STRING",
        "description": "Origem: skills-chat, telegram, bot, cli. Padrão: skills-chat"
      }
    },
    "required": ["content"]
  },
  "action": {
    "type": "http",
    "method": "POST",
    "url": "http://api-notion:8000/save",
    "headers": { "Content-Type": "application/json" },
    "body": {
      "content": "{{content}}",
      "origin": "{{origin}}"
    }
  }
}
```

> Para produção troque `http://api-notion:8000` por `https://notion.0api.cloud`

### Skill: consultar memória no Notion

```json
{
  "id": "notion_query",
  "name": "notion_query",
  "icon": "🔍",
  "description": "Busca registros salvos no Notion. Use quando o usuário perguntar sobre algo que pode ter sido salvo antes, quiser ver snippets de uma linguagem, ou buscar por tema.",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "type": {
        "type": "STRING",
        "description": "Tipo a filtrar: codigo, snippet, ideia, bug, explicacao, referencia"
      },
      "language": {
        "type": "STRING",
        "description": "Linguagem: javascript, typescript, python, go, bash, none"
      },
      "tag": {
        "type": "STRING",
        "description": "Tag específica para filtrar"
      }
    }
  },
  "action": {
    "type": "http",
    "method": "POST",
    "url": "http://api-notion:8000/query",
    "headers": { "Content-Type": "application/json" },
    "body": {
      "type": "{{type}}",
      "language": "{{language}}",
      "tag": "{{tag}}"
    }
  }
}
```

---

## Papel do Notion nesse sistema

O Notion funciona aqui como **memória longa** — não memória operacional da sessão.

| Tipo de memória | Onde fica |
|---|---|
| Contexto imediato da conversa | `gc_user_memory` local do skills-chat |
| Conhecimento persistente | Notion via api-notion |

O fluxo de uso natural é:
- você conversa normalmente no skills-chat
- quando aparece algo valioso (código bom, solução, ideia), pede pra salvar
- a skill `notion_save` é acionada
- o `api-notion` processa e estrutura via LLM
- fica no Notion organizado e consultável depois
- quando quiser recuperar, a skill `notion_query` filtra e traz de volta

### O que vale salvar

- código gerado que vai reaproveitar
- explicação técnica clara
- solução pra um bug
- ideia de projeto
- decisão importante
- snippet útil

### O que não vale salvar

- cada micro mensagem isolada
- perguntas simples sem resposta relevante
- conteúdo temporário que não vai usar depois

---

## Filtros futuros planejados (não implementados ainda)

Os campos já existem no Notion, só precisam ser expostos no `/query`:

- `after` / `before` — filtrar por data de criação
- `min_importance` — trazer só itens com importância acima de X
- `origin` — filtrar por origem (`skills-chat`, `telegram`, etc)
- `search` — busca por texto no resumo

---

## Setup

### Variáveis de ambiente

```env
NOTION_TOKEN=secret_xxxxx
NOTION_DATABASE_ID=xxxxx

# fluxo-codex como LLM — sem chave OpenAI
FLUXO_CODEX_URL=http://fluxo-codex:3000/v1/chat/completions
LLM_MODEL_FULL=gpt-5.4
LLM_MODEL_MINI=gpt-5.4-mini

PORT=8000
```

### Rodar só o api-notion

```bash
git clone https://github.com/sonyddr666/api-notion
cd api-notion
cp .env.example .env
# preenche NOTION_TOKEN e NOTION_DATABASE_ID
docker compose up -d
```

### Rodar com fluxo-codex + skills-chat juntos

```yaml
# docker-compose.yml na raiz do seu ambiente
version: "3.8"

services:
  skills-chat:
    build: ./skills-chat
    ports:
      - "9321:9321"
    env_file: ./skills-chat/.env
    networks:
      - stack

  api-notion:
    build: ./api-notion
    ports:
      - "8000:8000"
    env_file: ./api-notion/.env
    depends_on:
      - fluxo-codex
    networks:
      - stack

  fluxo-codex:
    build: ./fluxo-codex
    ports:
      - "3000:3000"
    volumes:
      - ./fluxo-codex/auth.json:/app/auth.json:ro
    networks:
      - stack

networks:
  stack:
    driver: bridge
```

```bash
docker compose up -d

# testar save
curl -X POST http://localhost:8000/save \
  -H "Content-Type: application/json" \
  -d '{"content": "função retry com backoff em Node.js", "origin": "teste"}'

# testar query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"type": "codigo", "language": "javascript"}'
```

---

## Repositórios relacionados

- [skills-chat](https://github.com/sonyddr666/skills-chat) — interface de chat com sistema de skills
- [fluxo-codex](https://github.com/sonyddr666/fluxo-codex/tree/chat-skills-code) — proxy Flask que usa ChatGPT sem API key oficial
- [0api-codex](https://github.com/sonyddr666/0api-codex/tree/codex) — servidor base
- [perplexo-api](https://github.com/sonyddr666/perplexo-api) — API Perplexity MCP
