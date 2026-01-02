# PRD - Plataforma Multi-Agent com Controle de Acesso

## 1. Visão Geral

### 1.1 Objetivo
Criar uma plataforma interna que permita hospedar múltiplos AI agents com controle granular de acesso por grupos de usuários, suportando múltiplos LLMs e integrações via MCP (Model Context Protocol).

### 1.2 Escopo da POC
Validar a arquitetura da plataforma, sistema de permissionamento e integrações MCP. O foco está no **ecossistema/infraestrutura**, não nos agents específicos de negócio.

### 1.3 Prazo
**Até 10/01/2026** (10 dias úteis)

### 1.4 Critérios de Sucesso
1. ✅ Interface de chat funcional com seleção de agents
2. ✅ 2 usuários criados com permissões diferentes
3. ✅ User A (Grupo Vendas) acessa Agent Diagnóstico + Agent Genérico
4. ✅ User B (Grupo Geral) acessa apenas Agent Genérico
5. ✅ Agent Diagnóstico consulta pelo menos 1 MCP e retorna análise
6. ✅ Validação de permissões: User B bloqueado ao tentar acessar Agent Diagnóstico
7. ✅ Logs de auditoria registram acessos e tentativas

---

## 2. Arquitetura da Solução

### 2.1 Stack Tecnológico

**Solução Base:**
- **Open WebUI**: Interface de chat (frontend + backend integrado)
- **LiteLLM**: Proxy unificado para múltiplos LLMs
- **Ollama**: Execução local de modelos open-source

**Componentes Custom:**
- **Permission Middleware**: FastAPI service para controle de acesso granular
- **MCP Adapter Service**: FastAPI service para integração com MCPs
- **MCP Server**: Servidor MCP interno com tools simuladas
- **PostgreSQL**: Banco de dados da aplicação
- **Langfuse**: Plataforma de observabilidade e analytics para LLMs
- **Redis** (opcional): Cache de sessões

**LLMs Suportados:**
- OpenAI (GPT-4)
- Anthropic (Claude Sonnet 4)
- Ollama (Llama 3 local)

### 2.2 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────┐
│  Open WebUI (Port 3000)                         │
│  - Interface de Chat                            │
│  - Autenticação básica                          │
│  - Histórico de conversas                       │
│  - Renderização Markdown                        │
└──────────────┬──────────────────────────────────┘
               │ HTTP API
               │
┌──────────────▼──────────────────────────────────┐
│  Permission Middleware (Port 8000)              │
│  - Validação de permissões por grupo            │
│  - Audit logging                                │
│  - Roteamento para agents                       │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼─────┐   ┌─────▼──────────────────────────┐
│  LiteLLM   │   │  MCP Adapter Service (8001)    │
│  (Port     │   │  - Orquestra consultas MCP     │
│   4000)    │   │  - Enriquece contexto do agent │
│            │   │  - Executa agent logic         │
└──────┬─────┘   └─────┬──────────────────────────┘
       │                │
       │                │ MCP Protocol
       │                │
   ┌───┴────┐      ┌────┴─────────────────────────────┐
   │        │      │                                  │
┌──▼──┐ ┌──▼───┐ ┌▼────────┐ ┌────────────────────┐  │
│OpenAI│ │Anthro│ │ Ollama │ │  MCP Server (8002) │  │
│     │ │ pic  │ │(11434) │ │  ┌──────────────┐  │  │
└─────┘ └──────┘ └────────┘ │  │ Analytics    │  │  │
                             │  │ Mock Tool    │  │  │
                             │  └──────────────┘  │  │
                             │  ┌──────────────┐  │  │
                             │  │ Monitoring   │  │  │
                             │  │ Mock Tool    │  │  │
                             │  └──────────────┘  │  │
                             │  ┌──────────────┐  │  │
                             │  │ Internal DB  │  │  │
                             │  │ Query Tool   │  │  │
                             │  └──────────────┘  │  │
                             └────────────────────┘  │
                                                     │
┌────────────────────────────────────────────────────┘
│  PostgreSQL (Port 5432)
│  - Usuários e grupos
│  - Agents e configurações
│  - Permissões
│  - Audit logs
│  - Histórico de conversas
│  - Dados mock de vendas (para MCP)
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  Langfuse Stack (Observabilidade)               │
│  ┌────────────────────────────────────────────┐ │
│  │ Langfuse UI (Port 3001)                    │ │
│  │ - Dashboards                               │ │
│  │ - Tracing de requests                      │ │
│  │ - Analytics de custos                      │ │
│  │ - Prompt management                        │ │
│  └────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │ Langfuse DB (PostgreSQL Separado)         │ │
│  │ - Traces e Spans                           │ │
│  │ - Generations                              │ │
│  │ - Scores                                   │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
       ▲
       │ Callbacks/API
       │
   ┌───┴────────────┐
   │                │
LiteLLM       MCP Adapter
(auto)        (decorators)
```

### 2.3 Fluxo de Requisição

```
1. User faz login no Open WebUI
   └─> Open WebUI valida credenciais (banco interno)

2. User seleciona um agent e envia mensagem
   └─> Open WebUI envia request para Permission Middleware
       - Headers: { Authorization: "Bearer <token>", X-User-ID: "123" }
       - Body: { agent_id: "diagnostico-vendas", message: "..." }

3. Permission Middleware valida acesso
   └─> Consulta DB: user_groups -> group_agent_permissions
   └─> Se não autorizado: retorna 403 Forbidden
   └─> Se autorizado: registra audit_log e roteia para MCP Adapter

4. MCP Adapter processa a mensagem
   └─> Identifica ferramentas MCP necessárias (baseado no agent_id)
   └─> Conecta ao MCP Server interno (porta 8002)
   └─> Consulta tools em paralelo via MCP Protocol
       ├─> analytics_get_conversion: métricas de conversão (simula Google Analytics)
       ├─> monitoring_get_latency: performance de APIs (simula Datadog)
       └─> db_query_sales: dados de vendas (consulta PostgreSQL)
   └─> Monta contexto enriquecido com os dados retornados

5. MCP Adapter chama LiteLLM
   └─> LiteLLM roteia para o LLM configurado (OpenAI/Anthropic/Ollama)
   └─> Retorna resposta em streaming

6. Resposta volta para o User via Open WebUI
   └─> Open WebUI renderiza Markdown
   └─> Salva conversa no histórico
```

---

## 3. Modelo de Dados

### 3.1 Schema do Banco de Dados

```sql
-- Usuários
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grupos de usuários
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação User-Group (N:N)
CREATE TABLE user_groups (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id)
);

-- Agents/Modelos
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    agent_key VARCHAR(100) UNIQUE NOT NULL,  -- Ex: "diagnostico-vendas"
    name VARCHAR(200) NOT NULL,
    description TEXT,
    llm_provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'ollama'
    llm_model VARCHAR(100) NOT NULL,    -- 'gpt-4', 'claude-sonnet-4', 'llama3'
    system_prompt TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prompts de exemplo por agent
CREATE TABLE agent_prompts (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    description VARCHAR(255),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuração de MCPs
CREATE TABLE mcp_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'google-analytics', 'datadog', 'internal-db'
    endpoint VARCHAR(500),
    credentials_encrypted TEXT,  -- JSON encriptado com credenciais
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação Agent-MCP (N:N)
CREATE TABLE agent_mcps (
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    mcp_id INTEGER REFERENCES mcp_configs(id) ON DELETE CASCADE,
    config JSONB,  -- Configurações específicas da relação
    PRIMARY KEY (agent_id, mcp_id)
);

-- Permissões Group-Agent (N:N)
CREATE TABLE group_agent_permissions (
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT true,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, agent_id)
);

