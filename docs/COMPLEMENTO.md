# Guia de Implementação - Plataforma Multi-Agent com Open WebUI

## 1. Visão Geral da Arquitetura

### 1.1 Objetivo
Implementar uma plataforma de AI agents customizados usando Open WebUI como interface, com agents configurados em banco de dados PostgreSQL, controle de acesso granular por grupos, e integração com MCPs (Model Context Protocol).

### 1.2 Stack Tecnológico

**Componentes:**
- **Open WebUI**: Interface de chat (frontend)
- **LiteLLM**: Proxy para múltiplos LLMs (OpenAI, Anthropic, Ollama)
- **PostgreSQL**: Banco de dados (agents, permissões, histórico)
- **MCP Adapter**: Service FastAPI que orquestra agents e MCPs
- **MCP Server**: Servidor com tools mockadas (analytics, monitoring, database)
- **Langfuse**: Observabilidade e analytics

### 1.3 Fluxo Completo

```
┌─────────────────────────────────────────────────────────┐
│ 1. User faz login no Open WebUI                        │
│    - emingues@gmail.com (Grupo Vendas)                  │
│    - geral@company.com (Grupo Geral)                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Open WebUI Function lista agents disponíveis        │
│    GET http://mcp-adapter:8001/agents?user_email=...    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. MCP Adapter consulta PostgreSQL                     │
│    - Busca usuário por email                            │
│    - Busca grupos do usuário                            │
│    - Busca permissões (group_agent_permissions)         │
│    - Busca agents permitidos                            │
│    - Busca prompts de exemplo (agent_prompts)           │
│    - Retorna lista de agents com prompts                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Open WebUI mostra agents como cards                 │
│                                                         │
│    emingues@gmail.com vê:                              │
│    ┌──────────────────────┐ ┌───────────────────────┐ │
│    │ 📊 Agent Diagnóstico │ │ 🤖 Assistente Genérico│ │
│    │    de Vendas         │ │                       │ │
│    │ [4 prompts exemplo]  │ │ [4 prompts exemplo]   │ │
│    └──────────────────────┘ └───────────────────────┘ │
│                                                         │
│    geral@company.com vê:                               │
│    ┌───────────────────────┐                           │
│    │ 🤖 Assistente Genérico│                           │
│    │ [4 prompts exemplo]   │                           │
│    └───────────────────────┘                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. User clica em prompt exemplo ou digita mensagem     │
│    "Qual foi a taxa de conversão nos últimos 30 dias?" │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 6. Open WebUI Function envia para MCP Adapter          │
│    POST /agents/diagnostico-vendas/chat                 │
│    {                                                    │
│      "user_email": "emingues@gmail.com",               │
│      "message": "Qual foi a taxa...",                  │
│      "history": []                                     │
│    }                                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 7. MCP Adapter processa                                │
│    a) Valida permissão (consulta banco)                │
│    b) Identifica MCPs necessários (analytics, db)      │
│    c) Chama MCP Server tools:                          │
│       - analytics_get_conversion                       │
│       - db_query_sales                                 │
│    d) Recebe dados estruturados                        │
│    e) Enriquece contexto da mensagem                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 8. MCP Adapter chama LiteLLM                           │
│    POST http://litellm:4000/v1/chat/completions        │
│    {                                                    │
│      "model": "claude-sonnet-4-20250514",              │
│      "messages": [                                     │
│        {"role": "system", "content": "[system prompt]"},│
│        {"role": "user", "content": "[msg + dados MCP]"}│
│      ],                                                │
│      "stream": true                                    │
│    }                                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 9. LiteLLM roteia para Anthropic/OpenAI/Ollama        │
│    + Envia telemetria para Langfuse                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 10. Resposta streaming volta para user                │
│     MCP Adapter → Open WebUI → Browser                │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Estrutura do Banco de Dados

### 2.1 Schema Completo

O banco PostgreSQL armazena toda a configuração de agents, permissões e histórico.

**Tabelas principais:**

```sql
-- Usuários
users (
  id, username, email, password_hash, is_active, 
  created_at, updated_at
)

-- Grupos de acesso
groups (
  id, name, description, created_at
)

-- Relação N:N usuário-grupo
user_groups (
  user_id, group_id, assigned_at
)

-- AGENTS - Configuração dos agents customizados
agents (
  id, 
  agent_key VARCHAR(100),          -- Ex: "diagnostico-vendas"
  name VARCHAR(200),                -- Ex: "Agent Diagnóstico de Vendas"
  description TEXT,                 -- Descrição do que o agent faz
  llm_provider VARCHAR(50),         -- 'openai', 'anthropic', 'ollama'
  llm_model VARCHAR(100),           -- 'claude-sonnet-4', 'gpt-4'
  system_prompt TEXT,               -- Prompt customizado do agent
  is_active BOOLEAN,
  created_at, updated_at
)

-- PROMPTS DE EXEMPLO - Cards clicáveis na UI
agent_prompts (
  id,
  agent_id,
  prompt_text TEXT,                 -- Ex: "Qual foi a taxa de conversão?"
  description VARCHAR(255),         -- Ex: "Análise de conversão"
  display_order INTEGER,            -- Ordem dos cards (1, 2, 3, 4)
  created_at
)

