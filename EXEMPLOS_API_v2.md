# Exemplos de API - LiteLLM + MCP Adapter (v2)

Documentação completa com exemplos práticos de uso da plataforma LiteLLM com MCP Adapter, incluindo os **novos endpoints de agents v2**.

**Data**: 2026-01-02
**Versão**: 2.0
**Branch**: `feat/view-customization-agents`

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Novidades v2](#2-novidades-v2)
3. [Usuários e Permissões](#3-usuários-e-permissões)
4. [Endpoints de Agents (Novos)](#4-endpoints-de-agents-novos)
5. [Endpoints de Modelos (Modificados)](#5-endpoints-de-modelos-modificados)
6. [Chat com Agents (MCP)](#6-chat-com-agents-mcp)
7. [Chat com Modelos Tradicionais](#7-chat-com-modelos-tradicionais)
8. [Validação dos Exemplos](#8-validação-dos-exemplos)
9. [Referência Rápida](#9-referência-rápida)

---

## 1. Visão Geral

### Arquitetura

```
┌─────────────────────────────┐
│      Auth Middleware        │
│  ┌───────────────────────┐  │
│  │ GET /api/agents       │◄─── Nova API (v2)
│  │ GET /api/agents/{id}  │◄─── Nova API (v2)
│  │ GET /v1/models        │◄─── Modificado (v2)
│  │ POST /v1/chat/...     │    │
│  └───────────────────────┘    │
└─────────────────────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌──────────┐    ┌──────────┐
│   MCP    │    │ LiteLLM  │
│ Adapter  │    │          │
└──────────┘    └──────────┘
    │
    ▼
┌──────────┐
│   MCP    │
│  Server  │
└──────────┘
```

### Componentes

| Componente | Porta | Descrição |
|------------|-------|-----------|
| **Auth Middleware** | 8000 | Proxy com permissões + Novos endpoints de agents |
| **MCP Adapter** | 8001 | Orquestração de agents e MCPs |
| **LiteLLM** | 4000 | Proxy para OpenAI/Anthropic |
| **MCP Server** | N/A | Ferramentas (analytics, monitoring, database) |
| **PostgreSQL** | 5432 | Banco de dados (agents, prompts, permissões) |

---

## 2. Novidades v2

### Mudanças da API

| Aspecto | v1 (Antiga) | v2 (Nova) |
|---------|-------------|-----------|
| **Agents em /v1/models** | ✅ Sim | ❌ Não |
| **Endpoint para listar agents** | /v1/models | /api/agents |
| **Endpoint para detalhes** | N/A | /api/agents/{id} |
| **Prompts de exemplo** | ❌ Não retornados | ✅ Retornados |

### Novos Endpoints

```bash
# v2: Listar agents (com contagem de prompts)
GET /api/agents
→ Retorna: agents com informações resumidas

# v2: Detalhes do agent (com prompts completos)
GET /api/agents/{agent_id}
→ Retorna: agent com array de prompts

# v2: Modelos tradicionais (SEM agents)
GET /v1/models
→ Retorna: apenas gpt-4, claude-sonnet, gpt-3.5-turbo
```

---

## 3. Usuários e Permissões

### Usuário VENDAS (emingues@gmail.com)

**Grupo**: `vendas`
**Virtual Key**: `vendas-team`

**Permissões**:
- ✅ Vê 2 agents: "Assistente Genérico" + "Agent Diagnóstico de Vendas"
- ✅ Vê modelos premium: `gpt-4` e `claude-sonnet`
- ✅ Acesso a 8 prompts de exemplo (4 por agent)

### Usuário GERAL (geral@company.com)

**Grupo**: `geral`
**Virtual Key**: `geral-team`

**Permissões**:
- ✅ Vê 1 agent: "Assistente Genérico" (apenas)
- ✅ Vê modelo básico: `gpt-3.5-turbo`
- ✅ Acesso a 4 prompts de exemplo
- ❌ NÃO vê: "Agent Diagnóstico de Vendas"
- ❌ NÃO vê: `gpt-4` ou `claude-sonnet`

---

## 4. Endpoints de Agents (Novos)

### 4.1. Listar Agents

**Endpoint**: `GET /api/agents`
**Propósito**: Retorna agents disponíveis para o usuário com contagem de prompts

#### Exemplo: Usuário VENDAS

```bash
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     -H "X-OpenWebUI-User-Id: user-1" \
     -H "X-OpenWebUI-User-Role: admin" \
     http://localhost:8000/api/agents | jq
```

**Resultado**:
```json
{
  "success": true,
  "agents": [
    {
      "id": "agent-generico",
      "name": "Assistente Genérico",
      "description": "Assistente de propósito geral para responder perguntas, ajudar com tarefas e fornecer informações. Não tem acesso a dados internos da empresa.",
      "llm_model": "gpt-4",
      "llm_provider": "openai",
      "prompt_count": 4
    },
    {
      "id": "diagnostico-vendas",
      "name": "Agent Diagnóstico de Vendas",
      "description": "Analisa performance de vendas consultando dados de analytics, monitoring e banco de dados interno. Fornece insights acionáveis sobre conversão, funil de vendas, performance técnica e recomendações estratégicas.",
      "llm_model": "claude-sonnet",
      "llm_provider": "anthropic",
      "prompt_count": 4
    }
  ]
}
```

#### Exemplo: Usuário GERAL

```bash
curl -H "X-OpenWebUI-User-Email: geral@company.com" \
     http://localhost:8000/api/agents | jq
```

**Resultado**:
```json
{
  "success": true,
  "agents": [
    {
      "id": "agent-generico",
      "name": "Assistente Genérico",
      "description": "Assistente de propósito geral para responder perguntas, ajudar com tarefas e fornecer informações. Não tem acesso a dados internos da empresa.",
      "llm_model": "gpt-4",
      "llm_provider": "openai",
      "prompt_count": 4
    }
  ]
}
```

**Observação**: Usuário GERAL vê apenas 1 agent.

---

### 4.2. Detalhes do Agent (com Prompts)

**Endpoint**: `GET /api/agents/{agent_id}`
**Propósito**: Retorna detalhes do agent incluindo todos os prompts de exemplo

#### Exemplo: Agent Diagnóstico de Vendas

```bash
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/api/agents/diagnostico-vendas | jq
```

**Resultado**:
```json
{
  "success": true,
  "agent": {
    "id": "diagnostico-vendas",
    "name": "Agent Diagnóstico de Vendas",
    "description": "Analisa performance de vendas consultando dados de analytics, monitoring e banco de dados interno. Fornece insights acionáveis sobre conversão, funil de vendas, performance técnica e recomendações estratégicas.",
    "llm_model": "claude-sonnet",
    "llm_provider": "anthropic",
    "prompts": [
      {
        "title": "Análise de conversão",
        "content": "Qual foi a taxa de conversão nos últimos 30 dias? Compare com o período anterior e identifique as principais fontes de tráfego."
      },
      {
        "title": "Comparação mensal",
        "content": "Compare a performance de vendas deste mês com o mês anterior. Analise por categoria de produto e fonte de tráfego."
      },
      {
        "title": "Análise de funil",
        "content": "Identifique os principais gargalos no funil de vendas. Correlacione com problemas técnicos se houver."
      },
      {
        "title": "Performance técnica",
        "content": "Mostre as APIs com maior latência e analise se estão afetando a conversão de vendas."
      }
    ]
  }
}
```

#### Exemplo: Acesso Negado

```bash
curl -H "X-OpenWebUI-User-Email: geral@company.com" \
     http://localhost:8000/api/agents/diagnostico-vendas | jq
```

**Resultado**:
```json
{
  "success": false,
  "agent": null,
  "error": "Agent not found"
}
```

**Status HTTP**: 200 OK (mas agent não existe na lista do usuário)

---

### 4.3. Extrair Apenas Títulos de Prompts

```bash
curl -s -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/api/agents/diagnostico-vendas | \
  jq '.agent.prompts[] | .title'
```

**Resultado**:
```
"Análise de conversão"
"Comparação mensal"
"Análise de funil"
"Performance técnica"
```

---

## 5. Endpoints de Modelos (Modificados)

### 5.1. Listar Modelos (SEM Agents)

**Endpoint**: `GET /v1/models`
**Modificação v2**: Retorna APENAS modelos tradicionais (gpt-4, claude-sonnet, gpt-3.5-turbo)
**Agents**: NÃO aparecem mais neste endpoint

#### Exemplo: Usuário VENDAS

```bash
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/v1/models | jq '.data[] | .id'
```

**Resultado**:
```
"gpt-4"
"claude-sonnet"
```

**Observação**: Agents NÃO aparecem mais nesta lista.

#### Exemplo: Usuário GERAL

```bash
curl -H "X-OpenWebUI-User-Email: geral@company.com" \
     http://localhost:8000/v1/models | jq '.data[] | .id'
```

**Resultado**:
```
"gpt-3.5-turbo"
```

---

### 5.2. Comparação v1 vs v2

| Endpoint | v1 (Antes) | v2 (Agora) |
|----------|------------|-----------|
| **GET /v1/models** | Retorna agents + modelos | Retorna APENAS modelos |
| **Agents em /v1/models** | ✅ Sim | ❌ Não |
| **Como listar agents** | GET /v1/models | GET /api/agents |
| **Como ver prompts** | ❌ Não disponível | GET /api/agents/{id} |

---

## 6. Chat com Agents (MCP)

### 6.1. Usando Prompt de Exemplo

**Endpoint**: `POST /v1/chat/completions`
**Modelo**: `diagnostico-vendas`
**Roteamento**: Auth Middleware → MCP Adapter

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
  -H "X-OpenWebUI-User-Id: user-vendas" \
  -d '{
    "model": "diagnostico-vendas",
    "messages": [
      {
        "role": "user",
        "content": "Qual foi a taxa de conversão nos últimos 30 dias? Compare com o período anterior e identifique as principais fontes de tráfego."
      }
    ],
    "stream": false
  }' | jq
```

### 6.2. Fluxo Interno (MCP)

```
1️⃣ Auth Middleware
   ├─ Detecta model_id: "diagnostico-vendas"
   └─ Roteia para: http://mcp-adapter:8001/agents/diagnostico-vendas/chat

2️⃣ MCP Adapter
   ├─ Valida permissão ✅
   ├─ Identifica keywords: "conversão", "tráfego"
   ├─ Chama MCP: analytics_get_conversion
   └─ Recebe 847 chars de dados reais

3️⃣ Contexto Enriquecido
   ├─ Mensagem original + Dados do MCP
   └─ Envia para LiteLLM (claude-sonnet)

4️⃣ Resposta
   └─ Análise inteligente com dados reais
```

### 6.3. Resultado Esperado

```json
{
  "id": "chatcmpl-xyz789",
  "object": "chat.completion",
  "model": "claude-sonnet",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "📊 **Análise da Taxa de Conversão - Últimos 30 dias**\n\n**Taxa de Conversão Geral:** 3.42% (+14.77%)\n\n**Performance por Fonte:**\n1. Campanhas Pagas: 5.8% 🥇\n2. Email Marketing: 4.2% 🥈\n3. Orgânico: 2.5% 🥉\n4. Redes Sociais: 1.9%\n\n**Recomendações:**\n- Investir mais em campanhas pagas (melhor ROI)\n- Otimizar funil orgânico\n- Testar novos formatos em redes sociais"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 450,
    "completion_tokens": 380,
    "total_tokens": 830
  }
}
```

---

## 7. Chat com Modelos Tradicionais

### 7.1. GPT-4 (Direto, sem MCP)

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "O que é taxa de conversão em e-commerce?"
      }
    ],
    "stream": false
  }' | jq
```

**Fluxo**:
```
Auth Middleware → LiteLLM → OpenAI GPT-4
(Sem MCPs, resposta direta)
```

**Resultado**: Explicação genérica sobre taxa de conversão (sem dados específicos).

---

### 7.2. Comparação: Agent vs Modelo Direto

| Aspecto | GPT-4 Direto | Agent Diagnóstico (MCP) |
|---------|--------------|-------------------------|
| **Endpoint** | POST /v1/chat/completions | POST /v1/chat/completions |
| **Model ID** | "gpt-4" | "diagnostico-vendas" |
| **Dados** | Conhecimento geral | Dados reais do analytics |
| **Precisão** | Genérica | Específica da empresa |
| **Contexto** | Limitado | Enriquecido com MCPs |
| **Latência** | ~2s | ~3-4s (inclui MCPs) |
| **Custo** | Menor | Maior (MCP + LLM) |
| **Valor** | Explicações | Insights acionáveis |

---

## 8. Validação dos Exemplos

### ✅ Testes Executados (v2)

```bash
# Teste 1: Listar agents (VENDAS)
curl -s -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/api/agents | jq '.agents | length'
# Resultado: 2
# Status: ✅ PASSOU

# Teste 2: Detalhes do agent com prompts
curl -s -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/api/agents/diagnostico-vendas | \
  jq '.agent.prompts | length'
# Resultado: 4
# Status: ✅ PASSOU

# Teste 3: Verificar que /v1/models NÃO tem agents
curl -s -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/v1/models | \
  jq '.data[] | select(.id | contains("agent") or contains("diagnostico"))'
# Resultado: (vazio)
# Status: ✅ PASSOU

# Teste 4: Apenas modelos tradicionais em /v1/models
curl -s -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/v1/models | jq '.data[] | .id'
# Resultado: "gpt-4", "claude-sonnet"
# Status: ✅ PASSOU

# Teste 5: Usuário GERAL vê apenas 1 agent
curl -s -H "X-OpenWebUI-User-Email: geral@company.com" \
     http://localhost:8000/api/agents | jq '.agents | length'
# Resultado: 1
# Status: ✅ PASSOU

# Teste 6: Acesso negado para GERAL
curl -s -H "X-OpenWebUI-User-Email: geral@company.com" \
     http://localhost:8000/api/agents | \
  jq '.agents[] | select(.id == "diagnostico-vendas")'
# Resultado: (vazio)
# Status: ✅ PASSOU
```

### 📊 Resumo da Validação

| Teste | Descrição | Status | Resultado |
|-------|-----------|--------|-----------|
| 1 | GET /api/agents (VENDAS) | ✅ PASSOU | 2 agents |
| 2 | GET /api/agents/{id} com prompts | ✅ PASSOU | 4 prompts |
| 3 | GET /v1/models sem agents | ✅ PASSOU | Agents não listados |
| 4 | GET /v1/models apenas modelos | ✅ PASSOU | gpt-4, claude-sonnet |
| 5 | GET /api/agents (GERAL) | ✅ PASSOU | 1 agent |
| 6 | Acesso negado diagnostico-vendas | ✅ PASSOU | Agent não visível |

---

## 9. Referência Rápida

### Endpoints de Agents (v2)

```bash
# Listar agents do usuário
GET /api/agents
Headers: X-OpenWebUI-User-Email
Response: { "success": true, "agents": [...] }

# Detalhes do agent com prompts
GET /api/agents/{agent_id}
Headers: X-OpenWebUI-User-Email
Response: { "success": true, "agent": {..., "prompts": [...]} }
```

### Endpoints de Modelos (v2)

```bash
# Listar modelos tradicionais (SEM agents)
GET /v1/models
Headers: X-OpenWebUI-User-Email
Response: { "data": [{"id": "gpt-4", ...}, {"id": "claude-sonnet", ...}] }
```

### Chat

```bash
# Chat com agent (roteado para MCP Adapter)
POST /v1/chat/completions
Body: { "model": "diagnostico-vendas", "messages": [...] }

# Chat com modelo tradicional (roteado para LiteLLM)
POST /v1/chat/completions
Body: { "model": "gpt-4", "messages": [...] }
```

### Acesso Direto ao MCP Adapter

```bash
# Listar agents com prompts completos
GET http://localhost:8001/agents?user_email=emingues@gmail.com

# Chat com agent (sem passar pelo auth-middleware)
POST http://localhost:8001/agents/{agent_key}/chat
Body: { "user_email": "...", "message": "...", "history": [] }
```

---

## 10. Migração v1 → v2

### Mudanças Necessárias

#### Para consumidores da API

**ANTES (v1)**:
```bash
# Buscar agents de /v1/models (misturado com modelos)
curl /v1/models | jq '.data[] | select(.id | contains("agent"))'
```

**DEPOIS (v2)**:
```bash
# Buscar agents de /api/agents (endpoint dedicado)
curl /api/agents | jq '.agents[]'
```

#### Vantagens da v2

- ✅ **Separação clara**: Agents vs Modelos
- ✅ **Prompts incluídos**: Retorna array de prompts de exemplo
- ✅ **Informações adicionais**: `prompt_count`, `description` detalhada
- ✅ **Permissões respeitadas**: Filtragem automática por usuário

---

## 11. Conclusão

### ✅ v2 Implementa

1. **Novos Endpoints**
   - `GET /api/agents` - Lista agents com informações resumidas
   - `GET /api/agents/{id}` - Detalhes com prompts completos

2. **Modificação de Endpoints**
   - `GET /v1/models` - Agora retorna APENAS modelos tradicionais

3. **Benefícios**
   - Separação clara entre agents e modelos
   - Prompts de exemplo acessíveis via API
   - Permissões validadas automaticamente
   - Escalável (novos agents aparecem automaticamente)

### 🔗 Links Úteis

- Auth Middleware: http://localhost:8000
- MCP Adapter: http://localhost:8001
- LiteLLM: http://localhost:4000

### 📚 Documentação Adicional

- **Implementação**: [open-webui-custom/IMPLEMENTATION_GUIDE.md](open-webui-custom/IMPLEMENTATION_GUIDE.md)
- **Arquitetura**: [open-webui-custom/README.md](open-webui-custom/README.md)

---

**Data da validação**: 2026-01-02
**Branch**: `feat/view-customization-agents`
**Status**: ✅ Todos os testes passando