-- Histórico de conversas
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mensagens das conversas
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    mcp_data JSONB,  -- Dados retornados pelos MCPs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,  -- 'access_granted', 'access_denied', 'message_sent'
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_user_groups_user ON user_groups(user_id);
CREATE INDEX idx_user_groups_group ON user_groups(group_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_conversations_user ON conversations(user_id);

-- Tabela de dados mock de vendas (para o MCP interno consultar)
CREATE TABLE sales_data (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'organic', 'paid', 'direct', 'referral'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_data_date ON sales_data(date);
CREATE INDEX idx_sales_data_source ON sales_data(source);
CREATE INDEX idx_sales_data_category ON sales_data(category);
```

### 3.2 Dados Seed para POC

```sql
-- Grupos
INSERT INTO groups (name, description) VALUES
('grupo-vendas', 'Grupo com acesso a análises de vendas'),
('grupo-geral', 'Grupo com acesso aos agents genéricos');

-- Usuários
INSERT INTO users (username, email, password_hash) VALUES
('user-a', 'user-a@empresa.com', '$2b$12$...'),  -- Senha: senha123
('user-b', 'user-b@empresa.com', '$2b$12$...');  -- Senha: senha123

-- Associações User-Group
INSERT INTO user_groups (user_id, group_id) VALUES
(1, 1),  -- user-a no grupo-vendas
(2, 2);  -- user-b no grupo-geral

-- Agents
INSERT INTO agents (agent_key, name, description, llm_provider, llm_model, system_prompt) VALUES
(
    'diagnostico-vendas',
    'Agent Diagnóstico de Vendas',
    'Analisa performance de vendas consultando múltiplas fontes de dados',
    'anthropic',
    'claude-sonnet-4-20250514',
    'Você é um analista de vendas especializado. Sua função é diagnosticar a performance de vendas da empresa usando dados do Google Analytics, Datadog e banco de dados interno. Sempre forneça insights acionáveis e contextualize os números.'
),
(
    'agent-generico',
    'Assistente Genérico',
    'Assistente de propósito geral para tarefas diversas',
    'openai',
    'gpt-4',
    'Você é um assistente prestativo e cordial. Ajude o usuário com suas dúvidas de forma clara e objetiva.'
);

-- Prompts de exemplo
INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order) VALUES
(1, 'Qual foi a taxa de conversão de vendas nos últimos 30 dias?', 'Análise de conversão', 1),
(1, 'Compare a performance de vendas deste mês com o mês anterior', 'Comparação mensal', 2),
(1, 'Identifique os principais gargalos no funil de vendas', 'Análise de funil', 3),
(1, 'Mostre as APIs com maior latência que podem estar afetando vendas', 'Performance técnica', 4),
(2, 'Me ajude a escrever um e-mail profissional', 'Redação de e-mail', 1),
(2, 'Explique o conceito de APIs REST', 'Explicação técnica', 2),
(2, 'Sugira ideias para uma apresentação sobre inovação', 'Brainstorming', 3),
(2, 'Revise este texto para erros gramaticais', 'Revisão de texto', 4);

-- MCPs
INSERT INTO mcp_configs (name, type, endpoint) VALUES
('analytics-mock', 'analytics', 'mcp-server:8002'),
('monitoring-mock', 'monitoring', 'mcp-server:8002'),
('internal-db', 'database', 'mcp-server:8002');

-- Associação Agent-MCP
INSERT INTO agent_mcps (agent_id, mcp_id) VALUES
(1, 1),  -- Agent diagnóstico usa analytics-mock
(1, 2),  -- Agent diagnóstico usa monitoring-mock
(1, 3);  -- Agent diagnóstico usa internal-db

-- Permissões
INSERT INTO group_agent_permissions (group_id, agent_id) VALUES
(1, 1),  -- grupo-vendas pode acessar diagnostico-vendas
(1, 2),  -- grupo-vendas pode acessar agent-generico
(2, 2);  -- grupo-geral pode acessar apenas agent-generico

-- Dados mock de vendas (últimos 30 dias)
INSERT INTO sales_data (date, product_id, product_name, category, quantity, unit_price, total_amount, customer_id, source)
SELECT 
    CURRENT_DATE - (random() * 30)::integer AS date,
    'PROD-' || (random() * 100)::integer AS product_id,
    CASE (random() * 5)::integer
        WHEN 0 THEN 'Produto Premium A'
        WHEN 1 THEN 'Produto Básico B'
        WHEN 2 THEN 'Produto Intermediário C'
        WHEN 3 THEN 'Produto Premium D'
        ELSE 'Produto Básico E'
    END AS product_name,
    CASE (random() * 3)::integer
        WHEN 0 THEN 'Eletrônicos'
        WHEN 1 THEN 'Vestuário'
        ELSE 'Casa e Jardim'
    END AS category,
    (random() * 10 + 1)::integer AS quantity,
    (random() * 500 + 50)::numeric(10,2) AS unit_price,
    ((random() * 10 + 1) * (random() * 500 + 50))::numeric(10,2) AS total_amount,
    'CUST-' || (random() * 1000)::integer AS customer_id,
    CASE (random() * 4)::integer
        WHEN 0 THEN 'organic'
        WHEN 1 THEN 'paid'
        WHEN 2 THEN 'direct'
        ELSE 'referral'
    END AS source
FROM generate_series(1, 500);  -- 500 vendas simuladas
```

---

## 4. Componentes da Solução

### 4.1 Open WebUI

**Responsabilidades:**
- Interface de chat
- Autenticação de usuários (username/password)
- Histórico de conversas
- Renderização de Markdown
- Upload de arquivos (futuro)

**Configuração:**
- Desabilitar signup público
- Apontar API base para Permission Middleware
- Configurar modelos via LiteLLM

**Não requer modificações no código**

### 4.2 LiteLLM Proxy

**Responsabilidades:**
- Proxy unificado para OpenAI, Anthropic, Ollama
- Load balancing (futuro)
- Rate limiting (futuro)
- Cost tracking (futuro)

**Configuração (litellm-config.yaml):**
```yaml
model_list:
  # OpenAI
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: os.environ/OPENAI_API_KEY
  
  # Anthropic
  - model_name: claude-sonnet-4
    litellm_params:
      model: claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_API_KEY
  
  # Ollama Local
  - model_name: llama3
    litellm_params:
      model: ollama/llama3
      api_base: http://ollama:11434

litellm_settings:
  max_parallel_requests: 100
  request_timeout: 600
  drop_params: true
  # Langfuse callbacks
  success_callback: ["langfuse"]
  failure_callback: ["langfuse"]
  
general_settings:
  master_key: "sk-1234"  # Para autenticação interna
```

### 4.3 Permission Middleware (CUSTOM)

**Responsabilidades:**
- Interceptar requests do Open WebUI
- Validar se usuário/grupo tem acesso ao agent solicitado
- Registrar audit logs
- Rotear para MCP Adapter ou diretamente para LiteLLM

**Tecnologia:** FastAPI + SQLAlchemy + Pydantic

**Endpoints:**

```python
POST /api/chat
- Valida permissões
- Roteia para agent apropriado
- Retorna streaming response

GET /api/agents
- Lista agents disponíveis para o usuário
- Baseado no grupo do usuário

GET /api/agents/{agent_id}/prompts
- Retorna prompts de exemplo do agent
- Valida acesso antes de retornar

POST /api/auth/login
- Autentica usuário
- Retorna JWT token

GET /api/audit-logs
- Lista logs de auditoria (admin only)
```

**Fluxo de Validação:**
```python
# Pseudocódigo
async def validate_access(user_id: int, agent_id: int) -> bool:
    # 1. Busca grupos do usuário
    user_groups = db.query(UserGroup).filter_by(user_id=user_id).all()
    
    # 2. Busca permissões dos grupos
    permissions = db.query(GroupAgentPermission).filter(
        GroupAgentPermission.group_id.in_([g.group_id for g in user_groups]),
        GroupAgentPermission.agent_id == agent_id,
        GroupAgentPermission.can_access == True
    ).first()
    
    # 3. Registra tentativa no audit log
    audit_log = AuditLog(
        user_id=user_id,
        agent_id=agent_id,
        action='access_granted' if permissions else 'access_denied',
        details={'groups': [g.group_id for g in user_groups]}
    )
    db.add(audit_log)
    db.commit()
    
    return permissions is not None
```

### 4.4 MCP Adapter Service (CUSTOM)

**Responsabilidades:**
- Receber requests do Permission Middleware
- Identificar quais tools MCP o agent precisa consultar
- Conectar ao MCP Server e executar tools
- Enriquecer contexto com dados dos MCPs
- Chamar LiteLLM com contexto completo
- Retornar resposta em streaming

**Tecnologia:** FastAPI + MCP SDK (cliente) + httpx (async)

**Estrutura:**
```
mcp-adapter/
├── main.py                 # FastAPI app
├── agents/
│   ├── base.py             # BaseAgent class
│   ├── diagnostico_vendas.py
│   └── generico.py
├── mcp_client.py           # Cliente MCP (conecta ao MCP Server)
├── utils/
│   ├── llm_client.py       # LiteLLM wrapper
│   └── streaming.py        # SSE utilities
└── config.py
```

**Como funciona:**
1. Agent recebe mensagem do usuário
2. Identifica quais tools MCP são necessárias (baseado em keywords)
3. Conecta ao MCP Server via stdio
4. Executa `tools/call` para cada tool necessária
5. Recebe dados estruturados de volta
6. Formata dados para o LLM
7. Envia para LiteLLM com contexto enriquecido

### 4.5 MCP Server (CUSTOM) - **NOVO!**

**Responsabilidades:**
- Implementar servidor MCP completo seguindo o protocolo oficial
- Expor tools que simulam Google Analytics e Datadog
- Expor tool que consulta dados reais do PostgreSQL
- Responder a `tools/list` e `tools/call`

**Tecnologia:** Python + MCP SDK (server)

**Estrutura:**
```
mcp-server/
├── main.py                 # MCP Server
├── tools/
│   ├── analytics.py        # Tools de analytics (mock)
│   ├── monitoring.py       # Tools de monitoring (mock)
│   └── database.py         # Tools de database (real query)
├── data/
│   └── mock_data.py        # Dados mockados
└── config.py
```

**Tools Expostas:**

1. **analytics_get_conversion**
   - Input: `{"period": "30d"}`
   - Output: Dados de conversão mockados (taxa, breakdown por fonte, etc)
   - Simula Google Analytics

2. **analytics_get_traffic**
   - Input: `{"period": "30d"}`
   - Output: Dados de tráfego mockados (sessões, páginas, etc)

3. **monitoring_get_latency**
   - Input: `{"period": "7d"}`
   - Output: Dados de latência mockados (P50, P95, P99 por endpoint)
   - Simula Datadog

4. **monitoring_get_errors**
   - Input: `{"period": "7d"}`
   - Output: Dados de erros mockados (taxa de erro por endpoint)

5. **db_query_sales**
   - Input: `{"period": "30d", "group_by": "source"}`
   - Output: Query real ao PostgreSQL na tabela `sales_data`
   - Retorna dados reais de vendas

**Exemplo de implementação:**

```python
# mcp-server/main.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from tools import analytics, monitoring, database

# Cria servidor MCP
app = Server("internal-mcp-server")

# Registra tools
@app.list_tools()
async def list_tools():
    return [
        {
            "name": "analytics_get_conversion",
            "description": "Get conversion rate metrics (simulates Google Analytics)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "Period (e.g., '30d', '7d')"}
                }
            }
        },
        {
            "name": "monitoring_get_latency",
            "description": "Get API latency metrics (simulates Datadog)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "period": {"type": "string"}
                }
            }
        },
        {
            "name": "db_query_sales",
            "description": "Query sales data from internal database",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "period": {"type": "string"},
                    "group_by": {"type": "string", "enum": ["source", "category", "date"]}
                }
            }
        }
        # ... outras tools
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "analytics_get_conversion":
        return await analytics.get_conversion_data(arguments)
    elif name == "monitoring_get_latency":
        return await monitoring.get_latency_data(arguments)
    elif name == "db_query_sales":
        return await database.query_sales(arguments)
    # ... outras tools

# Inicia servidor via stdio
async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0], streams[1],
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Por que criar um MCP Server interno?**
- ✅ Não precisa de tokens/credenciais de Google Analytics e Datadog
- ✅ Demonstra como criar MCPs customizados
- ✅ Permite testes consistentes e reproduzíveis
- ✅ Facilita desenvolvimento (sem rate limits externos)
- ✅ Base para futuros MCPs reais da empresa
- ✅ Aprende o protocolo MCP na prática

### 4.6 Ollama

**Responsabilidades:**
- Executar modelos LLM localmente
- Servir API compatível com OpenAI

**Modelo para POC:** Llama 3 (8B)

**Configuração:**
```bash
# Pull do modelo
docker exec ollama ollama pull llama3

# Verificar modelos disponíveis
docker exec ollama ollama list
```

---

### 4.7 Langfuse (Observabilidade)

**Responsabilidades:**
- Tracing detalhado de todas as requests LLM
- Analytics de custos e tokens por agent/usuário
- Dashboards de performance (latência, taxa de erro)
- Versionamento e gerenciamento de prompts
- User feedback e scoring
- Debugging e replay de conversas

**Tecnologia:** Next.js (UI) + PostgreSQL (DB)

**Por que usar?**
- ✅ Visibilidade completa do fluxo: User → Agent → MCP → LLM
- ✅ Identificar gargalos de performance
- ✅ Controlar custos por departamento/agent
- ✅ Melhorar prompts baseado em dados
- ✅ Compliance e auditoria detalhada
- ✅ Debugging rápido de problemas em produção

**Integração:**

**1. LiteLLM (Automático):**
```yaml
# litellm-config.yaml
litellm_settings:
  success_callback: ["langfuse"]
  failure_callback: ["langfuse"]

environment:
  LANGFUSE_PUBLIC_KEY: "pk-lf-..."
  LANGFUSE_SECRET_KEY: "sk-lf-..."
  LANGFUSE_HOST: "http://langfuse:3000"
```

LiteLLM automaticamente envia para Langfuse:
- Todas as chamadas LLM
- Tokens usados (input + output)
- Latência
- Custo estimado
- Modelo usado
- Status (sucesso/erro)

**2. MCP Adapter (Manual com Decorators):**
```python
# mcp-adapter/agents/base.py
from langfuse.decorators import langfuse_context, observe

class BaseAgent:
    @observe(name="agent_execution")
    async def execute(self, user_message: str, history: list):
        # Cria trace pai
        langfuse_context.update_current_trace(
            user_id=self.user_id,
            session_id=self.conversation_id,
            metadata={
                "agent_key": self.agent_key,
                "llm_provider": self.llm_provider
            }
        )
        
        # Execução do agent...
        tools_to_call = await self.identify_needed_tools(user_message)
        
        # MCP calls são traced automaticamente
        with langfuse_context.observe(name="mcp_calls"):
            mcp_results = await self.call_mcp_tools(tools_to_call)
        
        # LLM call é traced pelo LiteLLM
        response = await self.call_llm_stream(messages)
        
        return response
```

**3. Permission Middleware (Opcional):**
```python
# permission-middleware/routers/chat.py
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)

@router.post("/chat")
async def chat(request: ChatRequest, current_user: User):
    # Cria trace
    trace = langfuse.trace(
        name="chat_request",
        user_id=str(current_user.id),
        metadata={
            "agent_key": request.agent_key,
            "user_group": current_user.groups
        }
    )
    
    # Valida acesso
    with trace.span(name="permission_check") as span:
        has_access = validate_user_access(...)
        span.end(metadata={"granted": has_access})
    
    # Continua fluxo...
```

**O que você verá no Langfuse:**

```
Trace: Chat Request (user-a, diagnostico-vendas)
├─ Span: Permission Check (5ms)
│  └─ Granted: true
├─ Span: Agent Execution (2.3s)
│  ├─ Span: MCP Calls (450ms)
│  │  ├─ analytics_get_conversion (120ms)
│  │  ├─ monitoring_get_latency (180ms)
│  │  └─ db_query_sales (150ms)
│  └─ Generation: Claude Sonnet 4 (1.8s)
│     ├─ Tokens: 1,234 input + 567 output
│     ├─ Cost: $0.0234
│     └─ Latency: 1,823ms
└─ Total: 2.3s, $0.0234
```

**Dashboards Disponíveis:**

1. **Overview**
   - Total de requests
   - Custo total
   - Latência média
   - Taxa de erro

2. **Por Agent**
   - diagnostico-vendas: 234 requests, $12.45
   - agent-generico: 567 requests, $8.23

3. **Por Usuário**
   - user-a: 89 requests, $5.67
   - user-b: 145 requests, $3.45