-- Configurações MCP
mcp_configs (
  id, name, type, endpoint, 
  credentials_encrypted, is_active, created_at
)

-- Relação N:N agent-MCP (quais MCPs cada agent usa)
agent_mcps (
  agent_id, mcp_id, config JSONB
)

-- PERMISSÕES - Quais grupos podem acessar quais agents
group_agent_permissions (
  group_id, agent_id, can_access BOOLEAN, granted_at
)

-- Histórico de conversas
conversations (
  id, user_id, agent_id, title, created_at, updated_at
)

-- Mensagens
messages (
  id, conversation_id, role, content, mcp_data JSONB, created_at
)

-- Audit logs
audit_logs (
  id, user_id, agent_id, action, details JSONB, 
  ip_address, user_agent, created_at
)

-- Dados mock de vendas (para MCP consultar)
sales_data (
  id, date, product_id, product_name, category, 
  quantity, unit_price, total_amount, 
  customer_id, source, created_at
)
```

### 2.2 Dados de Exemplo (Seed)

**Grupos:**
- `grupo-vendas`: Acessa agents de vendas e análises
- `grupo-geral`: Acessa apenas agents genéricos

**Usuários:**
- `emingues@gmail.com` → Grupo Vendas (senha: senha123)
- `geral@company.com` → Grupo Geral (senha: senha123)

**Agents:**

1. **diagnostico-vendas**
   - Nome: "Agent Diagnóstico de Vendas"
   - LLM: Claude Sonnet 4
   - MCPs: analytics-mock, monitoring-mock, internal-db
   - 4 prompts de exemplo
   - Permissão: apenas grupo-vendas

2. **agent-generico**
   - Nome: "Assistente Genérico"
   - LLM: GPT-4
   - MCPs: nenhum
   - 4 prompts de exemplo
   - Permissão: todos os grupos

**Arquivo SQL completo:** `init-db.sql` (fornecido separadamente)

---

## 3. Componente 1: MCP Adapter

### 3.1 Responsabilidades

O MCP Adapter é o **coração da plataforma**. Ele:

1. **Consulta o banco** para buscar agents, permissões, MCPs
2. **Valida acesso** do usuário ao agent solicitado
3. **Identifica MCPs necessários** baseado na mensagem
4. **Chama MCP Server** para obter dados (analytics, monitoring, etc)
5. **Enriquece contexto** da mensagem com dados dos MCPs
6. **Chama LiteLLM** com o contexto completo
7. **Retorna streaming** da resposta para o Open WebUI

### 3.2 Estrutura de Arquivos

```
mcp-adapter/
├── Dockerfile
├── requirements.txt
├── main.py                    # FastAPI app principal
├── database.py                # Conexão PostgreSQL
├── models.py                  # SQLAlchemy models
├── schemas.py                 # Pydantic schemas
├── config.py                  # Configurações
├── mcp_client.py             # Cliente MCP (conecta ao MCP Server)
└── utils/
    ├── mcp_utils.py          # Utilitários para decisão de MCPs
    └── format_utils.py       # Formatação de resultados MCP
```

### 3.3 Endpoints Principais

#### GET /agents

Lista agents que o usuário pode acessar.

```python
@app.get("/agents")
async def list_agents(
    user_email: str,
    db: Session = Depends(get_db)
):
    """
    Retorna agents que o usuário pode acessar
    consultando banco de dados
    """
    
    # 1. Busca usuário por email
    user = db.query(models.User).filter_by(email=user_email).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # 2. Busca grupos do usuário
    user_groups = db.query(models.UserGroup).filter_by(
        user_id=user.id
    ).all()
    group_ids = [ug.group_id for ug in user_groups]
    
    # 3. Busca permissões dos grupos
    permissions = db.query(models.GroupAgentPermission).filter(
        models.GroupAgentPermission.group_id.in_(group_ids),
        models.GroupAgentPermission.can_access == True
    ).all()
    agent_ids = [p.agent_id for p in permissions]
    
    # 4. Busca agents
    agents = db.query(models.Agent).filter(
        models.Agent.id.in_(agent_ids),
        models.Agent.is_active == True
    ).all()
    
    # 5. Para cada agent, busca prompts de exemplo
    result = []
    for agent in agents:
        prompts = db.query(models.AgentPrompt).filter_by(
            agent_id=agent.id
        ).order_by(models.AgentPrompt.display_order).all()
        
        result.append({
            "id": agent.agent_key,
            "name": agent.name,
            "description": agent.description,
            "llm_provider": agent.llm_provider,
            "llm_model": agent.llm_model,
            "prompts": [
                {
                    "title": p.description,
                    "content": p.prompt_text
                }
                for p in prompts
            ]
        })
    
    return result
