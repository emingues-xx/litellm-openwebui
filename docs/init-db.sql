-- ============================================================================
-- AI Platform - Database Initialization Script
-- ============================================================================
-- Este script cria o schema completo e popula com dados iniciais (seed data)
-- ============================================================================

-- ============================================================================
-- SCHEMA CREATION
-- ============================================================================

-- Usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grupos de usuários
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação User-Group (N:N)
CREATE TABLE IF NOT EXISTS user_groups (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id)
);

-- Agents/Modelos
CREATE TABLE IF NOT EXISTS agents (
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
CREATE TABLE IF NOT EXISTS agent_prompts (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    description VARCHAR(255),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuração de MCPs
CREATE TABLE IF NOT EXISTS mcp_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'analytics', 'monitoring', 'database'
    endpoint VARCHAR(500),
    credentials_encrypted TEXT,  -- JSON encriptado com credenciais
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relação Agent-MCP (N:N)
CREATE TABLE IF NOT EXISTS agent_mcps (
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    mcp_id INTEGER REFERENCES mcp_configs(id) ON DELETE CASCADE,
    config JSONB,  -- Configurações específicas da relação
    PRIMARY KEY (agent_id, mcp_id)
);

-- Permissões Group-Agent (N:N)
CREATE TABLE IF NOT EXISTS group_agent_permissions (
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT true,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, agent_id)
);

-- Histórico de conversas
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mensagens das conversas
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    mcp_data JSONB,  -- Dados retornados pelos MCPs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,  -- 'access_granted', 'access_denied', 'message_sent'
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de dados mock de vendas (para o MCP interno consultar)
CREATE TABLE IF NOT EXISTS sales_data (
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

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_groups_user ON user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group ON user_groups(group_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_data_date ON sales_data(date);
CREATE INDEX IF NOT EXISTS idx_sales_data_source ON sales_data(source);
CREATE INDEX IF NOT EXISTS idx_sales_data_category ON sales_data(category);

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Grupos
INSERT INTO groups (name, description) VALUES
('grupo-vendas', 'Grupo com acesso a análises de vendas e métricas avançadas'),
('grupo-geral', 'Grupo com acesso aos agents genéricos')
ON CONFLICT (name) DO NOTHING;

-- Usuários (senha: senha123 - hash bcrypt)
-- Para gerar o hash: python -c "from passlib.hash import bcrypt; print(bcrypt.hash('senha123'))"
INSERT INTO users (username, email, password_hash) VALUES
('user-a', 'user-a@empresa.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7667.ves4W'),
('user-b', 'user-b@empresa.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7667.ves4W')
ON CONFLICT (username) DO NOTHING;

-- Associações User-Group
INSERT INTO user_groups (user_id, group_id) 
SELECT u.id, g.id 
FROM users u, groups g 
WHERE u.username = 'user-a' AND g.name = 'grupo-vendas'
ON CONFLICT DO NOTHING;

INSERT INTO user_groups (user_id, group_id) 
SELECT u.id, g.id 
FROM users u, groups g 
WHERE u.username = 'user-b' AND g.name = 'grupo-geral'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- AGENTS
-- ============================================================================

-- Agent 1: Diagnóstico de Vendas (restrito ao grupo-vendas)
INSERT INTO agents (agent_key, name, description, llm_provider, llm_model, system_prompt) VALUES
(
    'diagnostico-vendas',
    'Agent Diagnóstico de Vendas',
    'Analisa performance de vendas consultando dados de analytics (similar ao Google Analytics), monitoring (similar ao Datadog) e banco de dados interno. Identifica gargalos, oportunidades e fornece insights acionáveis.',
    'anthropic',
    'claude-sonnet-4-20250514',
    'Você é um analista de vendas sênior com expertise em e-commerce e análise de dados.

Sua função é diagnosticar a performance de vendas da empresa usando dados de múltiplas fontes:
- **Analytics**: Métricas de tráfego, conversão, fontes de tráfego e comportamento do usuário (similar ao Google Analytics)
- **Monitoring**: Performance técnica, latência de APIs, taxa de erros e disponibilidade (similar ao Datadog)
- **Database Interno**: Dados transacionais de vendas, receita, ticket médio e segmentação por categoria/fonte

## Diretrizes de Análise:

1. **Contextualize os números**: Sempre compare com períodos anteriores e explique o que os números significam para o negócio.
   - Exemplo: "A taxa de conversão de 3.42% representa um aumento de 14.77% vs período anterior, indicando melhora na efetividade do funil"

2. **Identifique correlações**: Busque relações entre diferentes métricas.
   - Exemplo: "A alta latência de 890ms no endpoint /checkout (P95) pode estar contribuindo para a queda de 5% na conversão desta página"

3. **Priorize insights acionáveis**: Foque em descobertas que levem a ações concretas.
   - Exemplo: "Recomendo: (1) Investigar a API de checkout com urgência, (2) Aumentar investimento em tráfego orgânico que converte 47% melhor"

4. **Organize com clareza**: Use markdown com seções, bullets e emojis para facilitar leitura.

5. **Seja objetivo**: Vá direto ao ponto. Líderes precisam de insights rápidos e claros.

## Exemplo de Resposta Bem Estruturada:

### 📊 Resumo Executivo
[2-3 frases sobre o status geral]

### 🎯 Principais Descobertas
- **Descoberta 1**: [insight + impacto]
- **Descoberta 2**: [insight + impacto]

### ⚠️ Alertas / Gargalos
- [Problema identificado + severidade]

### ✅ Recomendações
1. [Ação prioritária]
2. [Ação secundária]

Seja sempre profissional, baseado em dados e focado em gerar valor para o negócio.'
)
ON CONFLICT (agent_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    llm_provider = EXCLUDED.llm_provider,
    llm_model = EXCLUDED.llm_model,
    system_prompt = EXCLUDED.system_prompt,
    updated_at = CURRENT_TIMESTAMP;

-- Agent 2: Assistente Genérico (acessível a todos)
INSERT INTO agents (agent_key, name, description, llm_provider, llm_model, system_prompt) VALUES
(
    'agent-generico',
    'Assistente Genérico',
    'Assistente de propósito geral para tarefas diversas como redação, explicações técnicas, brainstorming e revisão de textos. Ideal para uso cotidiano.',
    'openai',
    'gpt-4',
    'Você é um assistente prestativo, cordial e altamente competente.

Sua função é ajudar o usuário com uma ampla variedade de tarefas:
- Redação de textos (emails, documentos, posts)
- Explicações técnicas e conceituais
- Brainstorming e geração de ideias
- Revisão e melhoria de textos
- Resolução de problemas
- Suporte geral

## Diretrizes:

1. **Seja claro e objetivo**: Vá direto ao ponto sem rodeios desnecessários.

2. **Adapte-se ao contexto**: 
   - Para textos técnicos: Use linguagem precisa e estruturada
   - Para textos criativos: Seja mais fluido e expressivo
   - Para explicações: Use exemplos e analogias

3. **Organize bem**: Use markdown quando apropriado (listas, seções, código).

4. **Seja amigável**: Mantenha um tom profissional mas acessível.

5. **Pergunte quando necessário**: Se algo não estiver claro, peça esclarecimentos.

6. **Forneça contexto**: Quando relevante, explique o "porquê" além do "como".

Você está aqui para ajudar da melhor forma possível. Seja prestativo, competente e empático.'
)
ON CONFLICT (agent_key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    llm_provider = EXCLUDED.llm_provider,
    llm_model = EXCLUDED.llm_model,
    system_prompt = EXCLUDED.system_prompt,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- PROMPTS DE EXEMPLO
-- ============================================================================

-- Prompts para Agent Diagnóstico de Vendas
INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order) 
SELECT a.id, p.prompt_text, p.description, p.display_order
FROM agents a, (VALUES
    ('Qual foi a taxa de conversão de vendas nos últimos 30 dias?', 'Análise de conversão', 1),
    ('Compare a performance de vendas deste mês com o mês anterior', 'Comparação mensal', 2),
    ('Identifique os principais gargalos no funil de vendas', 'Análise de funil', 3),
    ('Mostre as APIs com maior latência que podem estar afetando vendas', 'Performance técnica', 4)
) AS p(prompt_text, description, display_order)
WHERE a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

-- Prompts para Agent Genérico
INSERT INTO agent_prompts (agent_id, prompt_text, description, display_order)
SELECT a.id, p.prompt_text, p.description, p.display_order
FROM agents a, (VALUES
    ('Me ajude a escrever um email profissional para um cliente', 'Redação de email', 1),
    ('Explique o conceito de APIs REST de forma simples', 'Explicação técnica', 2),
    ('Sugira 5 ideias criativas para uma apresentação sobre inovação', 'Brainstorming', 3),
    ('Revise este texto e sugira melhorias de clareza e gramática', 'Revisão de texto', 4)
) AS p(prompt_text, description, display_order)
WHERE a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- MCPs
-- ============================================================================

-- MCP Configs (apontam para o MCP Server interno)
INSERT INTO mcp_configs (name, type, endpoint) VALUES
('analytics-mock', 'analytics', 'mcp-server:8002'),
('monitoring-mock', 'monitoring', 'mcp-server:8002'),
('internal-db', 'database', 'mcp-server:8002')
ON CONFLICT (name) DO NOTHING;

-- Associação Agent-MCP
-- Agent Diagnóstico usa os 3 MCPs
INSERT INTO agent_mcps (agent_id, mcp_id) 
SELECT a.id, m.id 
FROM agents a, mcp_configs m 
WHERE a.agent_key = 'diagnostico-vendas' AND m.name = 'analytics-mock'
ON CONFLICT DO NOTHING;

INSERT INTO agent_mcps (agent_id, mcp_id) 
SELECT a.id, m.id 
FROM agents a, mcp_configs m 
WHERE a.agent_key = 'diagnostico-vendas' AND m.name = 'monitoring-mock'
ON CONFLICT DO NOTHING;

INSERT INTO agent_mcps (agent_id, mcp_id) 
SELECT a.id, m.id 
FROM agents a, mcp_configs m 
WHERE a.agent_key = 'diagnostico-vendas' AND m.name = 'internal-db'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- PERMISSÕES
-- ============================================================================

-- Grupo Vendas: Acessa Diagnóstico + Genérico
INSERT INTO group_agent_permissions (group_id, agent_id) 
SELECT g.id, a.id 
FROM groups g, agents a 
WHERE g.name = 'grupo-vendas' AND a.agent_key = 'diagnostico-vendas'
ON CONFLICT DO NOTHING;

INSERT INTO group_agent_permissions (group_id, agent_id) 
SELECT g.id, a.id 
FROM groups g, agents a 
WHERE g.name = 'grupo-vendas' AND a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

-- Grupo Geral: Acessa apenas Genérico
INSERT INTO group_agent_permissions (group_id, agent_id) 
SELECT g.id, a.id 
FROM groups g, agents a 
WHERE g.name = 'grupo-geral' AND a.agent_key = 'agent-generico'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- DADOS MOCK DE VENDAS
-- ============================================================================

-- Gera 500 vendas aleatórias dos últimos 30 dias
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
FROM generate_series(1, 500)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- VERIFICAÇÕES FINAIS
-- ============================================================================

-- Mostra resumo do que foi criado
DO $$
BEGIN
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Database initialized successfully!';
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Users created: %', (SELECT COUNT(*) FROM users);
    RAISE NOTICE 'Groups created: %', (SELECT COUNT(*) FROM groups);
    RAISE NOTICE 'Agents created: %', (SELECT COUNT(*) FROM agents);
    RAISE NOTICE 'Agent prompts: %', (SELECT COUNT(*) FROM agent_prompts);
    RAISE NOTICE 'MCPs configured: %', (SELECT COUNT(*) FROM mcp_configs);
    RAISE NOTICE 'Permissions set: %', (SELECT COUNT(*) FROM group_agent_permissions);
    RAISE NOTICE 'Sales data records: %', (SELECT COUNT(*) FROM sales_data);
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Test users:';
    RAISE NOTICE '  - user-a / senha123 (Grupo Vendas)';
    RAISE NOTICE '  - user-b / senha123 (Grupo Geral)';
    RAISE NOTICE '=================================================';
END $$;

-- Lista agents criados
SELECT 
    agent_key,
    name,
    llm_provider || '/' || llm_model as model,
    (SELECT COUNT(*) FROM agent_prompts WHERE agent_id = agents.id) as prompts_count,
    (SELECT COUNT(*) FROM group_agent_permissions WHERE agent_id = agents.id) as groups_with_access
FROM agents
ORDER BY id;
