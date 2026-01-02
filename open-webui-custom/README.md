# Open WebUI - Custom Agents UI

Customização do Open WebUI para exibir agents no menu lateral (estilo ChatGPT GPTs) com cards de exemplo de prompts.

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                      Open WebUI                         │
│  ┌──────────────┐  ┌──────────────────────────────┐   │
│  │   Sidebar    │  │      Main Content            │   │
│  │              │  │  ┌────────────────────────┐  │   │
│  │  📊 Agents   │  │  │  Agent Detail Page     │  │   │
│  │  ├─ Agent 1  │  │  │  ┌──────┐  ┌──────┐   │  │   │
│  │  ├─ Agent 2  │──┼──┤  │Card 1│  │Card 2│   │  │   │
│  │  └─ Agent 3  │  │  │  └──────┘  └──────┘   │  │   │
│  │              │  │  │  ┌──────┐  ┌──────┐   │  │   │
│  │  💬 Chats    │  │  │  │Card 3│  │Card 4│   │  │   │
│  │  └─ Chat 1   │  │  │  └──────┘  └──────┘   │  │   │
│  └──────────────┘  │  └────────────────────────┘  │   │
│                    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │      Auth Middleware           │
         │  (Filtra agents do /models)    │
         └────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │       MCP Adapter              │
         │  GET /agents                   │
         │  GET /agents/{id}              │
         │  POST /agents/{id}/chat        │
         └────────────────────────────────┘
```

## Funcionalidades

### 1. Sidebar de Agents
- **Localização**: Menu lateral esquerdo (abaixo do logo, acima dos chats)
- **Conteúdo**: Lista de agents disponíveis para o usuário
- **Interação**: Click no agent abre a página de detalhes

### 2. Página de Detalhes do Agent
- **Localização**: `/agents/{agent_id}`
- **Conteúdo**:
  - Header com nome, descrição, modelo e provider
  - Grid de cards com prompts de exemplo (4 prompts por agent)
- **Interação**: Click no card inicia um chat com o prompt pré-preenchido

### 3. Filtro de Agents no Dropdown de Modelos
- **Modificação**: Agents NÃO aparecem no dropdown de seleção de modelos
- **Razão**: Agents têm UI dedicada (sidebar + detail page)
- **Implementação**: Auth middleware filtra agents da resposta `/v1/models`

## Estrutura de Arquivos

```
open-webui-custom/
├── README.md                          # Este arquivo
├── Dockerfile                         # Build customizado
├── backend/
│   └── agents_api.py                  # Rotas API para agents
├── frontend/
│   ├── AgentsSidebar.svelte          # Componente de sidebar
│   └── AgentDetail.svelte            # Página de detalhes
└── integration/
    ├── routes.py                      # Integração das rotas
    └── layout-patch.svelte            # Patch para layout principal
```

## Integração com Open WebUI

### Opção 1: Plugin/Extension (Recomendado)

Open WebUI suporta extensões via environment variables e custom mounting.

1. **Backend API Routes** (`backend/agents_api.py`):
   - Montar como plugin FastAPI
   - Adicionar rotas: `/api/agents`, `/api/agents/{id}`, `/api/agents/{id}/chat`

2. **Frontend Components**:
   - Injetar `AgentsSidebar.svelte` no layout principal
   - Adicionar rota `/agents/{id}` que renderiza `AgentDetail.svelte`

3. **Environment Variables**:
   ```bash
   ENABLE_AGENTS_UI=true
   MCP_ADAPTER_URL=http://mcp-adapter:8001
   ```

### Opção 2: Fork Completo

Para controle total, fazer fork do repositório Open WebUI:

```bash
# Clone Open WebUI
git clone https://github.com/open-webui/open-webui.git open-webui-fork

# Aplicar patches
cp backend/agents_api.py open-webui-fork/backend/apps/webui/routers/
cp frontend/AgentsSidebar.svelte open-webui-fork/src/lib/components/layout/
cp frontend/AgentDetail.svelte open-webui-fork/src/routes/agents/[agentId]/+page.svelte

# Modificar layout
# Editar: open-webui-fork/src/routes/+layout.svelte
# Adicionar: <AgentsSidebar /> acima da lista de chats
```

## Modificações no Auth Middleware

Para esconder agents do dropdown de modelos:

```python
# auth-middleware/app.py

@app.get("/v1/models")
async def get_models(request: Request):
    # ... código existente ...

    # 3. Buscar modelos tradicionais do LiteLLM
    # MODIFICAÇÃO: Não incluir agents na resposta
    try:
        virtual_key = get_virtual_key(group)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{LITELLM_URL}/v1/models",
                headers={"Authorization": f"Bearer {virtual_key}"}
            )

            if response.status_code == 200:
                litellm_response = response.json()
                litellm_models = litellm_response.get("data", [])

                # Adicionar apenas modelos tradicionais (não agents)
                all_models.extend(litellm_models)

    except Exception as e:
        print(f"[MODELS] Error fetching LiteLLM models: {e}")

    # NÃO retornar agents aqui (eles são buscados via /api/agents)
    return {"data": all_models, "object": "list"}