```

**Exemplo de resposta:**

```json
[
  {
    "id": "diagnostico-vendas",
    "name": "Agent Diagnóstico de Vendas",
    "description": "Analisa performance de vendas consultando analytics...",
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4-20250514",
    "prompts": [
      {
        "title": "Análise de conversão",
        "content": "Qual foi a taxa de conversão nos últimos 30 dias?"
      },
      {
        "title": "Comparação mensal",
        "content": "Compare a performance de vendas deste mês com o anterior"
      },
      {
        "title": "Análise de funil",
        "content": "Identifique os principais gargalos no funil de vendas"
      },
      {
        "title": "Performance técnica",
        "content": "Mostre as APIs com maior latência afetando vendas"
      }
    ]
  },
  {
    "id": "agent-generico",
    "name": "Assistente Genérico",
    "description": "Assistente de propósito geral...",
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "prompts": [...]
  }
]
```

#### POST /agents/{agent_key}/chat

Processa chat com agent específico.

```python
@app.post("/agents/{agent_key}/chat")
async def chat(
    agent_key: str,
    request: ChatRequest,  # {user_email, message, history}
    db: Session = Depends(get_db)
):
    """
    Processa chat com agent
    """
    
    # 1. Busca agent no banco
    agent = db.query(models.Agent).filter_by(
        agent_key=agent_key,
        is_active=True
    ).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    # 2. Valida permissão
    user = db.query(models.User).filter_by(
        email=request.user_email
    ).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    has_access = db.query(models.GroupAgentPermission).join(
        models.UserGroup
    ).filter(
        models.UserGroup.user_id == user.id,
        models.GroupAgentPermission.agent_id == agent.id,
        models.GroupAgentPermission.can_access == True
    ).first()
    
    if not has_access:
        # Registra tentativa de acesso negado
        audit_log = models.AuditLog(
            user_id=user.id,
            agent_id=agent.id,
            action='access_denied',
            details={'message': request.message[:100]}
        )
        db.add(audit_log)
        db.commit()
        
        raise HTTPException(403, "Access denied to this agent")
    
    # 3. Registra acesso permitido
    audit_log = models.AuditLog(
        user_id=user.id,
        agent_id=agent.id,
        action='chat_started',
        details={'message_preview': request.message[:100]}
    )
    db.add(audit_log)
    db.commit()
    
    # 4. Busca MCPs configurados para este agent
    agent_mcps = db.query(models.AgentMcp).filter_by(
        agent_id=agent.id
    ).all()
    
    mcp_configs = [
        db.query(models.McpConfig).filter_by(id=am.mcp_id).first()
        for am in agent_mcps
    ]
    
    # 5. Identifica quais MCPs chamar baseado na mensagem
    mcps_to_call = identify_needed_mcps(
        message=request.message,
        available_mcps=mcp_configs
    )
    
    # 6. Chama MCPs
    mcp_client = MCPClient()
    mcp_results = {}
    
    for mcp_config in mcps_to_call:
        tool_name = get_tool_for_mcp(mcp_config.type, request.message)
        tool_args = get_args_for_tool(request.message)
        
        try:
            result = await mcp_client.call_tool(
                mcp_name=mcp_config.name,
                tool_name=tool_name,
                args=tool_args
            )
            mcp_results[mcp_config.name] = result
        except Exception as e:
            logger.error(f"Error calling MCP {mcp_config.name}: {e}")
            mcp_results[mcp_config.name] = {"error": str(e)}
    
    # 7. Formata contexto enriquecido
    context = format_mcp_results(mcp_results)
    
    # 8. Monta mensagem enriquecida
    enriched_message = f"""{request.message}

---
DADOS DISPONÍVEIS PARA ANÁLISE:

{context}
---

Por favor, analise estes dados e forneça insights acionáveis.
"""
    
    # 9. Chama LiteLLM com streaming
    async def generate():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "http://litellm:4000/v1/chat/completions",
                headers={
                    "Authorization": "Bearer sk-1234",
                    "Content-Type": "application/json"
                },
                json={
                    "model": agent.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": agent.system_prompt
                        }
                    ] + request.history + [
                        {
                            "role": "user",
                            "content": enriched_message
                        }
                    ],
                    "stream": True
                },
                timeout=120.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        yield line + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


def identify_needed_mcps(message: str, available_mcps: list) -> list:
    """Identifica quais MCPs chamar baseado na mensagem"""
    
    keywords = {
        "analytics": ["conversão", "tráfego", "visitas", "sessions", "funil"],
        "monitoring": ["latência", "erro", "performance", "api", "timeout"],
        "database": ["vendas", "receita", "produto", "cliente", "ticket"]
    }
    
    message_lower = message.lower()
    needed_mcps = []
    
    for mcp in available_mcps:
        mcp_keywords = keywords.get(mcp.type, [])
        if any(kw in message_lower for kw in mcp_keywords):
            needed_mcps.append(mcp)
    
    # Se nenhum keyword, usa conjunto padrão
    if not needed_mcps and available_mcps:
        # Para agent de vendas, usa analytics + database por padrão
        needed_mcps = [
            mcp for mcp in available_mcps 
            if mcp.type in ["analytics", "database"]
        ]
    
    return needed_mcps


def get_tool_for_mcp(mcp_type: str, message: str) -> str:
    """Retorna nome da tool a chamar no MCP Server"""
    
    message_lower = message.lower()
    
    if mcp_type == "analytics":
        if "conversão" in message_lower or "conversion" in message_lower:
            return "analytics_get_conversion"
        else:
            return "analytics_get_traffic"
    
    elif mcp_type == "monitoring":
        if "latência" in message_lower or "latency" in message_lower:
            return "monitoring_get_latency"
        else:
            return "monitoring_get_errors"
    
    else:  # database
        return "db_query_sales"