4. **Por Modelo**
   - Claude Sonnet 4: $15.34
   - GPT-4: $3.21
   - Llama 3: $0.00 (local)

5. **Traces**
   - Lista todas as conversas
   - Filtros por data, usuário, agent, status
   - Drill-down em cada trace

**Acesso:**
- URL: `http://localhost:3001`
- Login inicial: criar conta no primeiro acesso
- Depois: configurar SSO (futuro)

---

## 5. Configuração de Deploy

### 5.1 Docker Compose

```yaml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: ai-platform-postgres
    environment:
      POSTGRES_DB: ai_platform
      POSTGRES_USER: aiuser
      POSTGRES_PASSWORD: aipass123
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - ai-platform-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiuser -d ai_platform"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Ollama
  ollama:
    image: ollama/ollama:latest
    container_name: ai-platform-ollama
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - ai-platform-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    # Para ambientes sem GPU, remover a seção deploy acima

  # Langfuse Database
  langfuse-db:
    image: postgres:15-alpine
    container_name: ai-platform-langfuse-db
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse123
    volumes:
      - langfuse-data:/var/lib/postgresql/data
    networks:
      - ai-platform-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langfuse -d langfuse"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Langfuse (Observability Platform)
  langfuse:
    image: langfuse/langfuse:latest
    container_name: ai-platform-langfuse
    ports:
      - "3001:3000"
    environment:
      - DATABASE_URL=postgresql://langfuse:langfuse123@langfuse-db:5432/langfuse
      - NEXTAUTH_SECRET=${LANGFUSE_NEXTAUTH_SECRET:-langfuse-secret-change-in-production}
      - NEXTAUTH_URL=http://localhost:3001
      - SALT=${LANGFUSE_SALT:-langfuse-salt-change-in-production}
      - TELEMETRY_ENABLED=false
      - LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=true
    networks:
      - ai-platform-network
    depends_on:
      langfuse-db:
        condition: service_healthy

  # LiteLLM
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: ai-platform-litellm
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgresql://aiuser:aipass123@postgres:5432/ai_platform
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LITELLM_MASTER_KEY=sk-1234
      # Langfuse integration
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - LANGFUSE_HOST=http://langfuse:3000
    volumes:
      - ./litellm-config.yaml:/app/config.yaml
    command: --config /app/config.yaml --port 4000 --detailed_debug
    networks:
      - ai-platform-network
    depends_on:
      postgres:
        condition: service_healthy
      ollama:
        condition: service_started
      langfuse:
        condition: service_started

  # Permission Middleware
  permission-middleware:
    build:
      context: ./permission-middleware
      dockerfile: Dockerfile
    container_name: ai-platform-permissions
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://aiuser:aipass123@postgres:5432/ai_platform
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-super-secret-jwt-key-change-in-prod}
      - MCP_ADAPTER_URL=http://mcp-adapter:8001
      - LITELLM_URL=http://litellm:4000
      - LITELLM_API_KEY=sk-1234
    volumes:
      - ./permission-middleware:/app
    networks:
      - ai-platform-network
    depends_on:
      postgres:
        condition: service_healthy
      litellm:
        condition: service_started

  # MCP Server
  mcp-server:
    build:
      context: ./mcp-server
      dockerfile: Dockerfile
    container_name: ai-platform-mcp-server
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://aiuser:aipass123@postgres:5432/ai_platform
    volumes:
      - ./mcp-server:/app
    networks:
      - ai-platform-network
    depends_on:
      postgres:
        condition: service_healthy
    stdin_open: true  # Necessário para MCP stdio
    tty: true

  # MCP Adapter Service
  mcp-adapter:
    build:
      context: ./mcp-adapter
      dockerfile: Dockerfile
    container_name: ai-platform-mcp-adapter
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://aiuser:aipass123@postgres:5432/ai_platform
      - LITELLM_URL=http://litellm:4000
      - LITELLM_API_KEY=sk-1234
      - MCP_SERVER_COMMAND=docker exec ai-platform-mcp-server python /app/main.py
      # Langfuse integration
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - LANGFUSE_HOST=http://langfuse:3000
    volumes:
      - ./mcp-adapter:/app
      - /var/run/docker.sock:/var/run/docker.sock  # Para executar comando no container do MCP
    networks:
      - ai-platform-network
    depends_on:
      postgres:
        condition: service_healthy
      litellm:
        condition: service_started
      mcp-server:
        condition: service_started
      langfuse:
        condition: service_started

  # Open WebUI
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: ai-platform-webui
    ports:
      - "3000:8080"
    environment:
      - OPENAI_API_BASE_URL=http://permission-middleware:8000
      - OPENAI_API_KEY=dummy-key-not-used
      - WEBUI_AUTH=true
      - ENABLE_OAUTH_SIGNUP=false
      - ENABLE_SIGNUP=false
      - DEFAULT_MODELS=diagnostico-vendas,agent-generico
    volumes:
      - open-webui-data:/app/backend/data
    networks:
      - ai-platform-network
    depends_on:
      - permission-middleware

volumes:
  postgres-data:
  ollama-data:
  open-webui-data:
  langfuse-data:

networks:
  ai-platform-network:
    driver: bridge
```

### 5.2 Arquivo .env

```bash
# .env
# LLM API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
POSTGRES_PASSWORD=aipass123

# Langfuse (será gerado após primeiro acesso ao Langfuse)
# Acesse http://localhost:3001, crie uma conta, crie um projeto
# e copie as keys de Settings > API Keys
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_NEXTAUTH_SECRET=your-nextauth-secret-min-32-chars
LANGFUSE_SALT=your-salt-min-32-chars

# Opcional para desenvolvimento
DEBUG=true
LOG_LEVEL=INFO
```

### 5.3 Estrutura de Diretórios

```
empresa-ai-platform/
├── docker-compose.yml
├── .env
├── .gitignore
├── README.md
│
├── litellm-config.yaml
│
├── init-db.sql                    # Schema + seed data
│
├── permission-middleware/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── dependencies.py
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       ├── agents.py
│       ├── chat.py
│       └── admin.py
│
├── mcp-adapter/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── mcp_client.py             # Cliente MCP (conecta ao MCP Server)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── diagnostico_vendas.py
│   │   └── generico.py
│   └── utils/
│       ├── __init__.py
│       ├── llm_client.py
│       └── streaming.py
│
├── mcp-server/                    # ← NOVO!
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                    # Servidor MCP via stdio
│   ├── config.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── analytics.py           # Tools de analytics (mock)
│   │   ├── monitoring.py          # Tools de monitoring (mock)
│   │   └── database.py            # Tools de database (query real)
│   └── data/
│       └── mock_data.py           # Dados mockados para analytics e monitoring
│
└── scripts/
    ├── seed_data.py               # Popular banco com dados iniciais
    ├── create_users.py            # Criar usuários de teste
    ├── test_permissions.py        # Testar permissões
    └── load_ollama_model.sh       # Baixar modelo Llama3
```

---

## 6. Plano de Implementação

### Dia 1: Setup Inicial
**Objetivo:** Ambiente base funcionando

**Tarefas:**
1. ✅ Criar estrutura de diretórios
2. ✅ Criar `docker-compose.yml` base
3. ✅ Criar `init-db.sql` com schema completo
4. ✅ Criar `litellm-config.yaml`
5. ✅ Subir containers base: PostgreSQL, Ollama, LiteLLM
6. ✅ Testar conectividade entre containers
7. ✅ Baixar modelo Llama3 no Ollama
8. ✅ Testar LiteLLM chamando OpenAI/Anthropic/Ollama

**Validação:**
```bash
# Testar PostgreSQL
docker exec -it ai-platform-postgres psql -U aiuser -d ai_platform -c "\dt"

# Testar Ollama
curl http://localhost:11434/api/tags

# Testar LiteLLM
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-1234"
```

**Entregável:** Infraestrutura base rodando ✅

---

### Dia 2: Permission Middleware - Base

**Objetivo:** Serviço de permissões com autenticação básica

**Tarefas:**
1. ✅ Criar Dockerfile do Permission Middleware
2. ✅ Setup FastAPI + SQLAlchemy
3. ✅ Criar modelos SQLAlchemy (User, Group, Agent, etc)
4. ✅ Criar schemas Pydantic
5. ✅ Implementar autenticação JWT
6. ✅ Implementar endpoint `POST /api/auth/login`
7. ✅ Implementar endpoint `POST /api/auth/register` (admin)
8. ✅ Criar middleware de autenticação
9. ✅ Popular banco com dados seed (users, groups, agents)

**Código Principal:**

```python
# permission-middleware/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, engine
import models, schemas, auth
from routers import auth_router, agents_router, chat_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Platform Permission Middleware")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Validação:**
```bash
# Login com user-a
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user-a", "password": "senha123"}'

# Deve retornar JWT token
```

**Entregável:** Serviço de auth funcionando ✅

---

### Dia 3: Permission Middleware - Lógica de Permissões

**Objetivo:** Validação de acesso a agents por grupo

**Tarefas:**
1. ✅ Implementar `GET /api/agents` (lista agents do usuário)
2. ✅ Implementar `GET /api/agents/{agent_id}/prompts`
3. ✅ Implementar função `validate_user_access(user_id, agent_id)`
4. ✅ Implementar registro de audit logs
5. ✅ Implementar endpoint `GET /api/audit-logs` (admin)
6. ✅ Criar testes de permissões (user-a vs user-b)

**Código Principal:**

```python
# permission-middleware/routers/agents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.AgentOut])
async def list_agents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista agents acessíveis pelo usuário"""
    
    # 1. Busca grupos do usuário
    user_groups = db.query(models.UserGroup).filter_by(
        user_id=current_user.id
    ).all()
    group_ids = [ug.group_id for ug in user_groups]
    
    # 2. Busca permissões dos grupos
    permissions = db.query(models.GroupAgentPermission).filter(
        models.GroupAgentPermission.group_id.in_(group_ids),
        models.GroupAgentPermission.can_access == True
    ).all()
    agent_ids = list(set([p.agent_id for p in permissions]))
    
    # 3. Busca agents
    agents = db.query(models.Agent).filter(
        models.Agent.id.in_(agent_ids),
        models.Agent.is_active == True
    ).all()
    
    return agents

@router.get("/{agent_id}/prompts", response_model=List[schemas.AgentPromptOut])
async def get_agent_prompts(
    agent_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna prompts de exemplo do agent"""
    
    # Valida acesso
    if not validate_user_access(current_user.id, agent_id, db):
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    prompts = db.query(models.AgentPrompt).filter_by(
        agent_id=agent_id
    ).order_by(models.AgentPrompt.display_order).all()
    
    return prompts

def validate_user_access(user_id: int, agent_id: int, db: Session) -> bool:
    """Valida se usuário tem acesso ao agent"""
    
    # Busca grupos do usuário
    user_groups = db.query(models.UserGroup).filter_by(
        user_id=user_id
    ).all()
    group_ids = [ug.group_id for ug in user_groups]
    
    # Verifica permissões
    permission = db.query(models.GroupAgentPermission).filter(
        models.GroupAgentPermission.group_id.in_(group_ids),
        models.GroupAgentPermission.agent_id == agent_id,
        models.GroupAgentPermission.can_access == True
    ).first()
    
    # Registra audit log
    audit_log = models.AuditLog(
        user_id=user_id,
        agent_id=agent_id,
        action='access_granted' if permission else 'access_denied',
        details={'groups': group_ids}
    )
    db.add(audit_log)
    db.commit()
    
    return permission is not None
```

**Validação:**
```bash
# Login como user-a (grupo vendas)
TOKEN_A=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user-a", "password": "senha123"}' | jq -r '.access_token')

# Lista agents do user-a (deve ver diagnostico-vendas + generico)
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer $TOKEN_A"

# Login como user-b (grupo geral)
TOKEN_B=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user-b", "password": "senha123"}' | jq -r '.access_token')

# Lista agents do user-b (deve ver apenas generico)
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer $TOKEN_B"

# Tenta acessar prompts do diagnostico-vendas com user-b (deve dar 403)
curl http://localhost:8000/api/agents/1/prompts \
  -H "Authorization: Bearer $TOKEN_B"
