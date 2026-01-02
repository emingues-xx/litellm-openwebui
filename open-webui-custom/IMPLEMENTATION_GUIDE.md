# Guia de Implementação - Agents UI Customizada

## Resumo Executivo

Esta branch (`feat/view-customization-agents`) implementa uma UI customizada no Open WebUI onde:

✅ **Agents aparecem no menu lateral** (como "GPTs" no ChatGPT)
✅ **Cada agent tem página de detalhes com cards de prompts clicáveis**
✅ **Agents NÃO aparecem no dropdown de modelos** (apenas gpt-4, claude-sonnet, etc.)
✅ **Permissões respeitadas** (VENDAS vê 2 agents, GERAL vê 1 agent)

## Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────┐
│                    Open WebUI (Frontend)                    │
│  ┌──────────────┐  ┌─────────────────────────────────────┐ │
│  │   Sidebar    │  │         Main Content                │ │
│  │ ┌──────────┐ │  │  ┌────────────────────────────────┐ │ │
│  │ │ 📊 Agents│ │  │  │  Agent Detail Page             │ │ │
│  │ │ Agent 1  │─┼──┼─►│  ┌─────────┐  ┌─────────┐      │ │ │
│  │ │ Agent 2  │ │  │  │  │ Card 1  │  │ Card 2  │      │ │ │
│  │ │ Agent 3  │ │  │  │  │ Prompt  │  │ Prompt  │      │ │ │
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
              │  │ GET /api/agents     │    │ ← Nova rota
              │  │ GET /api/agents/{id}│    │ ← Nova rota
              │  │ GET /v1/models      │    │ ← Modificada (sem agents)
              │  └─────────────────────┘    │
              └─────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │      MCP Adapter            │
              │  GET /agents                │
              │  GET /agents/{id}           │
              │  POST /agents/{id}/chat     │
              └─────────────────────────────┘
```

## Modificações Realizadas

### 1. Auth Middleware - Novos Endpoints

**Arquivo**: `auth-middleware/app.py`

**Mudanças**:

#### A. Novo endpoint `/api/agents` (linha 82-128)
```python
@app.get("/api/agents")
async def get_agents(request: Request):
    """
    API endpoint para UI customizada buscar agents
    Retorna apenas agents (não modelos tradicionais)
    """
    # Busca agents do MCP Adapter
    # Retorna formato simplificado para UI:
    # {
    #   "success": true,
    #   "agents": [
    #     {
    #       "id": "diagnostico-vendas",
    #       "name": "Agent Diagnóstico de Vendas",
    #       "description": "...",
    #       "llm_model": "claude-sonnet",
    #       "llm_provider": "anthropic",
    #       "prompt_count": 4
    #     }
    #   ]
    # }
```

#### B. Novo endpoint `/api/agents/{agent_id}` (linha 131-179)
```python
@app.get("/api/agents/{agent_id}")
async def get_agent_detail(agent_id: str, request: Request):
    """
    API endpoint para buscar detalhes de um agent específico
    Retorna agent com todos os prompts
    """
    # Busca agent específico
    # Retorna formato detalhado:
    # {
    #   "success": true,
    #   "agent": {
    #     "id": "diagnostico-vendas",
    #     "name": "Agent Diagnóstico de Vendas",
    #     "description": "...",
    #     "llm_model": "claude-sonnet",
    #     "llm_provider": "anthropic",
    #     "prompts": [
    #       {
    #         "title": "Análise de conversão",
    #         "content": "Qual foi a taxa de conversão..."
    #       },
    #       ...
    #     ]
    #   }
    # }
```

#### C. Modificação em `/v1/models` (linha 182-219)
```python
@app.get("/v1/models")
async def get_models(request: Request):
    """
    Retorna APENAS modelos tradicionais do LiteLLM (NÃO agents)

    Agents têm UI dedicada (sidebar + detail page) e são buscados via /api/agents
    """
    # ANTES: Retornava agents + modelos
    # DEPOIS: Retorna APENAS modelos (gpt-4, claude-sonnet, gpt-3.5-turbo)

    # Agents NÃO aparecem mais no dropdown de modelos