def format_mcp_results(results: dict) -> str:
    """Formata resultados MCP para incluir no contexto do LLM"""
    
    formatted = []
    
    for mcp_name, data in results.items():
        if "error" in data:
            continue  # Pula erros
        
        formatted.append(f"### {mcp_name}")
        formatted.append(format_single_mcp(mcp_name, data))
    
    return "\n\n".join(formatted) if formatted else "Nenhum dado disponível."


def format_single_mcp(mcp_name: str, data: dict) -> str:
    """Formata um resultado MCP específico"""
    
    if "analytics" in mcp_name:
        if "conversion_rate" in data:
            cr = data["conversion_rate"]
            comp = data["comparison"]
            
            result = f"""
**Taxa de Conversão**: {cr['formatted']}
**Variação**: {comp['direction']} {comp['change_percent']}% vs período anterior

**Por Fonte**:
"""
            for item in data.get("breakdown_by_source", []):
                result += f"- {item['source']}: {item['rate']*100:.2f}% ({item['sessions']} sessões)\n"
            
            return result
    
    elif "monitoring" in mcp_name:
        if "average_latency" in data:
            latency = data["average_latency"]
            
            result = f"""
**Latência Média**: P50={latency['p50']}ms, P95={latency['p95']}ms, P99={latency['p99']}ms

**Por Endpoint**:
"""
            for ep in data.get("endpoints", []):
                alert = f" ⚠️ {ep['alert']}" if ep.get('alert') else ""
                result += f"- {ep['endpoint']}: P95={ep['p95']}ms{alert}\n"
            
            return result
    
    elif "database" in mcp_name or "internal-db" in mcp_name:
        if "results" in data:
            result = f"**Agrupado por**: {data.get('group_by', 'N/A')}\n\n"
            
            for row in data["results"][:5]:  # Top 5
                result += f"- {list(row.values())[0]}: "
                result += f"{row.get('total_sales', 0)} vendas, "
                result += f"R$ {row.get('revenue', 0):,.2f}\n"
            
            return result
    
    # Fallback: JSON formatado
    return f"```json\n{json.dumps(data, indent=2)}\n```"
```

### 3.4 MCP Client

```python
# mcp-adapter/mcp_client.py
"""Cliente para conectar ao MCP Server via stdio"""

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """Cliente MCP que conecta ao MCP Server"""
    
    def __init__(self, server_command: str = None):
        self.server_command = server_command or (
            "docker exec -i ai-platform-mcp-server python /app/main.py"
        )
        self.session = None
    
    async def connect(self):
        """Estabelece conexão com MCP Server"""
        
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "ai-platform-mcp-server", "python", "/app/main.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.session = session
                
                # Lista tools disponíveis
                tools = await session.list_tools()
                logger.info(f"Connected to MCP Server. Available tools: {[t.name for t in tools.tools]}")
                
                return self
    
    async def call_tool(self, mcp_name: str, tool_name: str, args: dict) -> dict:
        """
        Chama uma tool no MCP Server
        
        Args:
            mcp_name: Nome do MCP (não usado aqui, mas útil para logging)
            tool_name: Nome da tool (ex: "analytics_get_conversion")
            args: Argumentos da tool (ex: {"period": "30d"})
        
        Returns:
            dict: Resultado da tool
        """
        
        if not self.session:
            await self.connect()
        
        logger.info(f"Calling MCP tool: {tool_name} with args: {args}")
        
        try:
            result = await self.session.call_tool(tool_name, args)
            
            # Parse resultado (MCP retorna TextContent)
            if result.content and len(result.content) > 0:
                text_content = result.content[0].text
                
                # Converte string para dict
                import ast
                return ast.literal_eval(text_content)
            
            return {}
        
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def disconnect(self):
        """Fecha conexão"""
        if self.session:
            await self.session.close()
            self.session = None