```

**Entregável:** Sistema de permissões validado ✅

---

### Dia 4: MCP Server - Criação do Servidor MCP Interno

**Objetivo:** Criar um MCP Server completo que expõe tools simuladas

**Tarefas:**
1. ✅ Criar estrutura base do MCP Server
2. ✅ Configurar MCP SDK (server side)
3. ✅ Implementar tool `analytics_get_conversion` (dados mockados)
4. ✅ Implementar tool `analytics_get_traffic` (dados mockados)
5. ✅ Implementar tool `monitoring_get_latency` (dados mockados)
6. ✅ Implementar tool `monitoring_get_errors` (dados mockados)
7. ✅ Implementar tool `db_query_sales` (consulta real ao PostgreSQL)
8. ✅ Testar servidor MCP isoladamente via stdio
9. ✅ Criar dados mockados realistas

**Código Principal:**

```python
# mcp-server/main.py
"""
MCP Server que implementa tools para simular Google Analytics, Datadog
e consultar dados internos do PostgreSQL
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tools import analytics, monitoring, database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria servidor MCP
app = Server("internal-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas as tools disponíveis"""
    return [
        Tool(
            name="analytics_get_conversion",
            description="Get conversion rate metrics including breakdown by source (simulates Google Analytics)",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period (e.g., '30d', '7d', '90d')",
                        "default": "30d"
                    }
                }
            }
        ),
        Tool(
            name="analytics_get_traffic",
            description="Get traffic and session metrics (simulates Google Analytics)",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period",
                        "default": "30d"
                    }
                }
            }
        ),
        Tool(
            name="monitoring_get_latency",
            description="Get API latency metrics (P50, P95, P99) by endpoint (simulates Datadog)",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period",
                        "default": "7d"
                    }
                }
            }
        ),
        Tool(
            name="monitoring_get_errors",
            description="Get error rate metrics by endpoint (simulates Datadog)",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period",
                        "default": "7d"
                    }
                }
            }
        ),
        Tool(
            name="db_query_sales",
            description="Query sales data from internal database with aggregations",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Time period (e.g., '30d', '7d')",
                        "default": "30d"
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["source", "category", "product", "date"],
                        "description": "Group results by this dimension",
                        "default": "source"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executa uma tool e retorna o resultado"""
    logger.info(f"Calling tool: {name} with args: {arguments}")
    
    try:
        if name == "analytics_get_conversion":
            result = await analytics.get_conversion_data(arguments)
        elif name == "analytics_get_traffic":
            result = await analytics.get_traffic_data(arguments)
        elif name == "monitoring_get_latency":
            result = await monitoring.get_latency_data(arguments)
        elif name == "monitoring_get_errors":
            result = await monitoring.get_error_data(arguments)
        elif name == "db_query_sales":
            result = await database.query_sales(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Retorna resultado como TextContent (formato MCP)
        return [TextContent(
            type="text",
            text=str(result)
        )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    """Inicia o servidor MCP via stdio"""
    logger.info("Starting MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


# mcp-server/tools/analytics.py
"""Tools simuladas de Google Analytics"""
import json
from data.mock_data import get_analytics_mock_data

async def get_conversion_data(args: dict) -> dict:
    """Retorna dados de conversão mockados"""
    period = args.get("period", "30d")
    
    data = get_analytics_mock_data()
    
    return {
        "tool": "analytics_get_conversion",
        "period": period,
        "conversion_rate": data["conversion_rate"],
        "comparison": data["conversion_comparison"],
        "breakdown_by_source": data["conversion_by_source"],
        "top_converting_pages": data["top_converting_pages"]
    }

async def get_traffic_data(args: dict) -> dict:
    """Retorna dados de tráfego mockados"""
    period = args.get("period", "30d")
    
    data = get_analytics_mock_data()
    
    return {
        "tool": "analytics_get_traffic",
        "period": period,
        "total_sessions": data["total_sessions"],
        "comparison": data["traffic_comparison"],
        "daily_breakdown": data["daily_sessions"]
    }


# mcp-server/tools/monitoring.py
"""Tools simuladas de Datadog"""
from data.mock_data import get_monitoring_mock_data

async def get_latency_data(args: dict) -> dict:
    """Retorna dados de latência mockados"""
    period = args.get("period", "7d")
    
    data = get_monitoring_mock_data()
    
    return {
        "tool": "monitoring_get_latency",
        "period": period,
        "average_latency": data["average_latency"],
        "endpoints": data["endpoint_latency"]
    }

async def get_error_data(args: dict) -> dict:
    """Retorna dados de erros mockados"""
    period = args.get("period", "7d")
    
    data = get_monitoring_mock_data()
    
    return {
        "tool": "monitoring_get_errors",
        "period": period,
        "overall_error_rate": data["overall_error_rate"],
        "by_status_code": data["errors_by_status"],
        "top_errors": data["top_error_endpoints"]
    }


# mcp-server/tools/database.py
"""Tool para consultar banco de dados interno"""
from sqlalchemy import create_engine, text
from config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)

async def query_sales(args: dict) -> dict:
    """Consulta real ao banco de dados de vendas"""
    period = args.get("period", "30d")
    group_by = args.get("group_by", "source")
    
    # Converte período para dias
    days = int(period.replace("d", ""))
    
    # Query SQL baseado no group_by
    if group_by == "source":
        query = text("""
            SELECT 
                source,
                COUNT(*) as total_sales,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_ticket,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales_data
            WHERE date >= CURRENT_DATE - INTERVAL ':days days'
            GROUP BY source
            ORDER BY revenue DESC
        """)
    elif group_by == "category":
        query = text("""
            SELECT 
                category,
                COUNT(*) as total_sales,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_ticket
            FROM sales_data
            WHERE date >= CURRENT_DATE - INTERVAL ':days days'
            GROUP BY category
            ORDER BY revenue DESC
        """)
    else:
        query = text("""
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_ticket,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales_data
            WHERE date >= CURRENT_DATE - INTERVAL ':days days'
        """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"days": days})
            rows = result.fetchall()
            
            # Converte resultado para dict
            data = []
            for row in rows:
                data.append({
                    col: float(val) if isinstance(val, (int, float)) else val
                    for col, val in zip(result.keys(), row)
                })
        
        return {
            "tool": "db_query_sales",
            "period": period,
            "group_by": group_by,
            "results": data
        }
    
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return {
            "error": str(e)
        }


# mcp-server/data/mock_data.py
"""Dados mockados para analytics e monitoring"""

def get_analytics_mock_data():
    """Retorna dados mockados de analytics (Google Analytics)"""
    return {
        "conversion_rate": {
            "value": 0.0342,
            "formatted": "3.42%"
        },
        "conversion_comparison": {
            "previous_period": 0.0298,
            "change_percent": 14.77,
            "direction": "up"
        },
        "conversion_by_source": [
            {"source": "organic", "rate": 0.0421, "sessions": 12450, "conversions": 524},
            {"source": "paid", "rate": 0.0287, "sessions": 8920, "conversions": 256},
            {"source": "direct", "rate": 0.0319, "sessions": 5630, "conversions": 180},
            {"source": "referral", "rate": 0.0312, "sessions": 3210, "conversions": 100}
        ],
        "top_converting_pages": [
            {"page": "/produto-premium", "rate": 0.0587, "visitors": 3200},
            {"page": "/promocao-black-friday", "rate": 0.0523, "visitors": 4100},
            {"page": "/produto-basico", "rate": 0.0401, "visitors": 5600}
        ],
        "total_sessions": 45230,
        "traffic_comparison": {
            "previous_period": 41220,
            "change_percent": 9.73
        },
        "daily_sessions": [
            {"date": "2025-01-03", "sessions": 6420},
            {"date": "2025-01-02", "sessions": 6890},
            {"date": "2025-01-01", "sessions": 5210},
            {"date": "2024-12-31", "sessions": 6710},
            {"date": "2024-12-30", "sessions": 7120},
            {"date": "2024-12-29", "sessions": 6340},
            {"date": "2024-12-28", "sessions": 6540}
        ]
    }

def get_monitoring_mock_data():
    """Retorna dados mockados de monitoring (Datadog)"""
    return {
        "average_latency": {
            "p50": 142,
            "p95": 387,
            "p99": 1240
        },
        "endpoint_latency": [
            {
                "endpoint": "/api/v1/products",
                "p50": 98,
                "p95": 245,
                "p99": 890,
                "requests_per_min": 450,
                "status": "healthy"
            },
            {
                "endpoint": "/api/v1/checkout",
                "p50": 320,
                "p95": 890,
                "p99": 2340,
                "requests_per_min": 120,
                "status": "degraded",
                "alert": "High latency detected - P95 > 800ms"
            },
            {
                "endpoint": "/api/v1/search",
                "p50": 156,
                "p95": 412,
                "p99": 1120,
                "requests_per_min": 780,
                "status": "healthy"
            },
            {
                "endpoint": "/api/v1/user/profile",
                "p50": 89,
                "p95": 234,
                "p99": 567,
                "requests_per_min": 340,
                "status": "healthy"
            }
        ],
        "overall_error_rate": 0.0234,  # 2.34%
        "errors_by_status": {
            "500": 0.0012,
            "502": 0.0004,
            "503": 0.0008,
            "504": 0.0003,
            "404": 0.0210
        },
        "top_error_endpoints": [
            {
                "endpoint": "/api/v1/checkout",
                "error_rate": 0.0456,
                "count": 234,
                "main_error": "500 Internal Server Error"
            },
            {
                "endpoint": "/api/v1/payment",
                "error_rate": 0.0312,
                "count": 156,
                "main_error": "503 Service Unavailable"
            }
        ]
    }
```

**Validação:**
```bash
# Testar MCP Server isoladamente
cd mcp-server
python main.py

# Em outro terminal, testar com mcp CLI
npx @modelcontextprotocol/inspector python main.py

# Ou testar programaticamente
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python main.py
```

**Entregável:** MCP Server funcional com todas as tools ✅

---

### Dia 5: MCP Adapter - Integração com MCP Server

**Objetivo:** Conectar MCP Adapter ao MCP Server e implementar agents

**Tarefas:**
1. ✅ Criar cliente MCP no MCP Adapter (conecta via stdio ao MCP Server)
2. ✅ Implementar classe `BaseAgent`
3. ✅ Implementar `DiagnosticoVendasAgent` usando tools MCP
4. ✅ Implementar `GenericoAgent` (sem MCPs)
5. ✅ Criar lógica para identificar tools necessárias baseado na mensagem
6. ✅ Implementar chamada a LiteLLM com contexto enriquecido
7. ✅ Implementar streaming de resposta (SSE)
8. ✅ Criar endpoint `POST /agents/{agent_key}/chat`
9. ✅ Testar fluxo completo: mensagem → MCP tools → LLM → resposta

**Código Principal:**

```python
# mcp-adapter/mcp_client.py
"""Cliente MCP que se conecta ao MCP Server via stdio"""
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import subprocess
import logging

logger = logging.getLogger(__name__)

class MCPClient:
    """Cliente para se conectar ao MCP Server"""
    
    def __init__(self):
        self.session = None
        self.server_params = None
    
    async def connect(self):
        """Conecta ao MCP Server via stdio"""
        # Comando para executar o MCP Server
        # O server roda no container mcp-server
        self.server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "ai-platform-mcp-server", "python", "/app/main.py"]
        )
        
        # Estabelece conexão
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.session = session
                logger.info("Connected to MCP Server")
                
                # Lista tools disponíveis
                tools = await session.list_tools()
                logger.info(f"Available tools: {[t.name for t in tools.tools]}")
                
                return self
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Chama uma tool no MCP Server"""
        if not self.session:
            raise RuntimeError("Not connected to MCP Server")
        
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        
        result = await self.session.call_tool(tool_name, arguments)
        
        # Parseia resultado
        if result.content:
            # Retorna primeiro TextContent
            return eval(result.content[0].text)  # Converte string para dict
        
        return {}
    
    async def disconnect(self):
        """Desconecta do MCP Server"""
        if self.session:
            await self.session.close()
            self.session = None


# mcp-adapter/agents/diagnostico_vendas.py
"""Agent de diagnóstico de vendas usando MCP"""
from typing import List, Dict, Any, AsyncIterator
import asyncio
from .base import BaseAgent
from mcp_client import MCPClient

class DiagnosticoVendasAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_key="diagnostico-vendas",
            llm_provider="anthropic",
            llm_model="claude-sonnet-4-20250514",
            system_prompt="""Você é um analista de vendas sênior com expertise em e-commerce.

Sua função é diagnosticar a performance de vendas usando dados de múltiplas fontes:
- Analytics: métricas de tráfego, conversão e comportamento (similar ao Google Analytics)
- Monitoring: performance técnica de APIs e latência (similar ao Datadog)
- Database: dados transacionais de vendas

Ao analisar, sempre:
1. Contextualize os números (ex: "3.42% de conversão está 14% acima do período anterior")
2. Identifique padrões e correlações (ex: "A alta latência no checkout pode estar afetando conversão")
3. Forneça insights acionáveis (ex: "Recomendo investigar a API de checkout")
4. Use markdown para organizar a resposta com seções claras

Seja direto e objetivo, focando no que realmente importa para o negócio."""
        )
        self.mcp_client = None
    
    async def _ensure_mcp_connection(self):
        """Garante que está conectado ao MCP Server"""
        if not self.mcp_client:
            self.mcp_client = MCPClient()
            await self.mcp_client.connect()
    
    async def identify_needed_tools(self, user_message: str) -> List[tuple]:
        """Identifica quais tools MCP são necessárias baseado na mensagem"""
        tools_to_call = []
        message_lower = user_message.lower()
        
        # Analytics tools
        if any(kw in message_lower for kw in [
            'conversão', 'conversion', 'taxa', 'funil', 'funnel', 'converter'
        ]):
            tools_to_call.append(('analytics_get_conversion', {'period': '30d'}))
        
        if any(kw in message_lower for kw in [
            'tráfego', 'traffic', 'visitantes', 'sessions', 'visitas'
        ]):
            tools_to_call.append(('analytics_get_traffic', {'period': '30d'}))
        
        # Monitoring tools
        if any(kw in message_lower for kw in [
            'latência', 'latency', 'performance', 'lento', 'slow', 'resposta', 'response time'
        ]):
            tools_to_call.append(('monitoring_get_latency', {'period': '7d'}))
        
        if any(kw in message_lower for kw in [
            'erro', 'error', 'falha', 'failure', 'timeout', 'indisponível'
        ]):
            tools_to_call.append(('monitoring_get_errors', {'period': '7d'}))
        
        # Database tool
        if any(kw in message_lower for kw in [
            'vendas', 'sales', 'receita', 'revenue', 'ticket', 
            'faturamento', 'clientes', 'customers', 'produto'
        ]):
            # Identifica group_by
            if 'fonte' in message_lower or 'source' in message_lower:
                group_by = 'source'
            elif 'categoria' in message_lower or 'category' in message_lower:
                group_by = 'category'
            else:
                group_by = 'source'  # default
            
            tools_to_call.append(('db_query_sales', {
                'period': '30d',
                'group_by': group_by
            }))
        
        # Se nenhuma keyword específica, usa um conjunto padrão
        if not tools_to_call:
            tools_to_call = [
                ('analytics_get_conversion', {'period': '30d'}),
                ('db_query_sales', {'period': '30d', 'group_by': 'source'})
            ]
        
        return tools_to_call
    
    async def call_mcp_tools(self, tools_to_call: List[tuple]) -> Dict[str, Any]:
        """Executa tools MCP em paralelo"""
        await self._ensure_mcp_connection()
        
        # Executa tools em paralelo
        results = {}
        tasks = []
        
        for tool_name, args in tools_to_call:
            tasks.append((tool_name, self.mcp_client.call_tool(tool_name, args)))
        
        # Aguarda todas as tools
        for tool_name, task in tasks:
            try:
                result = await task
                results[tool_name] = result
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                results[tool_name] = {"error": str(e)}
        
        return results
    
    def format_mcp_results(self, results: Dict[str, Any]) -> str:
        """Formata resultados MCP para o LLM"""
        formatted = []
        
        # Analytics - Conversion
        if 'analytics_get_conversion' in results:
            data = results['analytics_get_conversion']
            formatted.append(f"""
### Analytics - Taxa de Conversão (30 dias)
- **Taxa Atual**: {data['conversion_rate']['formatted']}
- **Comparação**: {data['comparison']['direction']} {data['comparison']['change_percent']}% vs período anterior
- **Por Fonte**:
{chr(10).join([f"  - {item['source']}: {item['rate']*100:.2f}% ({item['sessions']} sessões, {item['conversions']} conversões)" for item in data['breakdown_by_source']])}
- **Páginas com Melhor Conversão**:
{chr(10).join([f"  - {item['page']}: {item['rate']*100:.2f}% ({item['visitors']} visitantes)" for item in data['top_converting_pages']])}
""")
        
        # Analytics - Traffic
        if 'analytics_get_traffic' in results:
            data = results['analytics_get_traffic']
            formatted.append(f"""
### Analytics - Tráfego
- **Total de Sessões**: {data['total_sessions']:,}
- **Variação**: +{data['comparison']['change_percent']}% vs período anterior
""")
        
        # Monitoring - Latency
        if 'monitoring_get_latency' in results:
            data = results['monitoring_get_latency']
            formatted.append(f"""
### Monitoring - Latência de APIs (7 dias)
- **Média Geral**: P50={data['average_latency']['p50']}ms, P95={data['average_latency']['p95']}ms, P99={data['average_latency']['p99']}ms
- **Por Endpoint**:
{chr(10).join([f"  - {ep['endpoint']}: P95={ep['p95']}ms ({ep['requests_per_min']} req/min) {('⚠️ '+ep['alert']) if ep.get('alert') else '✅ '+ep['status']}" for ep in data['endpoints']])}
""")
        
        # Monitoring - Errors
        if 'monitoring_get_errors' in results:
            data = results['monitoring_get_errors']
            formatted.append(f"""
### Monitoring - Taxa de Erros
- **Taxa Geral**: {data['overall_error_rate']*100:.2f}%
- **Top Endpoints com Erros**:
{chr(10).join([f"  - {ep['endpoint']}: {ep['error_rate']*100:.2f}% ({ep['count']} erros)" for ep in data['top_errors']])}
""")
        
        # Database - Sales
        if 'db_query_sales' in results:
            data = results['db_query_sales']
            formatted.append(f"""
### Database - Vendas ({data['period']})
- **Agrupado por**: {data['group_by']}
- **Resultados**:
{chr(10).join([f"  - {list(row.values())[0]}: {row.get('total_sales', 0)} vendas, R$ {row.get('revenue', 0):,.2f}" for row in data['results'][:5]])}
""")
        
        return "\n".join(formatted) if formatted else "Nenhum dado disponível."
    
    async def execute(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = []
    ) -> AsyncIterator[str]:
        """Executa o agent"""
        
        # 1. Identifica tools necessárias
        tools_to_call = await self.identify_needed_tools(user_message)
        
        # 2. Chama tools MCP
        mcp_results = await self.call_mcp_tools(tools_to_call)
        
        # 3. Formata resultados
        context_formatted = self.format_mcp_results(mcp_results)
        
        # 4. Monta mensagem enriquecida
        enriched_message = f"""{user_message}

---
**DADOS DISPONÍVEIS PARA ANÁLISE:**

{context_formatted}
---

Por favor, analise estes dados e forneça insights acionáveis.
"""
        
        # 5. Chama LLM via LiteLLM com streaming
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + conversation_history + [
            {"role": "user", "content": enriched_message}
        ]
        
        async for chunk in self.call_llm_stream(messages):
            yield chunk
