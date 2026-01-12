# Implementação de Agents no Open WebUI

Este documento descreve a implementação completa da funcionalidade de Agents no Open WebUI customizado.

## Visão Geral

A funcionalidade de Agents permite que usuários visualizem e interajam com agents especializados através de uma interface gráfica intuitiva.

## Arquitetura

```
┌─────────────────┐
│   Open WebUI    │
│   (Frontend)    │
└────────┬────────┘
         │
         ├─ GET /api/agents (lista agents)
         │
         ├─ GET /api/agents/{id} (detalhes do agent)
         │
         └─ POST /v1/chat/completions (chat com agent)
                 │
                 ▼
         ┌──────────────────┐
         │ Auth Middleware  │
         │  (Port 8000)     │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │   MCP Adapter    │
         │  (Port 8001)     │
         └────────┬─────────┘
                  │
                  ▼
              Database
```

## Componentes Implementados

### 1. API Client Module

**Arquivo**: `open-webui/src/lib/apis/agents/index.ts`

```typescript
// Funções disponíveis:
getAgents(token, userEmail)      // Lista agents do usuário
getAgentById(token, userEmail, agentId)  // Detalhes de um agent
```

**Detalhes**:
- Integra com o backend via header `X-OpenWebUI-User-Email`
- Retorna dados estruturados dos agents e seus prompts
- Inclui tratamento de erros

### 2. Ícone Agent

**Arquivo**: `open-webui/src/lib/components/icons/Agent.svelte`

- Ícone SVG representando um robot/agent
- Customizável via props `className` e `strokeWidth`
- Consistente com o design system do Open WebUI

### 3. Menu Sidebar

**Arquivo**: `open-webui/src/lib/components/layout/Sidebar.svelte`

**Modificações**:
1. Import do ícone Agent (linha 65)
2. Botão colapsado (linhas 752-772)
   - Apenas ícone
   - Tooltip "Agentes"
   - Link para `/agents`
3. Botão expandido (linhas 986-1003)
   - Ícone + texto "Agentes"
   - Estilo consistente com outros itens
   - Posicionado entre Notes e Workspace

### 4. Página de Lista de Agents

**Arquivo**: `open-webui/src/routes/(app)/agents/+page.svelte`

**Funcionalidades**:
- Grid responsivo de cards (1-3 colunas)
- Cada card mostra:
  - Nome do agent
  - Descrição
  - Provider e modelo (anthropic/claude-3-haiku)
  - Número de prompts disponíveis
- Estados:
  - Loading (spinner)
  - Empty state (sem agents)
  - Lista de agents
- Click no card navega para `/agents/{id}`

**Layout**:
```
┌─────────────────────────────────────┐
│  Agentes                            │
│  Selecione um agente para iniciar...│
├─────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │Agent1│  │Agent2│  │Agent3│      │
│  └──────┘  └──────┘  └──────┘      │
└─────────────────────────────────────┘
```

### 5. Página de Detalhe do Agent

**Arquivo**: `open-webui/src/routes/(app)/agents/[id]/+page.svelte`

**Funcionalidades**:
- Header com botão "Voltar para Agentes"
- Informações do agent:
  - Ícone grande
  - Nome
  - Descrição detalhada
  - Provider e modelo
- Seção de prompts sugeridos:
  - Cada prompt em um card clicável
  - Mostra título e conteúdo
  - Seta indicando ação
- Click em prompt:
  1. Cria novo chat
  2. Seleciona o agent como modelo
  3. Preenche o prompt
  4. Navega para home com query params
  5. Auto-envia a mensagem
- Botão "Iniciar Chat com Agente" (sem prompt)

**Layout**:
```
┌─────────────────────────────────────┐
│  ← Voltar para Agentes              │
│                                      │
│  [icon]  Diagnóstico de Vendas      │
│          Agent especializado...      │
│          anthropic • claude-3-haiku  │
├─────────────────────────────────────┤
│  Prompts Sugeridos                  │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Top Produtos               →   │ │
│  │ Quais são os produtos...       │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ Faturamento Mensal         →   │ │
│  │ Qual foi o faturamento...      │ │
│  └────────────────────────────────┘ │
├─────────────────────────────────────┤
│  [   Iniciar Chat com Agente   ]    │
└─────────────────────────────────────┘
```

## Fluxo de Usuário

### Fluxo 1: Explorar Agents

```
1. User clica em "Agentes" no sidebar
   ↓
2. Visualiza grid de agents disponíveis
   ↓
3. Clica em um agent
   ↓
4. Vê detalhes e prompts sugeridos
```

### Fluxo 2: Usar Prompt Sugerido

```
1. User está na página de detalhe do agent
   ↓
2. Clica em um prompt sugerido
   ↓
3. Sistema cria novo chat com o agent
   ↓
4. Navega para home com prompt preenchido
   ↓
5. Prompt é enviado automaticamente
   ↓
6. Agent responde com streaming
```

### Fluxo 3: Chat Direto

```
1. User está na página de detalhe do agent
   ↓
2. Clica em "Iniciar Chat com Agente"
   ↓
3. Navega para home com agent selecionado
   ↓
4. User digita sua própria pergunta
   ↓
5. Agent responde com streaming
```

## Integração com Backend

### Endpoint: GET /api/agents

**Request**:
```http
GET /api/agents
X-OpenWebUI-User-Email: user@example.com
```

**Response**:
```json
{
  "success": true,
  "agents": [
    {
      "id": "diagnostico-vendas",
      "name": "Diagnóstico de Vendas",
      "description": "Agent especializado em análise de vendas...",
      "llm_provider": "anthropic",
      "llm_model": "claude-3-haiku",
      "prompt_count": 3
    }
  ]
}
```

