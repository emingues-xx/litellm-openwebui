# Open WebUI Fork - Implementation Status

## Branch: `feat/view-customization-agents`

## Objetivo

Criar um fork do Open WebUI onde agents aparecem em uma sidebar dedicada (estilo ChatGPT GPTs) com páginas de detalhes mostrando cards de prompts clicáveis.

## Status Atual: ✅ Código Completo / ⏸️ Build Pendente

### ✅ Completado

1. **Fork do Open WebUI**
   - Clonado repositório oficial do Open WebUI
   - Localização: `open-webui-fork/`
   - .git removido para integração no repositório principal

2. **Componentes Svelte Criados**
   - `AgentsSidebar.svelte` - Componente de sidebar que lista agents
     - Localização: `open-webui-fork/src/lib/components/layout/AgentsSidebar.svelte`
     - Busca agents de `/api/agents`
     - Mostra ícone, nome, modelo e contagem de prompts
     - Click navega para página de detalhes

   - `AgentDetail.svelte` - Página de detalhes do agent
     - Localização: `open-webui-fork/src/routes/(app)/agents/[agentId]/+page.svelte`
     - Busca detalhes de `/api/agents/{agentId}`
     - Exibe 4 cards de prompts clicáveis
     - Click no card abre chat com prompt pré-preenchido

3. **Modificações no Layout**
   - Arquivo: `open-webui-fork/src/routes/(app)/+layout.svelte`
   - Adicionado import: `import AgentsSidebar from '$lib/components/layout/AgentsSidebar.svelte';`
   - Adicionado componente antes do Sidebar existente: `<AgentsSidebar />`

4. **Backend API Endpoints** (já implementados anteriormente)
   - `GET /api/agents` - Lista agents do usuário
   - `GET /api/agents/{id}` - Detalhes do agent com prompts
   - `GET /v1/models` - Modificado para NÃO incluir agents

5. **Configuração Docker**
   - Criado `Dockerfile.custom` para build do fork
   - Atualizado `docker-compose.yml` para usar fork customizado
   - Note: O Dockerfile usa `--legacy-peer-deps` para resolver conflitos de dependência

### ⏸️ Pendente

**Build do Frontend**

O build do Open WebUI customizado requer:

```bash
# No diretório open-webui-fork
npm ci --legacy-peer-deps
npm run build
```

**Nota**: Este build pode levar 10-30 minutos dependendo do hardware.

## Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────┐
│                Open WebUI (Fork Customizado)                │
│  ┌──────────────┐  ┌─────────────────────────────────────┐ │
│  │ AgentsSide  │  │         Main Content                │ │
│  │ bar.svelte  │  │  ┌────────────────────────────────┐  │ │
│  │             │  │  │  AgentDetail.svelte            │  │ │
│  │ • Agent 1   │──┼─►│  ┌──────┐  ┌──────┐            │  │ │
│  │ • Agent 2   │  │  │  │Card 1│  │Card 2│            │  │ │
│  │             │  │  │  └──────┘  └──────┘            │  │ │
│  │ Sidebar     │  │  │  ┌──────┐  ┌──────┐            │  │ │
│  │ • Chats     │  │  │  │Card 3│  │Card 4│            │  │ │
│  └──────────────┘  │  │  └──────┘  └──────┘            │  │ │
│                    │  └────────────────────────────────┘  │ │
│                    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │   Auth Middleware           │
              │  • GET /api/agents          │
              │  • GET /api/agents/{id}     │
              │  • GET /v1/models (sem agents)│
              └─────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │      MCP Adapter            │
              │  • Agents + Permissões      │
              │  • MCP Tool Calls           │
              └─────────────────────────────┘