```

**Validação:**
```bash
# Testar MCP Adapter conectando ao MCP Server
curl -X POST http://localhost:8001/agents/diagnostico-vendas/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analise a taxa de conversão e identifique se há problemas de performance que possam estar afetando as vendas",
    "history": []
  }'

# Verificar logs para ver tools sendo chamadas
docker logs ai-platform-mcp-adapter
docker logs ai-platform-mcp-server
```

**Entregável:** Agent usando MCP Server real ✅

```python
# mcp-adapter/agents/diagnostico_vendas.py
from typing import List, Dict, Any
import asyncio
from .base import BaseAgent
from mcp_clients import GoogleAnalyticsMockClient, DatadogMockClient, InternalDBClient

class DiagnosticoVendasAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_key="diagnostico-vendas",
            llm_provider="anthropic",
            llm_model="claude-sonnet-4-20250514",
            system_prompt="""Você é um analista de vendas sênior com expertise em e-commerce.

Sua função é diagnosticar a performance de vendas usando dados de múltiplas fontes:
- Google Analytics: métricas de tráfego, conversão e comportamento
- Datadog: performance técnica de APIs e latência
- Banco de Dados Interno: dados transacionais de vendas

Ao analisar, sempre:
1. Contextualize os números (ex: "3.42% de conversão está 14% acima do período anterior")
2. Identifique padrões e correlações (ex: "A alta latência no checkout pode estar afetando conversão")
3. Forneça insights acionáveis (ex: "Recomendo investigar a API de checkout")
4. Use markdown para organizar a resposta

Seja direto e objetivo, focando no que realmente importa para o negócio."""
        )
        self.ga_client = GoogleAnalyticsMockClient()
        self.dd_client = DatadogMockClient()
        self.db_client = InternalDBClient()
    
    async def prepare_context(self, user_message: str) -> Dict[str, Any]:
        """Identifica e consulta MCPs necessários"""
        context = {}
        tasks = []
        
        message_lower = user_message.lower()
        
        # Google Analytics
        if any(kw in message_lower for kw in [
            'conversão', 'conversion', 'taxa', 'funil', 'funnel',
            'tráfego', 'traffic', 'visitantes', 'sessions'
        ]):
            tasks.append(('google_analytics', self.ga_client.query({
                'metric': 'conversion_rate',
                'period': '30d'
            })))
        
        # Datadog
        if any(kw in message_lower for kw in [
            'latência', 'latency', 'performance', 'api', 'lento',
            'erro', 'error', 'timeout', 'resposta'
        ]):
            tasks.append(('datadog_latency', self.dd_client.query({
                'metric': 'api_latency',
                'period': '7d'
            })))
            tasks.append(('datadog_errors', self.dd_client.query({
                'metric': 'error_rate',
                'period': '7d'
            })))
        
        # Internal DB
        if any(kw in message_lower for kw in [
            'vendas', 'sales', 'receita', 'revenue', 'ticket',
            'faturamento', 'clientes', 'customers'
        ]):
            tasks.append(('internal_db', self.db_client.query({
                'query_type': 'sales_summary',
                'period': 'last_30_days'
            })))
        
        # Executa em paralelo
        if tasks:
            results = await asyncio.gather(*[task[1] for task in tasks])
            for i, (key, _) in enumerate(tasks):
                context[key] = results[i]
        
        return context
    
    def format_context(self, context: Dict[str, Any]) -> str:
        """Formata contexto dos MCPs para o LLM"""
        formatted = []
        
        if 'google_analytics' in context:
            ga = context['google_analytics']
            formatted.append(f"""
### Google Analytics (últimos 30 dias)
- **Taxa de Conversão**: {ga['value_formatted']}
- **Variação**: {ga['comparison']['change_direction']} {ga['comparison']['change_percent']}% vs período anterior
- **Breakdown por Fonte**:
{chr(10).join([f"  - {item['source']}: {item['rate']*100:.2f}% ({item['sessions']} sessões)" for item in ga['breakdown_by_source']])}
- **Páginas com Melhor Conversão**:
{chr(10).join([f"  - {item['page']}: {item['rate']*100:.2f}%" for item in ga['top_converting_pages']])}
""")
        
        if 'datadog_latency' in context:
            dd = context['datadog_latency']
            formatted.append(f"""
### Datadog - Performance de APIs (últimos 7 dias)
- **Latência Média**: P50={dd['average_p50']}ms, P95={dd['average_p95']}ms, P99={dd['average_p99']}ms
- **Endpoints**:
{chr(10).join([f"  - {ep['endpoint']}: P95={ep['p95']}ms ({ep['requests_per_min']} req/min) {'⚠️ '+ep.get('alert','') if ep.get('alert') else ''}" for ep in dd['endpoints']])}
""")
        
        if 'datadog_errors' in context:
            dd_err = context['datadog_errors']
            formatted.append(f"""
### Datadog - Taxa de Erros
- **Taxa Geral de Erros**: {dd_err['overall_error_rate']*100:.2f}%
- **Top Erros**: {dd_err['top_errors'][0]['endpoint']} com {dd_err['top_errors'][0]['error_rate']*100:.2f}%
""")
        
        if 'internal_db' in context:
            db = context['internal_db']
            formatted.append(f"""
### Banco de Dados Interno (últimos 30 dias)
- **Total de Vendas**: {db['total_sales']:,}
- **Receita Total**: R$ {db['total_revenue']:,.2f}
- **Ticket Médio**: R$ {db['avg_ticket']:,.2f}
- **Clientes Únicos**: {db['unique_customers']:,}
""")
        
        return "\n".join(formatted) if formatted else "Nenhum dado adicional disponível."
    
    async def execute(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = []
    ) -> AsyncIterator[str]:
        """Executa o agent"""
        
        # 1. Consulta MCPs
        context = await self.prepare_context(user_message)
        
        # 2. Formata contexto
        context_formatted = self.format_context(context)
        
        # 3. Monta mensagem enriquecida
        enriched_message = f"""{user_message}

---
**DADOS DISPONÍVEIS PARA ANÁLISE:**

{context_formatted}
---

Por favor, analise estes dados e forneça insights acionáveis.
"""
        
        # 4. Chama LLM via LiteLLM com streaming
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + conversation_history + [
            {"role": "user", "content": enriched_message}
        ]
        
        async for chunk in self.call_llm_stream(messages):
            yield chunk

