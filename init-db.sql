-- ============================================================================
-- AI Platform Database Schema
-- Implementação conforme COMPLEMENTO.md
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USERS & GROUPS
-- ============================================================================

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de grupos de acesso
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação N:N usuário-grupo
CREATE TABLE IF NOT EXISTS user_groups (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id)
);

-- ============================================================================
-- 2. AGENTS & PROMPTS
-- ============================================================================

-- Tabela de agents customizados
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    agent_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    llm_provider VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'ollama'
    llm_model VARCHAR(100) NOT NULL,    -- 'claude-sonnet-4-20250514', 'gpt-4'
    system_prompt TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de prompts de exemplo (cards clicáveis)
CREATE TABLE IF NOT EXISTS agent_prompts (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    description VARCHAR(255) NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. MCP CONFIGURATION
-- ============================================================================

-- Configurações de MCPs
CREATE TABLE IF NOT EXISTS mcp_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'analytics', 'monitoring', 'database'
    endpoint VARCHAR(500),
    credentials_encrypted TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação N:N agent-MCP (quais MCPs cada agent usa)
CREATE TABLE IF NOT EXISTS agent_mcps (
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    mcp_id INTEGER REFERENCES mcp_configs(id) ON DELETE CASCADE,
    config JSONB,  -- Configurações específicas desta relação
    PRIMARY KEY (agent_id, mcp_id)
);

-- ============================================================================
-- 4. PERMISSIONS
-- ============================================================================

-- Permissões: quais grupos podem acessar quais agents
CREATE TABLE IF NOT EXISTS group_agent_permissions (
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT true,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, agent_id)
);

-- ============================================================================
-- 5. CONVERSATIONS & MESSAGES
-- ============================================================================