```

## Fluxo de Uso

### Usuário VENDAS (emingues@gmail.com)

1. Login no Open WebUI
2. Vê AgentsSidebar com 2 agents:
   - Assistente Genérico
   - Agent Diagnóstico de Vendas
3. Click em "Agent Diagnóstico de Vendas"
4. Página mostra 4 cards:
   - Análise de conversão
   - Comparação mensal
   - Análise de funil
   - Performance técnica
5. Click em card → Chat abre com prompt pré-preenchido

### Usuário GERAL

1. Login no Open WebUI
2. Vê AgentsSidebar com 1 agent:
   - Assistente Genérico (apenas)
3. NÃO vê "Agent Diagnóstico de Vendas" (sem permissão)

## Como Buildar e Testar

### Opção 1: Build Local (Recomendado para desenvolvimento)

```bash
cd open-webui-fork

# Instalar dependências
npm ci --legacy-peer-deps

# Build frontend
npm run build

# Voltar para raiz do projeto
cd ..

# Build e start docker
docker-compose up -d --build open-webui
```

### Opção 2: Build via Docker (Produção)

```bash
# Build apenas open-webui
docker-compose build open-webui

# Start todos os serviços
docker-compose up -d
```

## Verificação

### 1. Verificar que container iniciou

```bash
docker ps | grep open-webui-custom
```

### 2. Testar endpoints

```bash
# Listar agents (VENDAS)
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     -H "X-OpenWebUI-User-Id: user-1" \
     -H "X-OpenWebUI-User-Role: admin" \
     http://localhost:8000/api/agents | jq

# Detalhes de um agent
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     -H "X-OpenWebUI-User-Id: user-1" \
     -H "X-OpenWebUI-User-Role: admin" \
     http://localhost:8000/api/agents/diagnostico-vendas | jq

# Verificar que agents NÃO aparecem em /v1/models
curl -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
     http://localhost:8000/v1/models | jq '.data[] | .id'
# Esperado: Apenas "gpt-4" e "claude-sonnet"
```

### 3. Testar UI

1. Acesse http://localhost:8888
2. Login como emingues@gmail.com
3. Verificar AgentsSidebar no lado esquerdo
4. Click em agent
5. Verificar página de detalhes com 4 cards
6. Click em card
7. Verificar que chat abre com prompt

## Commits Realizados

```bash
git log --oneline

821ee4c feat: Integrate custom Open WebUI fork with agents sidebar
[commit anterior] feat: Add custom agents UI with sidebar and prompt cards
[commit anterior] docs: Add EXEMPLOS_API_v2.md with new Agents UI endpoints
[commit anterior] docs: Update EXEMPLOS_API_v2.md - remove UI references, focus on API only
```

## Arquivos Modificados/Criados

### Novos Arquivos

- `open-webui-fork/` - Fork completo do Open WebUI
- `open-webui-fork/src/lib/components/layout/AgentsSidebar.svelte`
- `open-webui-fork/src/routes/(app)/agents/[agentId]/+page.svelte`
- `open-webui-fork/Dockerfile.custom`

### Arquivos Modificados

- `docker-compose.yml` - Atualizado para usar fork customizado
- `open-webui-fork/src/routes/(app)/+layout.svelte` - Adicionado AgentsSidebar

## Troubleshooting

### Problema: npm dependency conflict

**Solução**: Usar `--legacy-peer-deps`

```bash
npm ci --legacy-peer-deps
```

### Problema: Build muito lento

**Motivo**: Open WebUI tem muitas dependências (Svelte, Vite, etc.)

**Solução**: Paciência. O build pode levar 10-30 minutos.

### Problema: Container não inicia

**Debug**:

```bash
docker-compose logs open-webui
docker-compose ps
```

## Próximos Passos

1. ✅ Build completo do fork (via npm ou docker)
2. ✅ Testar AgentsSidebar aparece
3. ✅ Testar navegação para AgentDetail
4. ✅ Testar cards de prompts clicáveis
5. ✅ Validar com usuários VENDAS e GERAL

## Recursos

- **Implementation Guide**: `open-webui-custom/IMPLEMENTATION_GUIDE.md`
- **README**: `open-webui-custom/README.md`
- **API Examples**: `EXEMPLOS_API_v2.md`

## Contato/Suporte

Para dúvidas sobre a implementação:
1. Verificar logs: `docker-compose logs -f open-webui`
2. Verificar endpoints: Usar curl commands acima
3. Verificar componentes Svelte foram copiados corretamente
