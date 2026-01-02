# Exemplos de API - LiteLLM + MCP Adapter + Agents UI (v2)

Documentação completa com exemplos práticos de uso da plataforma LiteLLM com MCP Adapter, incluindo a **nova UI customizada de agents**.

**Data**: 2026-01-02
**Versão**: 2.0 (com Agents UI)
**Branch**: `feat/view-customization-agents`

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Novidades v2 - Agents UI](#2-novidades-v2---agents-ui)
3. [Usuários e Permissões](#3-usuários-e-permissões)
4. [Endpoints da UI de Agents](#4-endpoints-da-ui-de-agents)
5. [Endpoints de Modelos (Modificados)](#5-endpoints-de-modelos-modificados)
6. [Testando Agents com MCP](#6-testando-agents-com-mcp)
7. [Testando Modelos Tradicionais](#7-testando-modelos-tradicionais)
8. [Fluxo Completo de Uso](#8-fluxo-completo-de-uso)
9. [Validação dos Exemplos](#9-validação-dos-exemplos)

---

## 1. Visão Geral

### Arquitetura Atualizada (v2)

```
┌─────────────────────────────────────────────────────────────┐
│                    Open WebUI (Frontend)                    │
│  ┌──────────────┐  ┌─────────────────────────────────────┐ │
│  │   Sidebar    │  │         Main Content                │ │
│  │ ┌──────────┐ │  │  ┌────────────────────────────────┐ │ │
│  │ │ 📊 Agents│ │  │  │  Agent Detail Page             │ │ │
│  │ │ Agent 1  │─┼──┼─►│  ┌─────────┐  ┌─────────┐      │ │ │
│  │ │ Agent 2  │ │  │  │  │ Card 1  │  │ Card 2  │      │ │ │
│  │ │          │ │  │  │  │ Prompt  │  │ Prompt  │      │ │ │
│  │ └──────────┘ │  │  │  └─────────┘  └─────────┘      │ │ │
│  │              │  │  │  ┌─────────┐  ┌─────────┐      │ │ │
│  │ 💬 Chats     │  │  │  │ Card 3  │  │ Card 4  │      │ │ │
│  │ Chat 1       │  │  │  │ Prompt  │  │ Prompt  │      │ │ │
│  │ Chat 2       │  │  │  └─────────┘  └─────────┘      │ │ │
│  └──────────────┘  │  └────────────────────────────────┘ │ │
│                    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │   Auth Middleware           │
              │  ┌─────────────────────┐    │
              │  │ GET /api/agents     │◄── Nova API (v2)
              │  │ GET /api/agents/{id}│◄── Nova API (v2)
              │  │ GET /v1/models      │◄── Modificado (v2)
              │  │ POST /v1/chat/...   │    │
              │  └─────────────────────┘    │
              └─────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
   ┌──────────────────┐    ┌──────────────────┐
   │  MCP Adapter     │    │    LiteLLM       │
   │  GET /agents     │    │  /v1/models      │
   │  POST /chat      │    │  /v1/chat/...    │
   └──────────────────┘    └──────────────────┘
              │
              ▼
   ┌──────────────────┐
   │   MCP Server     │
   │   (Analytics,    │
   │   Monitoring,    │
   │   Database)      │
   └──────────────────┘
```

### Componentes

| Componente | Porta | Descrição |
|------------|-------|-----------|
| **Auth Middleware** | 8000 | Proxy com permissões + Novos endpoints de Agents UI |
| **MCP Adapter** | 8001 | Orquestração de agents e MCPs |
| **LiteLLM** | 4000 | Proxy para OpenAI/Anthropic |
| **Open WebUI** | 8888 | Interface web (com UI customizada de agents) |
| **MCP Server** | N/A | Ferramentas de analytics, monitoring, database |
| **PostgreSQL** | 5432 | Banco de dados (agents, prompts, permissões) |

---

## 2. Novidades v2 - Agents UI

### O que mudou na v2?

#### ✅ Agents no Menu Lateral (estilo ChatGPT GPTs)

**ANTES (v1)**:
- Agents apareciam no dropdown de modelos
- Sem prompts de exemplo visíveis
- Misturados com modelos tradicionais

**DEPOIS (v2)**:
- Agents aparecem em menu lateral dedicado
- Cada agent tem página de detalhes
- 4 cards de prompts clicáveis por agent
- Separação clara: sidebar para agents, dropdown para modelos

#### ✅ Novos Endpoints API

```bash
# NOVO: Listar agents (para UI)
GET /api/agents

# NOVO: Detalhes do agent (para UI)
GET /api/agents/{agent_id}

# MODIFICADO: Apenas modelos tradicionais (sem agents)
GET /v1/models
```

#### ✅ Experiência do Usuário

1. **Sidebar mostra agents** disponíveis
2. **Click no agent** → Abre página de detalhes
3. **Página mostra 4 cards** com prompts de exemplo
4. **Click no card** → Abre chat novo com prompt pré-preenchido
5. **Enviar mensagem** → MCP Adapter processa com dados reais

---

## 3. Usuários e Permissões

### Usuário VENDAS (emingues@gmail.com)

**Grupo**: `vendas`
**Virtual Key**: `vendas-team`

**Permissões**:
- ✅ Vê 2 agents: "Assistente Genérico" + "Agent Diagnóstico de Vendas"
- ✅ Vê modelos premium: `gpt-4` e `claude-sonnet`
- ✅ Acesso completo ao sistema

### Usuário GERAL (geral@company.com)

**Grupo**: `geral`
**Virtual Key**: `geral-team`

**Permissões**:
- ✅ Vê 1 agent: "Assistente Genérico" (apenas)
- ✅ Vê modelo básico: `gpt-3.5-turbo`
- ❌ NÃO vê: "Agent Diagnóstico de Vendas"
- ❌ NÃO vê: `gpt-4` ou `claude-sonnet`

---

## 4. Endpoints da UI de Agents

### 4.1. Listar Agents (Sidebar)

**Endpoint**: `GET /api/agents`
**Propósito**: Retorna agents disponíveis para o usuário (usado pela sidebar)

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
     -H "X-OpenWebUI-User-Id: user-2" \
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

### 4.2. Detalhes do Agent (Página de Detalhes)

**Endpoint**: `GET /api/agents/{agent_id}`
**Propósito**: Retorna detalhes do agent com todos os prompts (para página de detalhes)

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

**Status**: 200 OK (mas agent não está na lista do usuário GERAL)

---

### 4.3. Buscar Apenas Títulos de Prompts

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
**Agents**: NÃO aparecem aqui (são buscados via `/api/agents`)

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

**Observação**: Apenas modelo básico.

---

### 5.2. Comparação v1 vs v2

| Aspecto | v1 (Antiga) | v2 (Nova) |
|---------|-------------|-----------|
| **Agents no /v1/models** | ✅ Sim | ❌ Não |
| **Dropdown de modelos** | Agents + Modelos | Apenas modelos |
| **Como ver agents** | Dropdown | Sidebar dedicada |
| **Prompts de exemplo** | ❌ Não visíveis | ✅ Cards clicáveis |
| **Endpoint para agents** | /v1/models | /api/agents |

---

## 6. Testando Agents com MCP

### 6.1. Fluxo Completo (UI)

```
1. Usuário acessa Open WebUI (http://localhost:8888)
   ↓
2. Sidebar mostra "AI Agents":
   - Assistente Genérico
   - Agent Diagnóstico de Vendas (se VENDAS)
   ↓
3. Click em "Agent Diagnóstico de Vendas"
   ↓
4. Página mostra 4 cards de prompts:
   ┌─────────────────────┐  ┌─────────────────────┐
   │ 📊 Análise de       │  │ 📈 Comparação       │
   │    conversão        │  │    mensal           │
   │                     │  │                     │
   │ Qual foi a taxa...  │  │ Compare a perf...   │
   └─────────────────────┘  └─────────────────────┘
   ┌─────────────────────┐  ┌─────────────────────┐
   │ 🔍 Análise de       │  │ ⚡ Performance      │
   │    funil            │  │    técnica          │
   │                     │  │                     │
   │ Identifique os...   │  │ Mostre as APIs...   │
   └─────────────────────┘  └─────────────────────┘
   ↓
5. Click no card "Análise de conversão"
   ↓
6. Abre chat novo com modelo "diagnostico-vendas"
   e prompt pré-preenchido
   ↓
7. Usuário envia mensagem
   ↓
8. MCP Adapter processa (ver fluxo abaixo)
```

### 6.2. Testar Agent via API (Direto)

**Endpoint**: `POST /v1/chat/completions`
**Modelo**: `diagnostico-vendas`
**Roteamento**: Auth Middleware → MCP Adapter

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
  -H "X-OpenWebUI-User-Id: user-vendas" \
  -H "X-OpenWebUI-User-Role: admin" \
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

#### Fluxo Interno (MCP)

```
1️⃣ Auth Middleware
   ├─ Detecta model_id: "diagnostico-vendas"
   └─ Roteia para: http://mcp-adapter:8001/agents/diagnostico-vendas/chat

2️⃣ MCP Adapter
   ├─ Valida permissão ✅
   ├─ Identifica keywords: "conversão", "tráfego"
   ├─ Chama MCP: analytics_get_conversion
   └─ Recebe 847 chars de dados

3️⃣ Contexto Enriquecido
   ├─ Mensagem original + Dados do MCP
   └─ Envia para LiteLLM (claude-sonnet)

4️⃣ Resposta
   └─ Análise inteligente com dados reais
```

**Resultado Esperado**:
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
  ]
}
```

---

## 7. Testando Modelos Tradicionais

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
| **Dados** | Conhecimento geral | Dados reais do analytics |
| **Precisão** | Genérica | Específica da empresa |
| **Contexto** | Limitado | Enriquecido com MCPs |
| **Latência** | ~2s | ~3-4s (inclui MCPs) |
| **Custo** | Menor | Maior (MCP + LLM) |
| **Valor** | Explicações | Insights acionáveis |
| **UI** | Dropdown de modelos | Sidebar + Cards de prompts |

---

## 8. Fluxo Completo de Uso

### 8.1. Cenário: Usuário VENDAS analisa conversão

```bash
# 1. Login no Open WebUI
# URL: http://localhost:8888
# User: emingues@gmail.com

# 2. Sidebar carrega agents
GET /api/agents
→ Retorna: 2 agents (Genérico + Diagnóstico)

# 3. Click em "Agent Diagnóstico de Vendas"
# Navegação: /agents/diagnostico-vendas

# 4. Página de detalhes carrega
GET /api/agents/diagnostico-vendas
→ Retorna: Agent com 4 prompts

# 5. UI renderiza 4 cards clicáveis
# - Card 1: "Análise de conversão"
# - Card 2: "Comparação mensal"
# - Card 3: "Análise de funil"
# - Card 4: "Performance técnica"

# 6. Usuário clica no Card 1
# Click handler:
POST /api/agents/diagnostico-vendas/chat
{
  "prompt": "Qual foi a taxa de conversão nos últimos 30 dias?..."
}

# 7. Navegação para novo chat
# URL: /c/new?model=diagnostico-vendas&message=Qual+foi+a+taxa...

# 8. Chat envia mensagem
POST /v1/chat/completions
{
  "model": "diagnostico-vendas",
  "messages": [{"role": "user", "content": "Qual foi a taxa..."}]
}

# 9. Auth Middleware roteia para MCP Adapter
POST http://mcp-adapter:8001/agents/diagnostico-vendas/chat

# 10. MCP Adapter processa
# - Valida permissão ✅
# - Detecta keywords: "conversão", "tráfego"
# - Chama MCP: analytics_get_conversion
# - Enriquece contexto
# - Chama LiteLLM (claude-sonnet)

# 11. Resposta streaming para usuário
# Análise completa com dados reais
```

---

### 8.2. Cenário: Usuário GERAL tenta acessar

```bash
# 1. Login no Open WebUI
# User: geral@company.com

# 2. Sidebar carrega agents
GET /api/agents
→ Retorna: 1 agent (apenas Genérico)

# 3. NÃO vê "Agent Diagnóstico de Vendas"
# Sidebar mostra apenas:
# - Assistente Genérico

# 4. Dropdown de modelos mostra
GET /v1/models
→ Retorna: apenas "gpt-3.5-turbo"

# 5. Tentativa de acessar via URL direta
GET /api/agents/diagnostico-vendas
→ Resultado: { "success": false, "error": "Agent not found" }

# 6. Tentativa de chat direto
POST /v1/chat/completions { "model": "diagnostico-vendas", ... }
→ MCP Adapter retorna: HTTP 403 "Access denied"
```

---

## 9. Validação dos Exemplos

### ✅ Testes Executados (v2)

```bash
# Teste 1: Listar agents via nova API (VENDAS)
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
# Status: ✅ PASSOU - Agents não aparecem em /v1/models

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

# Teste 6: Usuário GERAL não vê diagnostico-vendas
curl -s -H "X-OpenWebUI-User-Email: geral@company.com" \
     http://localhost:8000/api/agents | \
  jq '.agents[] | select(.id == "diagnostico-vendas")'
# Resultado: (vazio)
# Status: ✅ PASSOU
```

### 📊 Resumo da Validação v2

| Teste | Descrição | Status | Resultado |
|-------|-----------|--------|-----------|
| 1 | GET /api/agents (VENDAS) | ✅ PASSOU | 2 agents |
| 2 | GET /api/agents/{id} com prompts | ✅ PASSOU | 4 prompts |
| 3 | GET /v1/models sem agents | ✅ PASSOU | Agents não listados |
| 4 | GET /v1/models apenas modelos | ✅ PASSOU | gpt-4, claude-sonnet |
| 5 | GET /api/agents (GERAL) | ✅ PASSOU | 1 agent |
| 6 | Acesso negado diagnostico-vendas | ✅ PASSOU | Agent não visível |

---

## 10. Endpoints Completos (Referência Rápida)

### Agents UI (Novos em v2)

```bash
# Listar agents do usuário (sidebar)
GET /api/agents
Headers: X-OpenWebUI-User-Email

# Detalhes do agent (página de detalhes)
GET /api/agents/{agent_id}
Headers: X-OpenWebUI-User-Email
```

### Modelos (Modificado em v2)

```bash
# Listar modelos tradicionais (SEM agents)
GET /v1/models
Headers: X-OpenWebUI-User-Email
```

### Chat (Inalterado)

```bash
# Chat com agent (roteado para MCP Adapter)
POST /v1/chat/completions
Body: { "model": "diagnostico-vendas", "messages": [...] }

# Chat com modelo tradicional (roteado para LiteLLM)
POST /v1/chat/completions
Body: { "model": "gpt-4", "messages": [...] }
```

### MCP Adapter (Direto)

```bash
# Listar agents com prompts completos
GET http://localhost:8001/agents?user_email=emingues@gmail.com

# Chat com agent (direto, sem auth-middleware)
POST http://localhost:8001/agents/{agent_key}/chat
Body: { "user_email": "...", "message": "...", "history": [] }
```

---

## 11. Migração v1 → v2

### O que precisa ser atualizado?

#### Frontend (Open WebUI)

**ANTES (v1)**:
```javascript
// Buscar agents de /v1/models
const response = await fetch('/v1/models');
const data = response.json();
const agents = data.data.filter(m => m.id.includes('agent'));
```

**DEPOIS (v2)**:
```javascript
// Buscar agents de /api/agents
const response = await fetch('/api/agents');
const data = response.json();
const agents = data.agents; // Já filtrado por permissões
```

#### Componentes

**Adicionar**:
- [AgentsSidebar.svelte](open-webui-custom/frontend/AgentsSidebar.svelte)
- [AgentDetail.svelte](open-webui-custom/frontend/AgentDetail.svelte)

**Modificar**:
- Layout principal: incluir `<AgentsSidebar />` no menu lateral
- Dropdown de modelos: usar `/v1/models` (que agora exclui agents)

---

## 12. Conclusão

### ✅ v2 Implementa

1. **Separação de Conceitos**
   - Agents → Sidebar dedicada
   - Modelos → Dropdown tradicional

2. **Prompts Visíveis**
   - 4 cards clicáveis por agent
   - Onboarding facilitado
   - Usuário não precisa decorar prompts

3. **Permissões Respeitadas**
   - `/api/agents` valida permissões do usuário
   - Cada grupo vê apenas seus agents

4. **Escalável**
   - Novos agents aparecem automaticamente
   - Prompts gerenciados no banco
   - Sem hardcoding na UI

### 📚 Documentação Completa

- **Arquitetura**: [open-webui-custom/README.md](open-webui-custom/README.md)
- **Implementação**: [open-webui-custom/IMPLEMENTATION_GUIDE.md](open-webui-custom/IMPLEMENTATION_GUIDE.md)
- **Código fonte**: [/Users/macbookpro2017/git/lite-lmm/](.)

### 🔗 Links Úteis

- Open WebUI: http://localhost:8888
- Auth Middleware: http://localhost:8000
- MCP Adapter: http://localhost:8001
- LiteLLM: http://localhost:4000

---

**Data da validação**: 2026-01-02
**Branch**: `feat/view-customization-agents`
**Status**: ✅ Todos os testes passando