-- Histórico de conversas
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mensagens das conversas
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    mcp_data JSONB,  -- Dados retornados pelos MCPs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. AUDIT & LOGS
-- ============================================================================

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,  -- 'chat_started', 'access_denied', etc
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 7. SALES DATA (para MCP consultar)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sales_data (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    customer_id VARCHAR(50),
    source VARCHAR(50),  -- 'organic', 'paid', 'direct'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_sales_date ON sales_data(date);
CREATE INDEX idx_sales_category ON sales_data(category);
CREATE INDEX idx_sales_source ON sales_data(source);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_conversations_user ON conversations(user_id);

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- ============================================================================
-- 1. Grupos
-- ============================================================================
INSERT INTO groups (name, description) VALUES
    ('grupo-vendas', 'Grupo com acesso a agents de vendas e análises'),
    ('grupo-geral', 'Grupo com acesso apenas a agents genéricos')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 2. Usuários
-- ============================================================================
INSERT INTO users (username, email, password_hash, is_active) VALUES
    ('emingues', 'emingues@gmail.com', 'senha123', true),
    ('vendas', 'vendas@company.com', 'senha123', true),
    ('geral', 'geral@company.com', 'senha123', true)
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- 3. Relação Usuário-Grupo
-- ============================================================================
INSERT INTO user_groups (user_id, group_id)
SELECT u.id, g.id
FROM users u, groups g
WHERE u.email = 'emingues@gmail.com' AND g.name = 'grupo-vendas'
ON CONFLICT DO NOTHING;

INSERT INTO user_groups (user_id, group_id)
SELECT u.id, g.id
FROM users u, groups g
WHERE u.email = 'vendas@company.com' AND g.name = 'grupo-vendas'
ON CONFLICT DO NOTHING;

INSERT INTO user_groups (user_id, group_id)
SELECT u.id, g.id
FROM users u, groups g
WHERE u.email = 'geral@company.com' AND g.name = 'grupo-geral'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 4. Agents
-- ============================================================================

-- Agent 1: Diagnóstico de Vendas (apenas grupo-vendas)
INSERT INTO agents (
    agent_key,
    name,
    description,
    llm_provider,
    llm_model,
    system_prompt,
    is_active
) VALUES (
    'diagnostico-vendas',
    'Agent Diagnóstico de Vendas',
    'Analisa performance de vendas consultando dados de analytics, monitoring e banco de dados interno. Fornece insights acionáveis sobre conversão, funil de vendas, performance técnica e recomendações estratégicas.',
    'anthropic',
    'claude-sonnet-4-20250514',
    'Você é um especialista em análise de vendas e performance de e-commerce.

Seu papel é analisar dados de múltiplas fontes (analytics, monitoring, vendas) e fornecer insights acionáveis para tomada de decisão.

DIRETRIZES:
1. Sempre baseie suas análises nos dados fornecidos
2. Identifique tendências, padrões e anomalias
3. Forneça recomendações específicas e priorizadas
4. Use visualizações em markdown (tabelas, listas) quando apropriado
5. Destaque alertas e problemas críticos
6. Correlacione dados técnicos (latência, erros) com impacto em vendas
7. Seja conciso mas completo

FORMATO DE RESPOSTA:
- Resumo Executivo (2-3 frases)
- Principais Descobertas (bullet points)
- Alertas/Problemas (se houver)
- Recomendações Priorizadas

Use emojis para melhorar legibilidade: 📊 📈 📉 ⚠️ ✅ 🎯',
    true
) ON CONFLICT (agent_key) DO NOTHING;

-- Agent 2: Assistente Genérico (todos os grupos)
INSERT INTO agents (
    agent_key,
    name,
    description,
    llm_provider,
    llm_model,
    system_prompt,
    is_active
) VALUES (
    'agent-generico',
    'Assistente Genérico',
    'Assistente de propósito geral para responder perguntas, ajudar com tarefas e fornecer informações. Não tem acesso a dados internos da empresa.',
    'openai',
    'gpt-4',
    'Você é um assistente útil, prestativo e amigável.

Seu papel é ajudar o usuário com perguntas gerais, tarefas de escrita, análise de textos e outras atividades que não requerem dados internos da empresa.

DIRETRIZES:
1. Seja claro, conciso e objetivo
2. Use formatação markdown para melhor legibilidade
3. Se não souber algo, admita honestamente
4. Forneça exemplos quando apropriado
5. Mantenha um tom profissional mas acessível',
    true
) ON CONFLICT (agent_key) DO NOTHING;

-- ============================================================================
-- 5. Prompts de Exemplo
-- ============================================================================

-- Prompts para Agent Diagnóstico de Vendas
INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Qual foi a taxa de conversão nos últimos 30 dias? Compare com o período anterior e identifique as principais fontes de tráfego.',
    'Análise de conversão',
    1
FROM agents a WHERE a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Compare a performance de vendas deste mês com o mês anterior. Analise por categoria de produto e fonte de tráfego.',
    'Comparação mensal',
    2
FROM agents a WHERE a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Identifique os principais gargalos no funil de vendas. Correlacione com problemas técnicos se houver.',
    'Análise de funil',
    3
FROM agents a WHERE a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Mostre as APIs com maior latência e analise se estão afetando a conversão de vendas.',
    'Performance técnica',
    4
FROM agents a WHERE a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

-- Prompts para Agent Genérico
INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Me ajude a escrever um email profissional sobre um projeto que está atrasado.',
    'Redação de email',
    1
FROM agents a WHERE a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Explique o conceito de API REST de forma simples para um iniciante.',
    'Explicação técnica',
    2
FROM agents a WHERE a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Me dê 5 dicas para melhorar a produtividade no trabalho.',
    'Dicas de produtividade',
    3
FROM agents a WHERE a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT
    a.id,
    'Resuma os principais benefícios de usar Docker em projetos de software.',
    'Resumo técnico',
    4
FROM agents a WHERE a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 6. MCP Configs
-- ============================================================================

INSERT INTO mcp_configs (name, type, endpoint, is_active) VALUES
    ('analytics-mock', 'analytics', 'internal://mcp-server', true),
    ('monitoring-mock', 'monitoring', 'internal://mcp-server', true),
    ('internal-db', 'database', 'internal://mcp-server', true)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- 7. Agent-MCP Associations
-- ============================================================================

-- diagnostico-vendas usa todos os MCPs
INSERT INTO agent_mcps (agent_id, mcp_id, config)
SELECT
    a.id,
    m.id,
    '{"enabled": true}'::jsonb
FROM agents a, mcp_configs m
WHERE a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

-- agent-generico não usa MCPs (sem associação)

-- ============================================================================
-- 8. Permissões
-- ============================================================================

-- grupo-vendas acessa diagnostico-vendas
INSERT INTO group_agent_permissions (group_id, agent_id, can_access)
SELECT g.id, a.id, true
FROM groups g, agents a
WHERE g.name = 'grupo-vendas' AND a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

-- grupo-vendas acessa agent-generico
INSERT INTO group_agent_permissions (group_id, agent_id, can_access)
SELECT g.id, a.id, true
FROM groups g, agents a
WHERE g.name = 'grupo-vendas' AND a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

-- grupo-geral acessa APENAS agent-generico
INSERT INTO group_agent_permissions (group_id, agent_id, can_access)
SELECT g.id, a.id, true
FROM groups g, agents a
WHERE g.name = 'grupo-geral' AND a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 9. Sales Data (dados mockados para o MCP consultar)
-- ============================================================================

-- Gera 90 dias de dados de vendas mockados
INSERT INTO sales_data (date, product_id, product_name, category, quantity, unit_price, total_amount, customer_id, source)
SELECT
    CURRENT_DATE - (gs.day_offset || ' days')::interval,
    'PROD-' || LPAD((random() * 50)::integer::text, 3, '0'),
    CASE (random() * 5)::integer
        WHEN 0 THEN 'Notebook Premium'
        WHEN 1 THEN 'Mouse Wireless'
        WHEN 2 THEN 'Teclado Mecânico'
        WHEN 3 THEN 'Monitor 4K'
        ELSE 'Webcam HD'
    END,
    CASE (random() * 3)::integer
        WHEN 0 THEN 'Eletrônicos'
        WHEN 1 THEN 'Periféricos'
        ELSE 'Acessórios'
    END,
    (random() * 10 + 1)::integer,
    (random() * 1000 + 50)::numeric(10,2),
    (random() * 1000 + 50)::numeric(10,2) * (random() * 10 + 1),
    'CUST-' || LPAD((random() * 1000)::integer::text, 4, '0'),
    CASE (random() * 3)::integer
        WHEN 0 THEN 'organic'
        WHEN 1 THEN 'paid'
        ELSE 'direct'
    END
FROM generate_series(0, 89) AS gs(day_offset);

-- ============================================================================
-- VALIDAÇÃO
-- ============================================================================

-- Mostra resumo das tabelas criadas
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Database initialization completed!';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Users: %', (SELECT COUNT(*) FROM users);
    RAISE NOTICE 'Groups: %', (SELECT COUNT(*) FROM groups);
    RAISE NOTICE 'Agents: %', (SELECT COUNT(*) FROM agents);
    RAISE NOTICE 'Agent Prompts: %', (SELECT COUNT(*) FROM agent_prompts);
    RAISE NOTICE 'MCP Configs: %', (SELECT COUNT(*) FROM mcp_configs);
    RAISE NOTICE 'Sales Records: %', (SELECT COUNT(*) FROM sales_data);
    RAISE NOTICE '============================================';
END $$;

-- Mostra configuração de permissões
SELECT
    g.name as grupo,
    u.email as usuario,
    a.name as agent,
    gap.can_access as pode_acessar
FROM users u
JOIN user_groups ug ON ug.user_id = u.id
JOIN groups g ON g.id = ug.group_id
LEFT JOIN group_agent_permissions gap ON gap.group_id = g.id
LEFT JOIN agents a ON a.id = gap.agent_id
ORDER BY g.name, u.email, a.name;