```

### 2. Componentes Frontend

**Arquivos criados**:

#### A. `open-webui-custom/frontend/AgentsSidebar.svelte`

**Propósito**: Componente Svelte para sidebar de agents

**Funcionalidades**:
- Busca agents de `/api/agents` ao montar
- Exibe lista de agents disponíveis para o usuário
- Cada agent mostra:
  - Ícone colorido
  - Nome
  - Modelo (badge)
  - Número de prompts
- Click no agent navega para `/agents/{agent_id}`

**Estilo**: Similar ao menu lateral do ChatGPT

#### B. `open-webui-custom/frontend/AgentDetail.svelte`

**Propósito**: Página de detalhes do agent

**Funcionalidades**:
- Busca detalhes de `/api/agents/{agent_id}`
- Exibe header com:
  - Ícone grande
  - Nome e descrição
  - Badges de modelo e provider
- Grid de cards de prompts (4 cards)
- Click no card:
  - Chama `/api/agents/{agent_id}/chat` com o prompt
  - Navega para nova conversa com prompt pré-preenchido

**Estilo**: Cards grandes e clicáveis, similar ao ChatGPT

### 3. Backend API

**Arquivo**: `open-webui-custom/backend/agents_api.py`

**Propósito**: Rotas API adicionais (caso Open WebUI precise de backend customizado)

**Rotas**:
- `GET /api/agents` - Lista agents
- `GET /api/agents/{agent_id}` - Detalhes do agent
- `POST /api/agents/{agent_id}/chat` - Inicia chat

**Nota**: Estas rotas foram implementadas no `auth-middleware` em vez de aqui, pois o middleware já está no caminho das requisições.

## Integração com Open WebUI

### Opção 1: Volume Mounts (Mais Simples)

Montar componentes Svelte e rotas via volumes no `docker-compose.yml`:

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    volumes:
      - open_webui_data:/app/backend/data
      # Mount custom components
      - ./open-webui-custom/frontend/AgentsSidebar.svelte:/app/src/lib/components/layout/AgentsSidebar.svelte:ro
      - ./open-webui-custom/frontend/AgentDetail.svelte:/app/src/routes/agents/[agentId]/+page.svelte:ro
```

### Opção 2: Build Customizado (Mais Robusto)

Criar Dockerfile que estende Open WebUI:

```dockerfile
FROM ghcr.io/open-webui/open-webui:main

# Copy custom components
COPY ./frontend/AgentsSidebar.svelte /app/src/lib/components/layout/
COPY ./frontend/AgentDetail.svelte /app/src/routes/agents/[agentId]/+page.svelte

# Rebuild frontend
RUN cd /app && npm run build
```

### Opção 3: Fork Completo (Controle Total)

1. Fork do repositório Open WebUI
2. Aplicar patches dos componentes
3. Modificar layout principal para incluir `<AgentsSidebar />`
4. Build e deploy

## Fluxo de Uso

### Cenário 1: Usuário VENDAS (emingues@gmail.com)

```
1. Login no Open WebUI
   ↓
2. Sidebar mostra "AI Agents":
   - Assistente Genérico
   - Agent Diagnóstico de Vendas
   ↓
3. Click em "Agent Diagnóstico de Vendas"
   ↓
4. Página de detalhes mostra 4 cards:
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
   e mensagem pré-preenchida:
   "Qual foi a taxa de conversão nos últimos 30 dias?
    Compare com o período anterior e identifique as
    principais fontes de tráfego."
   ↓
7. Envia mensagem
   ↓
8. MCP Adapter:
   - Valida permissão ✅
   - Identifica keywords: "conversão", "tráfego"
   - Chama MCP: analytics_get_conversion
   - Enriquece contexto com 847 chars de dados
   - Chama claude-sonnet com contexto enriquecido
   ↓
9. Retorna análise completa com dados reais
```

### Cenário 2: Usuário GERAL (geral@company.com)

```
1. Login no Open WebUI
   ↓
2. Sidebar mostra "AI Agents":
   - Assistente Genérico (apenas)
   ↓
3. NÃO vê "Agent Diagnóstico de Vendas"
   (sem permissão)
   ↓
4. Pode usar apenas modelos tradicionais
   no dropdown: gpt-3.5-turbo
```

## Vantagens

✅ **UX Familiar**
- UI similar ao ChatGPT (sidebar + cards)
- Usuários já sabem como usar

✅ **Separação de Conceitos**
- **Dropdown de modelos** = Modelos tradicionais (gpt-4, claude-sonnet)
- **Sidebar de agents** = Agents com MCPs e prompts

✅ **Onboarding Facilitado**
- Prompts de exemplo visíveis
- Não precisa decorar comandos
- Click para usar

✅ **Permissões Respeitadas**
- Sidebar busca `/api/agents` (valida permissões)
- Cada usuário vê apenas seus agents

✅ **Escalável**
- Novos agents aparecem automaticamente
- Prompts gerenciados no banco
- Sem hardcoding na UI

## Próximos Passos para Implementação

### 1. Testar Endpoints (Já Funcionam)

