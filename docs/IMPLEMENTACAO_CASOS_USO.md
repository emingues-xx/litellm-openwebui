# Implementação de Casos de Uso: Risco TI e Marketing

Este guia demonstra como utilizar a arquitetura atual para disponibilizar novos agents e ferramentas para times específicos, seguindo o "Golden Path".

---

## 🛡️ Caso 1: Agent de Análise de Risco (LangChain) para o time `risco-ti`

Neste cenário, você já tem um serviço Python rodando LangChain que expõe uma API compatível com OpenAI.

### Passo 1: Configurar o LiteLLM Proxy
Adicione o endpoint do seu serviço LangChain no arquivo `litellm/config.yaml`:

```yaml
model_list:
  - model_name: langchain-risco-engine
    litellm_params:
      model: openai/custom
      api_base: http://servico-risco:8000/v1
      api_key: sk-sua-chave-interna
```

### Passo 2: Configuração via Banco de Dados (SQL)
Execute os comandos para criar o grupo, o agent e as permissões:

```sql
-- 1. Criar o grupo
INSERT INTO groups (name, description) VALUES ('risco-ti', 'Time de Segurança e Riscos de Infra');

-- 2. Criar o Agent apontando para o modelo do LangChain
INSERT INTO agents (agent_key, name, description, llm_model, system_prompt)
VALUES (
    'analise-risco', 
    'Analista de Risco TI', 
    'Agent especializado em análise de vulnerabilidades e compliance.', 
    'langchain-risco-engine', 
    'Você é um analista sênior de Risco TI. Use sua lógica interna para avaliar os dados...'
);

-- 3. Dar acesso ao grupo
INSERT INTO group_agent_permissions (group_id, agent_id, can_access)
SELECT g.id, a.id, true FROM groups g, agents a 
WHERE g.name = 'risco-ti' AND a.agent_key = 'analise-risco';
```

---

## 📈 Caso 2: Ferramenta (MCP) Google Analytics para o time `mkt`

Neste cenário, usaremos um modelo de mercado (ex: Claude 3.5 Sonnet) mas daremos a ele "poderes" de consultar o Google Analytics via MCP.

### Passo 1: Cadastrar o Servidor MCP
No banco de dados, registre o servidor que contém as ferramentas do GA:

```sql
INSERT INTO mcp_configs (name, type, endpoint, is_active)
VALUES ('google-analytics-mcp', 'analytics', 'http://mcp-ga-server:8080', true);
```

### Passo 2: Configuração via Banco de Dados (SQL)
Crie o agent para o marketing e vincule a ferramenta:

```sql
-- 1. Criar o grupo
INSERT INTO groups (name, description) VALUES ('mkt', 'Time de Performance e Growth');

-- 2. Criar o Agent usando um modelo padrão (Claude)
INSERT INTO agents (agent_key, name, description, llm_model, system_prompt)
VALUES (
    'dashboard-mkt', 
    'Especialista em GA4', 
    'Agent que analisa tráfego e conversão direto do Google Analytics.', 
    'claude-3-haiku', 
    'Você é um especialista em marketing. Use as ferramentas de Analytics para responder...'
);

-- 3. Vincular o MCP ao Agent
INSERT INTO agent_mcps (agent_id, mcp_id)
SELECT a.id, m.id FROM agents a, mcp_configs m 
WHERE a.agent_key = 'dashboard-mkt' AND m.name = 'google-analytics-mcp';

-- 4. Dar acesso ao grupo de marketing
INSERT INTO group_agent_permissions (group_id, agent_id, can_access)
SELECT g.id, a.id, true FROM groups g, agents a 
WHERE g.name = 'mkt' AND a.agent_key = 'dashboard-mkt';
```

---

## 📝 Resumo do Fluxo de Trabalho

| Ação | Risco TI (LangChain) | Marketing (GA MCP) |
| :--- | :--- | :--- |
| **Onde está a lógica?** | No código Python do LangChain | No System Prompt + Tools |
| **Quem responde?** | O seu serviço externo | O Claude (via LiteLLM) |
| **Configuração LiteLLM?** | Sim (nova rota de modelo) | Não (usa modelo já existente) |
| **Configuração MCP?** | Não (lógica interna) | Sim (servidor de ferramentas) |

Estes exemplos mostram que a arquitetura suporta tanto a **delegação total da inteligência** (Caso 1) quanto o **enriquecimento de modelos padrão** (Caso 2).