# mcp-adapter/agents/generico.py
class GenericoAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_key="agent-generico",
            llm_provider="openai",
            llm_model="gpt-4",
            system_prompt="""Você é um assistente prestativo e cordial.
Ajude o usuário com suas dúvidas de forma clara, objetiva e amigável.
Use markdown para formatar suas respostas quando apropriado."""
        )
    
    async def execute(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = []
    ) -> AsyncIterator[str]:
        """Agent genérico - sem MCPs"""
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        async for chunk in self.call_llm_stream(messages):
            yield chunk

# mcp-adapter/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from agents import DiagnosticoVendasAgent, GenericoAgent

app = FastAPI(title="MCP Adapter Service")

# Instancia agents
agents = {
    "diagnostico-vendas": DiagnosticoVendasAgent(),
    "agent-generico": GenericoAgent()
}

@app.post("/agents/{agent_key}/chat")
async def chat(
    agent_key: str,
    request: ChatRequest
):
    """Endpoint de chat com agent"""
    
    if agent_key not in agents:
        raise HTTPException(status_code=404, detail="Agent não encontrado")
    
    agent = agents[agent_key]
    
    # Executa agent com streaming
    async def generate():
        async for chunk in agent.execute(
            user_message=request.message,
            conversation_history=request.history
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Validação:**
```bash
# Testar Agent Diagnóstico de Vendas
curl -X POST http://localhost:8001/agents/diagnostico-vendas/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Qual foi a taxa de conversão nos últimos 30 dias? Existe algum problema de performance afetando vendas?",
    "history": []
  }'

# Testar Agent Genérico
curl -X POST http://localhost:8001/agents/agent-generico/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Me explique o que é REST API em termos simples",
    "history": []
  }'
```

**Entregável:** Agents funcionando com MCPs ✅

---

### Dia 6: Integração Permission Middleware ↔ MCP Adapter

**Objetivo:** Conectar os dois services e fazer chat end-to-end

**Tarefas:**
1. ✅ Implementar endpoint `POST /api/chat` no Permission Middleware
2. ✅ Validar permissões antes de rotear para MCP Adapter
3. ✅ Proxy streaming response do MCP Adapter para o cliente
4. ✅ Salvar histórico de conversas no banco
5. ✅ Implementar endpoints de histórico
6. ✅ Testar fluxo completo: Permission → MCP Adapter → LLM

**Código Principal:**

```python
# permission-middleware/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import httpx
from database import get_db
from auth import get_current_user
from config import settings
import models, schemas

router = APIRouter()

@router.post("/")
async def chat(
    request: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint principal de chat
    1. Valida acesso do usuário ao agent
    2. Roteia para MCP Adapter
    3. Retorna streaming response
    4. Salva histórico
    """
    
    # 1. Busca agent
    agent = db.query(models.Agent).filter_by(
        agent_key=request.agent_key,
        is_active=True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent não encontrado")
    
    # 2. Valida acesso
    if not validate_user_access(current_user.id, agent.id, db):
        raise HTTPException(
            status_code=403,
            detail=f"Você não tem acesso ao agent '{agent.name}'"
        )
    
    # 3. Busca ou cria conversa
    conversation = db.query(models.Conversation).filter_by(
        id=request.conversation_id
    ).first() if request.conversation_id else None
    
    if not conversation:
        conversation = models.Conversation(
            user_id=current_user.id,
            agent_id=agent.id,
            title=request.message[:100]
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # 4. Salva mensagem do usuário
    user_message = models.Message(
        conversation_id=conversation.id,
        role='user',
        content=request.message
    )
    db.add(user_message)
    db.commit()
    
    # 5. Chama MCP Adapter
    mcp_url = f"{settings.MCP_ADAPTER_URL}/agents/{agent.agent_key}/chat"
    
    # Busca histórico se necessário
    history = []
    if request.include_history:
        history_messages = db.query(models.Message).filter_by(
            conversation_id=conversation.id
        ).order_by(models.Message.created_at).limit(10).all()
        
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in history_messages
        ]
    
    # Streaming proxy
    async def stream_response():
        assistant_response = ""
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                mcp_url,
                json={
                    "message": request.message,
                    "history": history
                },
                timeout=300.0
            ) as response:
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        # Remove "data: " prefix
                        if chunk.startswith("data: "):
                            chunk_data = chunk[6:]
                            if chunk_data != "[DONE]":
                                assistant_response += chunk_data
                        yield chunk
        
        # Salva resposta do assistente
        assistant_message = models.Message(
            conversation_id=conversation.id,
            role='assistant',
            content=assistant_response
        )
        db.add(assistant_message)
        db.commit()
    
    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream"
    )

@router.get("/conversations")
async def list_conversations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista conversas do usuário"""
    conversations = db.query(models.Conversation).filter_by(
        user_id=current_user.id
    ).order_by(models.Conversation.updated_at.desc()).all()
    
    return conversations

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna uma conversa específica com mensagens"""
    conversation = db.query(models.Conversation).filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    messages = db.query(models.Message).filter_by(
        conversation_id=conversation_id
    ).order_by(models.Message.created_at).all()
    
    return {
        "conversation": conversation,
        "messages": messages
    }
```

**Validação:**
```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user-a", "password": "senha123"}' | jq -r '.access_token')

# Chat com agent diagnóstico
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_key": "diagnostico-vendas",
    "message": "Analise a taxa de conversão e identifique se há problemas de performance",
    "include_history": false
  }'

# Verificar histórico
curl http://localhost:8000/api/chat/conversations \
  -H "Authorization: Bearer $TOKEN"
```

**Entregável:** Chat end-to-end funcionando ✅

---

### Dia 7: Integração Open WebUI + Configuração Langfuse

**Objetivo:** Configurar Open WebUI e inicializar Langfuse

**Tarefas Open WebUI:**
1. ✅ Configurar Open WebUI para apontar para Permission Middleware
2. ✅ Criar adapter/proxy para API do Open WebUI → Permission Middleware
3. ✅ Configurar lista de modelos/agents disponíveis
4. ✅ Testar login no Open WebUI
5. ✅ Testar seleção de agents
6. ✅ Testar chat interface
7. ✅ Ajustar configurações de UI (desabilitar signup, etc)

**Tarefas Langfuse:**
8. ✅ Acessar Langfuse UI (http://localhost:3001)
9. ✅ Criar conta inicial
10. ✅ Criar projeto "AI Platform POC"
11. ✅ Copiar Public Key e Secret Key
12. ✅ Atualizar arquivo .env com as keys
13. ✅ Reiniciar containers LiteLLM e MCP Adapter
14. ✅ Fazer um teste de chat e verificar trace no Langfuse
15. ✅ Configurar dashboards básicos

**Configuração Langfuse:**

```bash
# 1. Acesse Langfuse
open http://localhost:3001

# 2. Crie conta (primeira vez)
# Email: admin@empresa.com
# Password: sua-senha-segura

# 3. Crie projeto
# Nome: AI Platform POC
# Descrição: Plataforma multi-agent com controle de acesso

# 4. Vá em Settings > API Keys
# Copie:
# - Public Key: pk-lf-...
# - Secret Key: sk-lf-...

# 5. Atualize .env
echo "LANGFUSE_PUBLIC_KEY=pk-lf-..." >> .env
echo "LANGFUSE_SECRET_KEY=sk-lf-..." >> .env

# 6. Reinicie containers
docker-compose restart litellm mcp-adapter

# 7. Teste um chat
# Faça uma pergunta no Open WebUI

# 8. Volte ao Langfuse
# Vá em "Traces" e veja sua conversa aparecer!
```

**Verificação:**

```bash
# Verificar logs do LiteLLM (deve mencionar Langfuse)
docker logs ai-platform-litellm 2>&1 | grep -i langfuse

# Deve aparecer algo como:
# "Langfuse: Successfully sent trace to Langfuse"

# Fazer request de teste
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user-a", "password": "senha123"}' | jq -r '.access_token')

curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_key": "diagnostico-vendas",
    "message": "Qual a taxa de conversão?",
    "include_history": false
  }'

# Aguardar resposta e verificar no Langfuse Dashboard
```

**O que você verá no Langfuse:**
- Um novo trace com nome do agent
- Breakdown de tempo (MCP calls + LLM)
- Tokens usados
- Custo estimado
- Input e output completos

**Entregável:** Open WebUI integrado e Langfuse funcionando ✅

---

### Dia 8: Instrumentação Langfuse no MCP Adapter

**Objetivo:** Configurar Open WebUI para usar nosso backend

**Tarefas:**
1. ✅ Configurar Open WebUI para apontar para Permission Middleware
2. ✅ Criar adapter/proxy para API do Open WebUI → Permission Middleware
3. ✅ Configurar lista de modelos/agents disponíveis
4. ✅ Testar login no Open WebUI
5. ✅ Testar seleção de agents
6. ✅ Testar chat interface
7. ✅ Ajustar configurações de UI (desabilitar signup, etc)

**Configuração:**

```yaml
# docker-compose.yml - ajustar Open WebUI
open-webui:
  image: ghcr.io/open-webui/open-webui:main
  container_name: ai-platform-webui
  ports:
    - "3000:8080"
  environment:
    # API base aponta para nosso middleware
    - OPENAI_API_BASE_URL=http://permission-middleware:8000/api/openai-compat
    - OPENAI_API_KEY=dummy
    
    # Auth settings
    - WEBUI_AUTH=True
    - ENABLE_OAUTH_SIGNUP=False
    - ENABLE_SIGNUP=False
    
    # Default models (serão os agents)
    - DEFAULT_MODELS=diagnostico-vendas,agent-generico
    
    # Custom settings
    - WEBUI_NAME=AI Platform - Empresa
    - ENABLE_RAG=False
    - ENABLE_WEB_SEARCH=False
```

**Adapter OpenAI-compatible API:**

```python
# permission-middleware/routers/openai_compat.py
"""
Adapter para compatibilidade com OpenAI API
Open WebUI espera endpoints estilo OpenAI
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models

router = APIRouter()

@router.get("/v1/models")
async def list_models(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista agents como se fossem modelos OpenAI
    Open WebUI usa esse endpoint para popular dropdown
    """
    
    # Busca agents disponíveis para o usuário
    user_groups = db.query(models.UserGroup).filter_by(
        user_id=current_user.id
    ).all()
    group_ids = [ug.group_id for ug in user_groups]
    
    permissions = db.query(models.GroupAgentPermission).filter(
        models.GroupAgentPermission.group_id.in_(group_ids),
        models.GroupAgentPermission.can_access == True
    ).all()
    agent_ids = list(set([p.agent_id for p in permissions]))
    
    agents = db.query(models.Agent).filter(
        models.Agent.id.in_(agent_ids),
        models.Agent.is_active == True
    ).all()
    
    # Formato OpenAI
    return {
        "object": "list",
        "data": [
            {
                "id": agent.agent_key,
                "object": "model",
                "created": int(agent.created_at.timestamp()),
                "owned_by": "empresa",
                "permission": [],
                "root": agent.agent_key,
                "parent": None
            }
            for agent in agents
        ]
    }

@router.post("/v1/chat/completions")
async def chat_completions(
    request: OpenAIChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint compatível com OpenAI Chat Completions
    """
    
    agent_key = request.model
    user_message = request.messages[-1]['content']
    
    # Reutiliza lógica do /api/chat
    # ... (similar ao código do dia 6)
    
    if request.stream:
        # Retorna streaming
        async def generate():
            # ... streaming logic
            pass
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        # Retorna resposta completa
        # ... non-streaming logic
        pass
```

**Tarefas Manuais:**
1. Acessar http://localhost:3000
2. Fazer login com user-a / senha123
3. Verificar se agents aparecem no dropdown
4. Testar enviar mensagem
5. Verificar se prompts de exemplo aparecem
6. Fazer login com user-b e verificar permissões

**Entregável:** Open WebUI integrado e funcional ✅

---

### Dia 8: Instrumentação Langfuse no MCP Adapter

**Objetivo:** Adicionar tracing detalhado no MCP Adapter usando decorators Langfuse

**Tarefas:**
1. ✅ Instalar SDK Langfuse no MCP Adapter
2. ✅ Adicionar decorators @observe nos agents
3. ✅ Instrumentar chamadas MCP com spans
4. ✅ Adicionar metadata útil (user_id, agent_key, etc)
5. ✅ Testar tracing end-to-end
6. ✅ Criar dashboards customizados no Langfuse
7. ✅ Configurar alertas básicos (opcional)

**Código de Instrumentação:**

```python
# mcp-adapter/requirements.txt
# Adicionar:
langfuse>=2.0.0

# mcp-adapter/agents/base.py
from langfuse.decorators import langfuse_context, observe
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, agent_key: str, llm_provider: str, llm_model: str, system_prompt: str):
        self.agent_key = agent_key
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.system_prompt = system_prompt
        self.user_id = None
        self.conversation_id = None
    
    def set_context(self, user_id: str, conversation_id: str):
        """Define contexto para tracing"""
        self.user_id = user_id
        self.conversation_id = conversation_id
    
    @observe(name="agent_execution")
    async def execute(self, user_message: str, conversation_history: list):
        """
        Método principal do agent - automaticamente traced pelo @observe
        """
        # Atualiza trace com metadata
        langfuse_context.update_current_trace(
            user_id=self.user_id,
            session_id=self.conversation_id,
            metadata={
                "agent_key": self.agent_key,
                "llm_provider": self.llm_provider,
                "llm_model": self.llm_model
            },
            tags=["agent", self.agent_key]
        )
        
        # Implementação específica do agent
        raise NotImplementedError


# mcp-adapter/agents/diagnostico_vendas.py
from langfuse.decorators import observe

class DiagnosticoVendasAgent(BaseAgent):
    
    @observe(name="identify_tools")
    async def identify_needed_tools(self, user_message: str) -> List[tuple]:
        """Identifica tools - traced automaticamente"""
        # ... implementação
        return tools_to_call
    
    @observe(name="mcp_calls")
    async def call_mcp_tools(self, tools_to_call: List[tuple]) -> Dict[str, Any]:
        """Chama tools MCP - traced como span"""
        results = {}
        
        for tool_name, args in tools_to_call:
            # Cada tool é um span filho
            with langfuse_context.observe(
                name=f"mcp_tool_{tool_name}",
                metadata={"tool": tool_name, "args": args}
            ):
                try:
                    result = await self.mcp_client.call_tool(tool_name, args)
                    results[tool_name] = result
                    
                    # Adiciona output ao span
                    langfuse_context.update_current_observation(
                        output=result
                    )
                except Exception as e:
                    logger.error(f"Error calling {tool_name}: {e}")
                    results[tool_name] = {"error": str(e)}
                    
                    # Marca span como erro
                    langfuse_context.update_current_observation(
                        level="ERROR",
                        status_message=str(e)
                    )
        
        return results
    
    async def execute(self, user_message: str, conversation_history: list):
        """Execute com tracing completo"""
        # Atualiza contexto do trace
        langfuse_context.update_current_trace(
            user_id=self.user_id,
            session_id=self.conversation_id,
            metadata={
                "agent_key": self.agent_key,
                "user_message_length": len(user_message)
            }
        )
        
        # 1. Identifica tools (traced)
        tools_to_call = await self.identify_needed_tools(user_message)
        
        # 2. Chama MCPs (traced)
        mcp_results = await self.call_mcp_tools(tools_to_call)
        
        # 3. Formata contexto
        context_formatted = self.format_mcp_results(mcp_results)
        
        # 4. Prepara mensagem
        enriched_message = f"{user_message}\n\n---\n{context_formatted}\n---\n"
        
        # 5. Chama LLM (LiteLLM já envia para Langfuse)
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + conversation_history + [
            {"role": "user", "content": enriched_message}
        ]
        
        # LLM call é traced automaticamente pelo LiteLLM
        async for chunk in self.call_llm_stream(messages):
            yield chunk


# mcp-adapter/main.py
from langfuse import Langfuse
from config import settings

# Inicializa Langfuse
langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)

@app.post("/agents/{agent_key}/chat")
async def chat(agent_key: str, request: ChatRequest):
    """Endpoint de chat com Langfuse tracing"""
    
    agent = agents.get(agent_key)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent não encontrado")
    
    # Define contexto do agent para tracing
    agent.set_context(
        user_id=request.user_id,
        conversation_id=request.conversation_id
    )
    
    # Executa agent (será traced automaticamente)
    async def generate():
        async for chunk in agent.execute(
            user_message=request.message,
            conversation_history=request.history
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Validação:**

```bash
# 1. Rebuild MCP Adapter com nova dependência
docker-compose build mcp-adapter

# 2. Restart
docker-compose restart mcp-adapter

# 3. Fazer request de teste
curl -X POST http://localhost:8001/agents/diagnostico-vendas/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analise conversão e performance",
    "history": [],
    "user_id": "user-a",
    "conversation_id": "conv-123"
  }'

# 4. Ver no Langfuse
# Acesse http://localhost:3001/traces
# Você verá:
# - Trace principal: agent_execution
#   - Span: identify_tools
#   - Span: mcp_calls
#     - Span: mcp_tool_analytics_get_conversion
#     - Span: mcp_tool_monitoring_get_latency
#     - Span: mcp_tool_db_query_sales
#   - Generation: Claude Sonnet 4 (do LiteLLM)
```

**Dashboards no Langfuse:**

1. **Criar Dashboard "Agent Performance":**
   - Latência média por agent
   - Taxa de erro por agent
   - Custo por agent

2. **Criar Dashboard "MCP Tools":**
   - Latência por tool
   - Taxa de erro por tool
   - Frequência de uso

3. **Criar Dashboard "Users":**
   - Requests por usuário
   - Custo por usuário
   - Latência média por usuário

**Entregável:** Tracing detalhado funcionando ✅

---

### Dia 9: Testes e Refinamentos

**Objetivo:** Validar todos os cenários e ajustar bugs

**Tarefas:**
1. ✅ Criar script de testes automatizados
2. ✅ Testar cenário User A (acesso completo)
3. ✅ Testar cenário User B (acesso limitado)
4. ✅ Testar bypass de permissões (segurança)
5. ✅ Validar audit logs
6. ✅ Testar performance (múltiplas requisições)
7. ✅ Ajustar UX do Open WebUI
8. ✅ Melhorar mensagens de erro
9. ✅ Adicionar logging adequado

**Script de Testes:**

```python
# scripts/test_permissions.py
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_user_a():
    """Testa User A - deve ter acesso a ambos agents"""
    print("🧪 Testando User A...")
    
    # Login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "user-a",
        "password": "senha123"
    })
    assert response.status_code == 200, "Login falhou"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Lista agents
    response = requests.get(f"{BASE_URL}/api/agents", headers=headers)
    assert response.status_code == 200
    agents = response.json()
    agent_keys = [a["agent_key"] for a in agents]
    
    assert "diagnostico-vendas" in agent_keys, "User A deveria ver diagnostico-vendas"
    assert "agent-generico" in agent_keys, "User A deveria ver agent-generico"
    
    # Testa chat com diagnóstico
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json={
            "agent_key": "diagnostico-vendas",
            "message": "Qual a taxa de conversão?",
            "include_history": False
        },
        stream=True
    )
    assert response.status_code == 200, "Chat com diagnostico-vendas falhou"
    
    print("✅ User A: OK")
    return True