```bash
# Teste 1: Listar agents para VENDAS
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     -H "X-OpenWebUI-User-Id: user-1" \
     -H "X-OpenWebUI-User-Role: admin" \
     http://localhost:8000/api/agents | jq

# Resultado esperado: 2 agents

# Teste 2: Detalhes de um agent
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     -H "X-OpenWebUI-User-Id: user-1" \
     -H "X-OpenWebUI-User-Role: admin" \
     http://localhost:8000/api/agents/diagnostico-vendas | jq

# Resultado esperado: Agent com 4 prompts

# Teste 3: Verificar que agents NÃO aparecem em /v1/models
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/v1/models | jq '.data[] | .id'

# Resultado esperado: Apenas "gpt-4" e "claude-sonnet" (sem agents)
```

### 2. Integrar Componentes Svelte ao Open WebUI

**Método Recomendado: Volume Mounts**

1. Criar diretório de destino no Open WebUI container
2. Montar componentes via volumes
3. Modificar layout para incluir `<AgentsSidebar />`

**Alternativa: Fork**

1. Fork do Open WebUI
2. Copiar componentes para:
   - `src/lib/components/layout/AgentsSidebar.svelte`
   - `src/routes/agents/[agentId]/+page.svelte`
3. Modificar `src/routes/+layout.svelte`:
   ```svelte
   <script>
     import AgentsSidebar from '$lib/components/layout/AgentsSidebar.svelte';
   </script>

   <div class="app-container">
     <AgentsSidebar />
     <main>
       <slot />
     </main>
   </div>
   ```

### 3. Build e Deploy

```bash
# Rebuild auth-middleware (já tem os novos endpoints)
docker-compose up -d --build auth-middleware

# Restart Open WebUI (se usando volume mounts)
docker-compose restart open-webui

# Ou rebuild se usando Dockerfile customizado
docker-compose up -d --build open-webui
```

### 4. Validar

**Teste com usuário VENDAS**:
1. Login como emingues@gmail.com
2. Verificar sidebar mostra 2 agents
3. Click em "Agent Diagnóstico de Vendas"
4. Verificar 4 cards de prompts
5. Click em um card
6. Verificar chat abre com prompt pré-preenchido

**Teste com usuário GERAL**:
1. Login como geral@company.com
2. Verificar sidebar mostra 1 agent
3. Verificar NÃO vê "Agent Diagnóstico de Vendas"

## Troubleshooting

### Agents não aparecem na sidebar

**Sintoma**: Sidebar vazia ou erro

**Checklist**:
1. ✅ Auth Middleware rodando: `docker-compose ps auth-middleware`
2. ✅ Endpoint funcionando: `curl http://localhost:8000/api/agents`
3. ✅ MCP Adapter rodando: `docker-compose ps mcp-adapter`
4. ✅ Logs: `docker-compose logs -f auth-middleware`

### Cards de prompts não abrem chat

**Sintoma**: Click no card não faz nada

**Checklist**:
1. ✅ Console do navegador (F12 → Console)
2. ✅ Navegação: URL deve ser `/c/new?model={agent_id}&message={prompt}`
3. ✅ Logs: `docker-compose logs -f open-webui`

### Agents ainda aparecem no dropdown

**Sintoma**: Agents aparecem tanto na sidebar quanto no dropdown

**Solução**:
1. Verificar `auth-middleware/app.py` linha 182-219
2. Confirmar que `/v1/models` NÃO inclui agents
3. Restart middleware: `docker-compose restart auth-middleware`
4. Hard refresh no browser (Ctrl+Shift+R)

## Estado Atual da Branch

✅ **Completo**:
- Auth middleware com novos endpoints `/api/agents` e `/api/agents/{id}`
- Endpoint `/v1/models` modificado para NÃO incluir agents
- Componentes Svelte criados (AgentsSidebar.svelte, AgentDetail.svelte)
- Backend API de exemplo (agents_api.py)
- Documentação completa (README.md, este guia)

🔄 **Pendente**:
- Integração física dos componentes Svelte ao Open WebUI
  (via volume mounts ou fork)
- Modificação do layout principal do Open WebUI para incluir sidebar
- Testes E2E com usuários reais

## Recursos

- **Auth Middleware**: [auth-middleware/app.py](../auth-middleware/app.py)
- **Componentes Svelte**: [frontend/](./frontend/)
- **Documentação**: [README.md](./README.md)
- **Testes**: Ver seção "Próximos Passos" acima

## Contato

Para dúvidas ou suporte:
- Verificar logs: `docker-compose logs -f auth-middleware mcp-adapter open-webui`
- Testar endpoints: Ver seção "Próximos Passos para Implementação"