```

## Docker Compose

Atualizar `docker-compose.yml` para usar a versão customizada:

```yaml
services:
  open-webui:
    build:
      context: ./open-webui-custom
      dockerfile: Dockerfile
    container_name: open-webui-custom
    restart: unless-stopped
    depends_on:
      - auth-middleware
      - mcp-adapter
    environment:
      - OPENAI_API_BASE_URL=http://auth-middleware:8000/v1
      - OPENAI_API_KEY=dummy
      - WEBUI_AUTH=true
      - ENABLE_FORWARD_USER_INFO_HEADERS=true
      # Customizações
      - ENABLE_AGENTS_UI=true
      - MCP_ADAPTER_URL=http://mcp-adapter:8001
    volumes:
      - open_webui_data:/app/backend/data
      # Mount custom components
      - ./open-webui-custom/backend/agents_api.py:/app/backend/apps/webui/routers/agents.py
      - ./open-webui-custom/frontend/AgentsSidebar.svelte:/app/src/lib/components/layout/AgentsSidebar.svelte
      - ./open-webui-custom/frontend/AgentDetail.svelte:/app/src/routes/agents/[agentId]/+page.svelte
    ports:
      - "8888:8080"
    networks:
      - litellm-network
```

## Fluxo de Uso

### Usuário: emingues@gmail.com (VENDAS)

1. **Login no Open WebUI** → http://localhost:8888
2. **Sidebar mostra 2 agents**:
   - Assistente Genérico
   - Agent Diagnóstico de Vendas
3. **Click em "Agent Diagnóstico de Vendas"**
4. **Página de detalhes exibe 4 cards**:
   - Análise de conversão
   - Comparação mensal
   - Análise de funil
   - Performance técnica
5. **Click no card "Análise de conversão"**
6. **Abre chat novo com prompt pré-preenchido**:
   ```
   Qual foi a taxa de conversão nos últimos 30 dias?
   Compare com o período anterior e identifique as
   principais fontes de tráfego.
   ```
7. **Enviar mensagem** → MCP Adapter processa → Retorna análise

### Usuário: geral@company.com (GERAL)

1. **Login no Open WebUI**
2. **Sidebar mostra 1 agent**:
   - Assistente Genérico (apenas)
3. **NÃO vê Agent Diagnóstico de Vendas** (sem permissão)

## Vantagens desta Abordagem

✅ **UI Similar ao ChatGPT**
- Agents no menu lateral (como "GPTs")
- Cards de prompts clicáveis
- Experiência familiar

✅ **Separação de Conceitos**
- **Modelos** = Dropdown para seleção rápida (gpt-4, claude-sonnet)
- **Agents** = Sidebar com UI dedicada (agents com MCPs)

✅ **Permissões Respeitadas**
- Sidebar busca de `/api/agents` (que valida permissões)
- Cada usuário vê apenas seus agents

✅ **Exemplo de Prompts Visíveis**
- Cards grandes e clicáveis
- Usuário não precisa decorar prompts
- Onboarding facilitado

## Próximos Passos

1. ✅ Criar componentes Svelte (Sidebar + Detail Page)
2. ✅ Criar rotas API no backend (`agents_api.py`)
3. 🔄 Testar integração com Open WebUI
4. 🔄 Atualizar `auth-middleware` para filtrar agents do `/v1/models`
5. 🔄 Build e deploy com Docker Compose
6. 🔄 Validar com ambos usuários (VENDAS e GERAL)

## Teste Rápido

```bash
# Build custom Open WebUI
cd open-webui-custom
docker build -t open-webui-custom .

# Restart with custom image
docker-compose up -d open-webui

# Check logs
docker-compose logs -f open-webui
```

## Troubleshooting

### Agents não aparecem na sidebar
- Verificar logs: `docker-compose logs open-webui`
- Testar endpoint: `curl http://localhost:8888/api/agents`
- Verificar MCP Adapter: `curl http://localhost:8001/agents?user_email=emingues@gmail.com`

### Cards de prompts não abrem chat
- Verificar navegação: URL deve ser `/c/new?model={agent_id}&message={prompt}`
- Verificar logs do navegador (F12 → Console)

### Agents ainda aparecem no dropdown
- Atualizar `auth-middleware/app.py` para NÃO incluir agents em `/v1/models`
- Restart middleware: `docker-compose restart auth-middleware`