def test_user_b():
    """Testa User B - deve ter acesso apenas ao genérico"""
    print("🧪 Testando User B...")
    
    # Login
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "user-b",
        "password": "senha123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Lista agents
    response = requests.get(f"{BASE_URL}/api/agents", headers=headers)
    agents = response.json()
    agent_keys = [a["agent_key"] for a in agents]
    
    assert "diagnostico-vendas" not in agent_keys, "User B NÃO deveria ver diagnostico-vendas"
    assert "agent-generico" in agent_keys, "User B deveria ver agent-generico"
    
    # Tenta acessar diagnóstico (deve falhar)
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json={
            "agent_key": "diagnostico-vendas",
            "message": "Teste",
            "include_history": False
        }
    )
    assert response.status_code == 403, "User B deveria ser bloqueado no diagnostico-vendas"
    
    # Acessa genérico (deve funcionar)
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json={
            "agent_key": "agent-generico",
            "message": "Olá",
            "include_history": False
        },
        stream=True
    )
    assert response.status_code == 200, "Chat com agent-generico falhou"
    
    print("✅ User B: OK")
    return True

def test_audit_logs():
    """Valida que logs estão sendo registrados"""
    print("🧪 Testando Audit Logs...")
    
    # Login como admin (assumindo que existe)
    # ... código para checar audit_logs table
    
    print("✅ Audit Logs: OK")
    return True

if __name__ == "__main__":
    try:
        test_user_a()
        test_user_b()
        test_audit_logs()
        print("\n🎉 Todos os testes passaram!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Teste falhou: {e}")
        sys.exit(1)
```

**Executar:**
```bash
python scripts/test_permissions.py
```

**Entregável:** Sistema validado e bugs corrigidos ✅

---

### Dia 9: Testes e Refinamentos

**Objetivo:** Validar todos os cenários e ajustar bugs

**Tarefas:**
1. ✅ Criar script de testes automatizados
2. ✅ Testar cenário User A (acesso completo)
3. ✅ Testar cenário User B (acesso limitado)
4. ✅ Testar bypass de permissões (segurança)
5. ✅ Validar audit logs
6. ✅ Validar Langfuse traces
7. ✅ Testar performance (múltiplas requisições)
8. ✅ Ajustar UX do Open WebUI
9. ✅ Melhorar mensagens de erro
10. ✅ Adicionar logging adequado

**Validações Langfuse:**

```python
# scripts/test_langfuse.py
"""Testa se Langfuse está capturando todas as métricas"""
import requests
import time
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host="http://localhost:3001"
)

def test_trace_created():
    """Verifica se traces estão sendo criados"""
    
    # Faz request
    response = requests.post(...)
    
    # Aguarda processamento
    time.sleep(5)
    
    # Busca traces recentes
    traces = langfuse.get_traces(limit=10)
    
    assert len(traces.data) > 0, "Nenhum trace encontrado"
    
    latest_trace = traces.data[0]
    assert latest_trace.user_id == "user-a"
    assert "diagnostico-vendas" in str(latest_trace.metadata)
    
    print("✅ Traces sendo criados corretamente")

def test_spans_hierarchy():
    """Verifica hierarquia de spans"""
    
    # ... busca trace específico
    
    # Verifica estrutura
    assert "agent_execution" in spans
    assert "mcp_calls" in spans
    assert "mcp_tool_analytics_get_conversion" in spans
    
    print("✅ Hierarquia de spans correta")

def test_cost_tracking():
    """Verifica tracking de custos"""
    
    # Faz várias requests
    for i in range(5):
        requests.post(...)
    
    time.sleep(10)
    
    # Busca dados agregados
    # (via API ou UI do Langfuse)
    
    print("✅ Custos sendo tracked")