### Endpoint: GET /api/agents/{id}

**Request**:
```http
GET /api/agents/diagnostico-vendas
X-OpenWebUI-User-Email: user@example.com
```

**Response**:
```json
{
  "success": true,
  "agent": {
    "id": "diagnostico-vendas",
    "name": "Diagnóstico de Vendas",
    "description": "Agent especializado em análise de vendas...",
    "llm_provider": "anthropic",
    "llm_model": "claude-3-haiku",
    "prompts": [
      {
        "title": "Top Produtos",
        "content": "Quais são os produtos mais vendidos nos últimos 30 dias?"
      },
      {
        "title": "Faturamento Mensal",
        "content": "Qual foi o faturamento total do último mês?"
      },
      {
        "title": "Performance por Categoria",
        "content": "Quais categorias tiveram melhor performance?"
      }
    ]
  }
}
```

### Endpoint: POST /v1/chat/completions

**Request**:
```http
POST /v1/chat/completions
Content-Type: application/json
X-OpenWebUI-User-Email: user@example.com

{
  "model": "diagnostico-vendas",
  "messages": [
    {"role": "user", "content": "Quais foram os produtos mais vendidos?"}
  ],
  "stream": true
}
```

**Response**: Server-Sent Events (SSE)
```
data: {"choices":[{"delta":{"content":"Análise"}}]}
data: {"choices":[{"delta":{"content":" dos"}}]}
...
data: [DONE]
```

## Estilos e Design

### Cores e Temas

- Suporte a modo claro e escuro
- Classes Tailwind:
  - `dark:bg-gray-900` - Background escuro
  - `dark:text-gray-400` - Texto secundário escuro
  - `hover:border-gray-300` - Hover states
  - `transition-all` - Animações suaves

### Responsividade

- Mobile first
- Breakpoints:
  - `md:` - 768px+
  - `lg:` - 1024px+
- Grid adaptativo:
  - 1 coluna (mobile)
  - 2 colunas (tablet)
  - 3 colunas (desktop)

### Ícones

- Todos os ícones SVG inline
- Stroke width consistente (1.5 ou 2)
- Classes size: `size-4`, `size-4.5`, `size-5`, `size-8`, `size-16`

## Arquivos Docker

### Dockerfile.custom

```dockerfile
FROM ghcr.io/open-webui/open-webui:v0.7.2

# Copy custom frontend files
COPY ./src /app/src

# Rebuild frontend with custom changes
WORKDIR /app
RUN npm ci && npm run build

# Back to original working directory
WORKDIR /app/backend

CMD ["bash", "start.sh"]
```

### docker-compose.yml (excerpt)

```yaml
open-webui:
  build:
    context: ./open-webui
    dockerfile: Dockerfile.custom
  container_name: open-webui-custom
  environment:
    - OPENAI_API_BASE_URL=http://auth-middleware:8000/v1
    - OPENAI_API_KEY=dummy
    - WEBUI_AUTH=true
  ports:
    - "8888:8080"
  volumes:
    - open_webui_data:/app/backend/data
```

## Testes

### Checklist de Testes

- [ ] Menu Agentes aparece no sidebar (colapsado e expandido)
- [ ] Página /agents carrega lista de agents
- [ ] Cards de agents mostram informações corretas
- [ ] Click no card navega para detalhe
- [ ] Página de detalhe mostra agent correto
- [ ] Prompts sugeridos são exibidos
- [ ] Click em prompt cria chat e envia mensagem
- [ ] Botão "Start Chat" funciona
- [ ] Agent responde corretamente
- [ ] Streaming funciona
- [ ] Modo escuro funciona
- [ ] Responsividade em mobile/tablet/desktop

### Comandos para Testar

```bash
# Rebuild Open WebUI
docker-compose build open-webui

# Start container
docker-compose up -d open-webui

# Ver logs
docker-compose logs -f open-webui

# Acessar
open http://localhost:8888
```

## Troubleshooting

### Problema: Agents não aparecem na lista

**Causa**: Usuário não tem agents configurados ou permissões incorretas

**Solução**:
1. Verificar se usuário existe na tabela `users`
2. Verificar se está no grupo correto (`vendas` ou `geral`)
3. Verificar se agent tem permissão para o grupo
4. Rodar seed novamente: `docker exec mcp-adapter python seed.py`

### Problema: Click em prompt não faz nada

**Causa**: Navegação ou criação de chat falhando

**Solução**:
1. Verificar console do browser (F12)
2. Verificar se `createNewChat` retorna erro
3. Verificar permissões do usuário
4. Verificar se token está válido

### Problema: Agent não responde

**Causa**: Problema com LiteLLM ou Claude

**Solução**:
1. Verificar logs do mcp-adapter: `docker-compose logs mcp-adapter`
2. Verificar se Claude key está válida
3. Verificar se virtual keys têm acesso ao modelo
4. Testar endpoint diretamente: `curl http://localhost:8000/v1/chat/completions`

## Próximas Melhorias

### Curto Prazo
- [ ] Adicionar busca/filtro na lista de agents
- [ ] Adicionar categorias/tags para agents
- [ ] Melhorar feedback visual ao clicar em prompts
- [ ] Adicionar animações de transição

### Médio Prazo
- [ ] Permitir favoritar agents
- [ ] Histórico de chats com cada agent
- [ ] Estatísticas de uso por agent
- [ ] Editor de prompts sugeridos

### Longo Prazo
- [ ] Criar agents via UI
- [ ] Marketplace de agents
- [ ] Compartilhamento de agents entre usuários
- [ ] Templates de agents por domínio

## Referências

- [Open WebUI Documentation](https://docs.openwebui.com/)
- [API Integration Guide](./API_INTEGRATION_GUIDE.md)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