```

---

## 4. Componente 2: Open WebUI Function

### 4.1 Responsabilidade

A Open WebUI Function é um **thin client** que:

1. Consulta MCP Adapter para listar agents disponíveis
2. Exibe agents como opções no Open WebUI
3. Exibe prompts de exemplo como cards clicáveis
4. Encaminha mensagens do usuário para o MCP Adapter
5. Faz streaming da resposta de volta para a UI

**Importante:** A Function **NÃO** tem lógica de negócio. Toda lógica está no MCP Adapter.

### 4.2 Código Completo

```python
# open-webui-functions/dynamic_agents.py
"""
title: AI Platform Agents (Database-backed)
description: Carrega agents dinamicamente do banco de dados via MCP Adapter
author: Empresa
version: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable, List, Dict
import requests
import logging

logger = logging.getLogger(__name__)


class Pipe:
    """
    Open WebUI Function que integra com MCP Adapter
    para listar agents do banco de dados
    """
    
    class Valves(BaseModel):
        """Configurações da function"""
        
        mcp_adapter_url: str = Field(
            default="http://mcp-adapter:8001",
            description="URL do MCP Adapter service"
        )
        
        request_timeout: int = Field(
            default=60,
            description="Timeout para requests (segundos)"
        )
        
        enabled: bool = Field(
            default=True,
            description="Habilitar esta function"
        )
    
    def __init__(self):
        self.type = "manifold"  # Permite múltiplos "modelos" (agents)
        self.id = "ai-platform-agents"
        self.name = "AI Platform Agents"
        self.valves = self.Valves()
    
    def _get_user_email(self, __user__: dict) -> str:
        """Extrai email do usuário autenticado"""
        return __user__.get("email", "unknown@empresa.com")
    
    def _fetch_agents(self, user_email: str) -> List[Dict]:
        """
        Busca agents do MCP Adapter
        (que por sua vez consulta o banco de dados)
        """
        try:
            response = requests.get(
                f"{self.valves.mcp_adapter_url}/agents",
                params={"user_email": user_email},
                timeout=self.valves.request_timeout
            )
            
            if response.status_code == 200:
                agents = response.json()
                logger.info(f"Fetched {len(agents)} agents for {user_email}")
                return agents
            else:
                logger.error(f"Error fetching agents: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Exception fetching agents: {e}")
            return []
    
    def get_models(self, __user__: dict = None) -> List[Dict]:
        """
        Retorna lista de agents (como "models") que o usuário pode acessar
        
        Open WebUI chama este método para popular o dropdown de modelos.
        Retornamos agents do banco de dados.
        """
        
        if not __user__:
            logger.warning("No user provided to get_models")
            return []
        
        if not self.valves.enabled:
            return []
        
        user_email = self._get_user_email(__user__)
        agents = self._fetch_agents(user_email)
        
        # Converte formato do banco para formato Open WebUI
        models = []
        for agent in agents:
            models.append({
                "id": agent["id"],  # agent_key
                "name": agent["name"]  # nome exibido
            })
        
        return models
    
    def get_suggested_prompts(
        self,
        __user__: dict = None,
        model_id: str = None
    ) -> List[Dict]:
        """
        Retorna prompts de exemplo para um agent específico
        
        Open WebUI chama este método quando o usuário seleciona um agent.
        Retornamos os prompts cadastrados no banco.
        """
        
        if not __user__ or not model_id:
            return []
        
        user_email = self._get_user_email(__user__)
        agents = self._fetch_agents(user_email)
        
        # Busca agent específico
        agent = next((a for a in agents if a["id"] == model_id), None)
        
        if not agent:
            logger.warning(f"Agent {model_id} not found for {user_email}")
            return []
        
        # Retorna prompts do agent
        prompts = agent.get("prompts", [])
        
        logger.info(f"Returning {len(prompts)} prompts for agent {model_id}")
        
        return [
            {
                "title": prompt["title"],
                "content": prompt["content"]
            }
            for prompt in prompts
        ]
    
    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__: Callable[[dict], Awaitable[None]]
    ) -> dict:
        """
        Processa mensagem do usuário
        
        Open WebUI chama este método quando o usuário envia uma mensagem.
        Encaminhamos para o MCP Adapter e fazemos streaming da resposta.
        """
        
        # Extrai informações
        user_email = self._get_user_email(__user__)
        model_id = body.get("model")  # agent_key
        messages = body.get("messages", [])
        
        if not messages:
            await __event_emitter__({
                "type": "message",
                "data": {"content": "Erro: Nenhuma mensagem fornecida"}
            })
            return {"status": "error"}
        
        user_message = messages[-1]["content"]
        history = messages[:-1]
        
        logger.info(f"Processing chat: user={user_email}, agent={model_id}")
        
        # Chama MCP Adapter
        try:
            response = requests.post(
                f"{self.valves.mcp_adapter_url}/agents/{model_id}/chat",
                json={
                    "user_email": user_email,
                    "message": user_message,
                    "history": history
                },
                stream=True,
                timeout=self.valves.request_timeout
            )
            
            if response.status_code == 403:
                await __event_emitter__({
                    "type": "message",
                    "data": {"content": "❌ Você não tem permissão para acessar este agent."}
                })
                return {"status": "error"}
            
            elif response.status_code != 200:
                await __event_emitter__({
                    "type": "message",
                    "data": {"content": f"❌ Erro ao processar: {response.status_code}"}
                })
                return {"status": "error"}
            
            # Stream da resposta
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    # MCP Adapter retorna no formato SSE: "data: <content>"
                    if line_str.startswith("data: "):
                        content = line_str[6:]  # Remove "data: "
                        
                        if content == "[DONE]":
                            break
                        
                        # Emite chunk para Open WebUI
                        await __event_emitter__({
                            "type": "message",
                            "data": {"content": content}
                        })
            
            logger.info(f"Chat completed for user={user_email}, agent={model_id}")
            return {"status": "completed"}
        
        except requests.exceptions.Timeout:
            await __event_emitter__({
                "type": "message",
                "data": {"content": "❌ Timeout ao processar requisição"}
            })
            return {"status": "error"}
        
        except Exception as e:
            logger.error(f"Error in pipe: {e}")
            await __event_emitter__({
                "type": "message",
                "data": {"content": f"❌ Erro: {str(e)}"}
            })
            return {"status": "error"}
```

### 4.3 Como Instalar

**Via UI (recomendado):**

1. Acesse Open WebUI: `http://localhost:3000`
2. Faça login como admin
3. Vá em: **Workspace** → **Functions** → **+ Create New Function**
4. Cole o código acima
5. Clique em **Save**

**Via arquivo:**

```bash
# Copiar para container
docker cp dynamic_agents.py open-webui:/app/backend/functions/

# Reiniciar Open WebUI
docker restart open-webui
```

---

## 5. Componente 3: MCP Server

### 5.1 Responsabilidade

O MCP Server implementa **tools** que retornam dados estruturados:

- `analytics_get_conversion`: Simula Google Analytics (dados mock)
- `analytics_get_traffic`: Simula Google Analytics (dados mock)
- `monitoring_get_latency`: Simula Datadog (dados mock)
- `monitoring_get_errors`: Simula Datadog (dados mock)
- `db_query_sales`: Consulta real ao PostgreSQL

### 5.2 Código Resumido

```python
# mcp-server/main.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tools import analytics, monitoring, database

app = Server("internal-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="analytics_get_conversion",
            description="Get conversion rate metrics (simulates Google Analytics)",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "default": "30d"}
                }
            }
        ),
        Tool(
            name="monitoring_get_latency",
            description="Get API latency metrics (simulates Datadog)",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "default": "7d"}
                }
            }
        ),
        Tool(
            name="db_query_sales",
            description="Query sales data from internal database",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "default": "30d"},
                    "group_by": {"type": "string", "enum": ["source", "category"]}
                }
            }
        )
        # ... outras tools
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "analytics_get_conversion":
        result = await analytics.get_conversion_data(arguments)
    elif name == "monitoring_get_latency":
        result = await monitoring.get_latency_data(arguments)
    elif name == "db_query_sales":
        result = await database.query_sales(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    return [TextContent(type="text", text=str(result))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**Nota:** O MCP Server já está implementado conforme PRD original. Não requer modificações.

---

## 6. Checklist de Implementação

### Fase 1: Banco de Dados (0.5 dia)

- [ ] Executar `init-db.sql` no PostgreSQL
  ```bash
  docker exec -i ai-platform-postgres psql -U aiuser -d ai_platform < init-db.sql
  ```
- [ ] Validar criação das tabelas
  ```sql
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public';
  ```
- [ ] Validar dados seed
  ```sql
  SELECT agent_key, name FROM agents;
  SELECT COUNT(*) FROM agent_prompts;
  SELECT COUNT(*) FROM sales_data;
  ```

### Fase 2: MCP Adapter (2 dias)

- [ ] Criar estrutura de diretórios
- [ ] Configurar Dockerfile e requirements.txt
- [ ] Implementar `database.py` (conexão PostgreSQL)
- [ ] Implementar `models.py` (SQLAlchemy models)
- [ ] Implementar endpoint `GET /agents`
- [ ] Implementar endpoint `POST /agents/{agent_key}/chat`
- [ ] Implementar `mcp_client.py` (cliente MCP)
- [ ] Implementar funções auxiliares:
  - `identify_needed_mcps()`
  - `get_tool_for_mcp()`
  - `format_mcp_results()`
- [ ] Adicionar ao docker-compose.yml
- [ ] Build e start do container
  ```bash
  docker-compose up -d mcp-adapter
  ```
- [ ] Testar endpoints isoladamente
  ```bash
  # Testar listagem de agents
  curl "http://localhost:8001/agents?user_email=emingues@gmail.com"
  
  # Testar chat
  curl -X POST http://localhost:8001/agents/diagnostico-vendas/chat \
    -H "Content-Type: application/json" \
    -d '{"user_email":"emingues@gmail.com","message":"teste","history":[]}'
  ```

### Fase 3: Open WebUI Function (1 dia)

- [ ] Acessar Open WebUI admin panel
- [ ] Criar nova Function
- [ ] Copiar código de `dynamic_agents.py`
- [ ] Configurar Valves (URL do MCP Adapter)
- [ ] Salvar Function
- [ ] Testar função `get_models()`:
  - Login como `emingues@gmail.com`
  - Verificar se vê 2 agents
- [ ] Testar função `get_suggested_prompts()`:
  - Selecionar agent
  - Verificar se aparecem 4 cards
- [ ] Testar função `pipe()`:
  - Clicar em prompt de exemplo
  - Enviar mensagem
  - Verificar streaming de resposta

### Fase 4: Testes de Integração (1 dia)

#### Teste 1: User A (Grupo Vendas)
- [ ] Login: `emingues@gmail.com` / `senha123`
- [ ] Verificar agents visíveis: deve ver 2
  - Agent Diagnóstico de Vendas
  - Assistente Genérico
- [ ] Selecionar "Agent Diagnóstico de Vendas"
- [ ] Verificar cards de exemplo: deve ver 4
- [ ] Clicar no card "Taxa de conversão"
- [ ] Verificar que prompt preenche input
- [ ] Enviar mensagem
- [ ] Verificar resposta:
  - Contém dados de analytics
  - Contém dados de database
  - Formatação em Markdown
  - Insights acionáveis
- [ ] Verificar logs MCP Adapter:
  ```bash
  docker logs ai-platform-mcp-adapter
  # Deve mostrar: analytics_get_conversion, db_query_sales
  ```
- [ ] Verificar Langfuse:
  - Acesse `http://localhost:3001`
  - Verificar novo trace
  - Verificar spans (MCP calls)

#### Teste 2: User B (Grupo Geral)
- [ ] Login: `geral@company.com` / `senha123`
- [ ] Verificar agents visíveis: deve ver apenas 1
  - Assistente Genérico
- [ ] NÃO deve ver "Agent Diagnóstico de Vendas"
- [ ] Tentar acessar diretamente (força URL/API):
  ```bash
  # Via API (deve retornar 403)
  curl -X POST http://localhost:8001/agents/diagnostico-vendas/chat \
    -H "Content-Type: application/json" \
    -d '{"user_email":"geral@company.com","message":"teste","history":[]}'
  ```
- [ ] Selecionar "Assistente Genérico"
- [ ] Enviar mensagem
- [ ] Verificar resposta funciona
- [ ] Verificar logs: NÃO deve chamar MCPs

#### Teste 3: Audit Logs
- [ ] Consultar audit_logs no banco:
  ```sql
  SELECT 
    u.email,
    a.name as agent_name,
    al.action,
    al.created_at
  FROM audit_logs al
  JOIN users u ON u.id = al.user_id
  LEFT JOIN agents a ON a.id = al.agent_id
  ORDER BY al.created_at DESC
  LIMIT 20;
  ```
- [ ] Verificar registros de:
  - `chat_started` (User A com diagnóstico)
  - `access_denied` (User B tentando diagnóstico)

#### Teste 4: Performance
- [ ] Medir tempo de resposta:
  - Primeira mensagem: < 5s
  - Mensagens subsequentes: < 3s
- [ ] Teste de carga (opcional):
  ```bash
  # 10 requests simultâneas
  ab -n 10 -c 10 -p payload.json -T application/json \
    http://localhost:8001/agents/diagnostico-vendas/chat
  ```

### Fase 5: Validação Final (0.5 dia)

- [ ] Revisar todos os critérios de sucesso da POC
- [ ] Documentar problemas encontrados
- [ ] Coletar feedback dos usuários de teste
- [ ] Preparar demonstração
- [ ] Exportar métricas do Langfuse

---

## 7. Docker Compose

Adicionar ao `docker-compose.yml` existente:

```yaml
services:
  # ... (postgres, litellm, langfuse, etc já existentes)
  
  # MCP Adapter (NOVO)
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
      - MCP_SERVER_COMMAND=docker exec -i ai-platform-mcp-server python /app/main.py
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - LANGFUSE_HOST=http://langfuse:3000
    volumes:
      - ./mcp-adapter:/app
      - /var/run/docker.sock:/var/run/docker.sock
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
```

---

## 8. Resultado Final Esperado

### 8.1 Para emingues@gmail.com (Grupo Vendas)

**Ao fazer login:**

```
┌──────────────────────────────────────────────┐
│  Agents Disponíveis:                         │
│                                              │
│  📊 Agent Diagnóstico de Vendas             │
│  🤖 Assistente Genérico                      │
└──────────────────────────────────────────────┘
```

**Ao selecionar "Agent Diagnóstico de Vendas":**

```
┌──────────────────────────────────────────────┐
│  📊 Agent Diagnóstico de Vendas             │
│  Analisa performance de vendas consultando  │
│  dados de analytics, monitoring e vendas    │
├──────────────────────────────────────────────┤
│  Exemplos:                                   │
│  ┌─────────────────┐  ┌─────────────────┐  │
│  │ 📊 Análise de   │  │ 📈 Comparação   │  │
│  │ conversão       │  │ mensal          │  │
│  │                 │  │                 │  │
│  │ Qual foi a taxa │  │ Compare a       │  │
│  │ de conversão... │  │ performance...  │  │
│  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  │
│  │ 🔍 Análise de   │  │ ⚡ Performance  │  │
│  │ funil           │  │ técnica         │  │
│  │                 │  │                 │  │
│  │ Identifique os  │  │ Mostre as APIs  │  │
│  │ gargalos...     │  │ com latência... │  │
│  └─────────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────┘
```

**Ao enviar mensagem "Qual foi a taxa de conversão?":**

```
Resposta:

## 📊 Análise de Conversão (Últimos 30 dias)

### Resumo Executivo
A taxa de conversão atual está em **3.42%**, representando um 
aumento de **14.77%** em relação ao período anterior. Este é 
um resultado positivo que indica melhor efetividade do funil.

### 🎯 Principais Descobertas

**Por Fonte de Tráfego:**
- **Tráfego Orgânico**: 4.21% (12,450 sessões, 524 conversões)
  - Melhor performance entre todas as fontes
  - Recomendo aumentar investimento em SEO
  
- **Tráfego Pago**: 2.87% (8,920 sessões, 256 conversões)
  - Abaixo da média, sugere otimização de campanhas
  
- **Tráfego Direto**: 3.19% (5,630 sessões, 180 conversões)
  - Performance sólida, indica boa brand awareness

**Páginas com Melhor Conversão:**
1. /produto-premium: 5.87% (3,200 visitantes)
2. /promocao-black-friday: 5.23% (4,100 visitantes)
3. /produto-basico: 4.01% (5,600 visitantes)

### ⚠️ Alertas Técnicos

Identificado problema de performance no endpoint `/checkout`:
- **Latência P95**: 890ms (acima do recomendado)
- **Status**: ⚠️ Degraded - Alta latência detectada
- **Impacto potencial**: Pode estar afetando conversão nesta etapa

### ✅ Recomendações

1. **Prioridade Alta**: Investigar e otimizar API de checkout
   - Latência atual pode estar causando abandono de carrinho
   
2. **Aumentar investimento em tráfego orgânico**
   - Melhor ROI: 4.21% de conversão vs 2.87% do pago
   
3. **Otimizar campanhas pagas**
   - Taxa de conversão 32% menor que orgânico
   - Revisar targeting e creative

4. **Replicar estratégia da página /produto-premium**
   - Conversão 72% acima da média do site
```

### 8.2 Para geral@company.com (Grupo Geral)

**Ao fazer login:**

```
┌──────────────────────────────────────────────┐
│  Agents Disponíveis:                         │
│                                              │
│  🤖 Assistente Genérico                      │
│                                              │
│  (Agent Diagnóstico de Vendas não visível)  │
└──────────────────────────────────────────────┘
```

**Ao tentar acessar diagnostico-vendas via API:**

```
HTTP 403 Forbidden

{
  "detail": "Access denied to this agent"
}
```

---

## 9. Troubleshooting

### Problema: Open WebUI não mostra agents

**Sintomas:**
- Dropdown de modelos vazio
- Ou mostra apenas modelos LLM brutos (GPT-4, Claude)

**Solução:**
1. Verificar se Function está instalada:
   ```bash
   # Via UI: Workspace > Functions
   # Deve aparecer "AI Platform Agents"
   ```

2. Verificar logs da Function:
   ```bash
   docker logs open-webui | grep -i function
   ```

3. Verificar se MCP Adapter está rodando:
   ```bash
   docker ps | grep mcp-adapter
   curl http://localhost:8001/agents?user_email=emingues@gmail.com
   ```

4. Verificar connectivity:
   ```bash
   docker exec open-webui ping mcp-adapter
   ```

### Problema: Prompts de exemplo não aparecem

**Sintomas:**
- Agent aparece mas sem cards

**Solução:**
1. Verificar se prompts estão no banco:
   ```sql
   SELECT a.name, COUNT(ap.*) 
   FROM agents a 
   LEFT JOIN agent_prompts ap ON ap.agent_id = a.id 
   GROUP BY a.id, a.name;
   ```

2. Verificar resposta da API:
   ```bash
   curl "http://localhost:8001/agents?user_email=emingues@gmail.com" | jq
   # Deve ter array "prompts" com 4 itens
   ```

3. Verificar logs do MCP Adapter:
   ```bash
   docker logs mcp-adapter | grep prompts
   ```

### Problema: MCPs não são chamados

**Sintomas:**
- Resposta genérica sem dados de analytics/vendas

**Solução:**
1. Verificar se MCP Server está rodando:
   ```bash
   docker ps | grep mcp-server
   ```

2. Verificar configuração agent_mcps no banco:
   ```sql
   SELECT a.name, m.name as mcp_name
   FROM agents a
   JOIN agent_mcps am ON am.agent_id = a.id
   JOIN mcp_configs m ON m.id = am.mcp_id
   WHERE a.agent_key = 'diagnostico-vendas';
   ```

3. Verificar logs do MCP Adapter:
   ```bash
   docker logs mcp-adapter | grep "Calling MCP"
   ```

4. Testar MCP Server isoladamente:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
     docker exec -i mcp-server python /app/main.py
   ```

### Problema: Permissões não funcionam

**Sintomas:**
- User B consegue acessar agent restrito
- Ou User A não consegue acessar

**Solução:**
1. Verificar dados no banco:
   ```sql
   -- User A deve estar no grupo-vendas
   SELECT u.email, g.name
   FROM users u
   JOIN user_groups ug ON ug.user_id = u.id
   JOIN groups g ON g.id = ug.group_id
   WHERE u.email = 'emingues@gmail.com';
   
   -- Grupo vendas deve ter acesso ao agent
   SELECT g.name, a.name
   FROM groups g
   JOIN group_agent_permissions gap ON gap.group_id = g.id
   JOIN agents a ON a.id = gap.agent_id
   WHERE g.name = 'grupo-vendas' AND gap.can_access = true;
   ```

2. Verificar lógica de validação no MCP Adapter
3. Verificar audit logs:
   ```sql
   SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
   ```

---

## 10. Métricas de Sucesso

### Técnicas
- ✅ Tempo de resposta < 5s (excluindo LLM)
- ✅ Taxa de erro < 1%
- ✅ 100% dos testes de permissão passando
- ✅ Langfuse capturando 100% das requests
- ✅ MCPs sendo chamados corretamente

### Funcionais
- ✅ User A vê 2 agents com 8 prompts no total
- ✅ User B vê 1 agent com 4 prompts
- ✅ Cards clicáveis funcionam
- ✅ Respostas contêm dados dos MCPs
- ✅ Bloqueio de acesso funciona (403)

### Observabilidade
- ✅ Traces no Langfuse para cada conversa
- ✅ Spans identificam gargalos
- ✅ Custos calculados por agent
- ✅ Audit logs completos no banco

---

## 11. Arquivos de Referência

1. **Este documento**: Guia completo de implementação
2. **init-db.sql**: Schema e seed data (fornecido separadamente)
3. **PRD-Plataforma-AI-Agents.md**: Arquitetura completa (fornecido separadamente)

---

**Fim do Guia de Implementação**

Total estimado: **4.5 dias** de desenvolvimento