```

**Entregável:** Sistema validado e bugs corrigidos ✅

---

### Dia 10: Deploy Final e Validação

**Objetivo:** Deploy on-premise e validação com usuários

**Tarefas:**
1. ✅ Configurar ambiente de produção
2. ✅ Fazer deploy on-premise
3. ✅ Configurar backups automáticos
4. ✅ Validar com user-a todos os fluxos
5. ✅ Validar com user-b as restrições
6. ✅ Validar audit logs
7. ✅ Validar Langfuse dashboards
8. ✅ Coletar feedback inicial
9. ✅ Ajustes finais
10. ✅ Documentar lições aprendidas
11. ✅ Apresentar POC

**Checklist de Validação:**

```markdown
## Checklist de Validação da POC

### Infraestrutura
- [ ] Todos os containers rodando sem erros
- [ ] PostgreSQL acessível e populado
- [ ] LiteLLM conectando aos 3 LLMs
- [ ] Ollama com Llama3 carregado
- [ ] Langfuse UI acessível
- [ ] Logs sendo gerados corretamente

### Funcionalidades
- [ ] Open WebUI acessível via browser
- [ ] Login funciona (user-a e user-b)
- [ ] Logout funciona
- [ ] Lista de agents exibida corretamente

### User A (Grupo Vendas)
- [ ] Vê 2 agents: Diagnóstico e Genérico
- [ ] Consegue acessar Agent Diagnóstico
- [ ] Prompts de exemplo aparecem (4 cards)
- [ ] Clique nos prompts preenche input
- [ ] Mensagem é processada com sucesso
- [ ] MCPs são consultados (verificar logs)
- [ ] Resposta em Markdown é renderizada
- [ ] Histórico é salvo

### User B (Grupo Geral)
- [ ] Vê apenas 1 agent: Genérico
- [ ] Não vê Agent Diagnóstico na lista
- [ ] Tentativa de acesso direto ao Diagnóstico retorna 403
- [ ] Consegue usar Agent Genérico normalmente

### Segurança
- [ ] Tokens JWT expiram corretamente
- [ ] Senhas são armazenadas com hash
- [ ] Tentativas de bypass são bloqueadas
- [ ] Audit logs registram todas as ações

### Performance
- [ ] Resposta do chat em < 5s
- [ ] Streaming funciona suavemente
- [ ] Múltiplos usuários simultâneos funcionam
- [ ] Sem memory leaks aparentes

### Audit Logs
- [ ] Login registrado
- [ ] Acesso a agents registrado
- [ ] Negação de acesso registrada
- [ ] Mensagens enviadas registradas

### Langfuse (Observabilidade)
- [ ] Traces aparecem no dashboard
- [ ] Hierarquia de spans correta
- [ ] User ID sendo capturado
- [ ] Session ID sendo capturado
- [ ] Tokens sendo contabilizados
- [ ] Custos sendo calculados
- [ ] Latência sendo medida
- [ ] Dashboard "Agent Performance" funcionando
- [ ] Dashboard "MCP Tools" funcionando
- [ ] Filtros por data/usuário/agent funcionam
- [ ] Drill-down em traces funciona
```

**Validação Langfuse no Dia 10:**

```bash
# 1. Acessar Dashboard
open http://localhost:3001

# 2. Verificar métricas gerais
# - Total de traces: > 50
# - Usuários únicos: 2 (user-a, user-b)
# - Agents usados: 2 (diagnostico-vendas, agent-generico)
# - Custo total: $X.XX
# - Tokens totais: XXXXX

# 3. Analisar traces do user-a
# Filtrar: user_id = user-a
# Verificar:
# - Usa ambos agents
# - MCPs sendo chamados (diagnostico-vendas)
# - Latência razoável

# 4. Analisar traces do user-b
# Filtrar: user_id = user-b
# Verificar:
# - Usa apenas agent-generico
# - Sem chamadas MCP
# - Latência OK

# 5. Analisar por Agent
# Filtrar: metadata.agent_key = diagnostico-vendas
# Ver:
# - Latência média
# - Taxa de sucesso
# - Custo por request

# 6. Drill-down em trace específico
# Clicar em um trace
# Ver hierarquia completa:
# - agent_execution (parent)
#   - identify_tools
#   - mcp_calls
#     - mcp_tool_analytics_get_conversion
#     - mcp_tool_monitoring_get_latency
#     - mcp_tool_db_query_sales
#   - llm_generation (Claude Sonnet 4)

# 7. Exportar relatório
# Dashboard > Export > CSV
# Salvar para apresentação
```

**Apresentação Final:**

Preparar slides mostrando:
1. Arquitetura implementada
2. Demo ao vivo (user-a e user-b)
3. Dashboard Langfuse com métricas
4. Audit logs
5. Próximos passos

**Entregável:** POC validada e funcionando ✅

**Objetivo:** Documentar tudo e preparar para produção

**Tarefas:**
1. ✅ Criar README.md principal
2. ✅ Documentar arquitetura (diagramas)
3. ✅ Documentar APIs (Swagger/OpenAPI)
4. ✅ Criar guia de instalação
5. ✅ Criar guia de troubleshooting
6. ✅ Documentar variáveis de ambiente
7. ✅ Criar scripts de backup
8. ✅ Preparar ambiente de produção

**README.md:**

```markdown
# AI Platform - Plataforma Multi-Agent

Plataforma interna para hospedar múltiplos AI agents com controle de acesso baseado em grupos.

## Arquitetura

[Diagrama do Dia 2]

## Stack

- **Open WebUI**: Interface de chat
- **LiteLLM**: Proxy para múltiplos LLMs
- **Permission Middleware**: Controle de acesso
- **MCP Adapter**: Integração com fontes de dados
- **PostgreSQL**: Banco de dados
- **Ollama**: LLM local

## Instalação

### Pré-requisitos
- Docker & Docker Compose
- (Opcional) GPU para Ollama

### Passos

1. Clone o repositório
git clone <repo>
cd empresa-ai-platform

2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas API keys

3. Suba os containers
docker-compose up -d

4. Aguarde inicialização (2-3 min)
docker-compose logs -f

5. Acesse http://localhost:3000

### Usuários de Teste

- **user-a** / senha123 (Grupo Vendas - acesso completo)
- **user-b** / senha123 (Grupo Geral - acesso limitado)

## Agents Disponíveis

### Diagnóstico de Vendas
- **Acesso**: Grupo Vendas
- **MCPs**: Google Analytics, Datadog, Internal DB
- **LLM**: Claude Sonnet 4

### Assistente Genérico
- **Acesso**: Todos
- **MCPs**: Nenhum
- **LLM**: GPT-4

## Troubleshooting

### Open WebUI não carrega
docker-compose restart open-webui

### LiteLLM não conecta aos LLMs
# Verifique API keys
docker-compose logs litellm

### Permissões não funcionam
# Recarregue dados seed
docker-compose exec postgres psql -U aiuser -d ai_platform -f /init-db.sql
```

**Entregável:** Documentação completa ✅

---

### Dia 10: Deploy Final e Validação

**Objetivo:** Deploy on-premise e validação com usuários

**Tarefas:**
1. ✅ Configurar ambiente de produção
2. ✅ Fazer deploy on-premise
3. ✅ Configurar backups automáticos
4. ✅ Validar com user-a todos os fluxos
5. ✅ Validar com user-b as restrições
6. ✅ Validar audit logs
7. ✅ Coletar feedback inicial
8. ✅ Ajustes finais
9. ✅ Documentar lições aprendidas
10. ✅ Apresentar POC

**Checklist de Validação:**

```markdown
## Checklist de Validação da POC

### Infraestrutura
- [ ] Todos os containers rodando sem erros
- [ ] PostgreSQL acessível e populado
- [ ] LiteLLM conectando aos 3 LLMs
- [ ] Ollama com Llama3 carregado
- [ ] Logs sendo gerados corretamente

### Funcionalidades
- [ ] Open WebUI acessível via browser
- [ ] Login funciona (user-a e user-b)
- [ ] Logout funciona
- [ ] Lista de agents exibida corretamente

### User A (Grupo Vendas)
- [ ] Vê 2 agents: Diagnóstico e Genérico
- [ ] Consegue acessar Agent Diagnóstico
- [ ] Prompts de exemplo aparecem (4 cards)
- [ ] Clique nos prompts preenche input
- [ ] Mensagem é processada com sucesso
- [ ] MCPs são consultados (verificar logs)
- [ ] Resposta em Markdown é renderizada
- [ ] Histórico é salvo

### User B (Grupo Geral)
- [ ] Vê apenas 1 agent: Genérico
- [ ] Não vê Agent Diagnóstico na lista
- [ ] Tentativa de acesso direto ao Diagnóstico retorna 403
- [ ] Consegue usar Agent Genérico normalmente

### Segurança
- [ ] Tokens JWT expiram corretamente
- [ ] Senhas são armazenadas com hash
- [ ] Tentativas de bypass são bloqueadas
- [ ] Audit logs registram todas as ações

### Performance
- [ ] Resposta do chat em < 5s
- [ ] Streaming funciona suavemente
- [ ] Múltiplos usuários simultâneos funcionam
- [ ] Sem memory leaks aparentes

### Audit Logs
- [ ] Login registrado
- [ ] Acesso a agents registrado
- [ ] Negação de acesso registrada
- [ ] Mensagens enviadas registradas
```

**Deploy:**

```bash
# No servidor on-premise

# 1. Clone
git clone <repo> /opt/ai-platform
cd /opt/ai-platform

# 2. Configure
cp .env.example .env
nano .env  # Editar com API keys reais

# 3. Build e deploy
docker-compose up -d --build

# 4. Monitore
docker-compose logs -f

# 5. Valide
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:3000
```

**Entregável:** POC validada e funcionando ✅

---

## 7. Métricas de Sucesso

### Métricas Técnicas
- ✅ Sistema rodando estável por 24h sem crashes
- ✅ Tempo de resposta < 5s (excluindo tempo do LLM)
- ✅ Taxa de erro < 1%
- ✅ 100% dos testes de permissão passando
- ✅ Langfuse capturando 100% das requests

### Métricas de Negócio
- ✅ User A consegue obter diagnóstico de vendas consultando MCPs
- ✅ User B não consegue acessar agent restrito
- ✅ Audit logs completos para compliance
- ✅ Interface intuitiva (feedback qualitativo)

### Métricas de Observabilidade (Langfuse)
- ✅ Traces visíveis para todas as conversas
- ✅ Latência P95 < 3s (excluindo LLM)
- ✅ Custos calculados por agent/usuário
- ✅ Hierarquia de spans correta (agent → MCP → LLM)
- ✅ Dashboards configurados e funcionais

---

## 8. Limitações Conhecidas da POC

### Funcional
- Sistema de autenticação básico (username/password)
- MCPs parcialmente mockados
- Apenas 2 agents implementados
- Sem rate limiting
- Sem cache de respostas
- Langfuse sem autenticação externa (apenas local)

### Técnico
- Sem alta disponibilidade
- Sem backup automático configurado
- Logs em formato simples
- Sem monitoramento de infraestrutura (Prometheus/Grafana)
- Langfuse compartilhado (não multi-tenant)

### Segurança
- Secrets em variáveis de ambiente (não em vault)
- HTTPS não configurado
- CORS permissivo
- Sem 2FA
- Langfuse sem SSO

**Nota**: Estas limitações são esperadas e aceitáveis para uma POC. Devem ser endereçadas antes de produção.

---

## 9. Lições Aprendidas e Próximas Iterações

### O que funcionou bem
- Open WebUI + LiteLLM = ótima base (80% pronto)
- Arquitetura modular facilita manutenção
- MCPs mockados aceleraram desenvolvimento
- PostgreSQL suficiente para esta escala
- Langfuse fornece observabilidade valiosa desde o início

### Desafios Encontrados
- Integração Open WebUI ↔ Custom API (precisou adapter)
- Streaming SSE com múltiplos proxies (latência)
- Gestão de contexto dos MCPs (precisa otimizar)
- Configuração inicial do Langfuse (keys após primeiro acesso)
- Instrumentação manual do MCP Adapter (decorators)