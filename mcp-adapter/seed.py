"""
Seed script to populate initial data in database
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

def seed_database():
    db = SessionLocal()

    try:
        # Create Users
        user1 = models.User(
            username="emingues",
            email="emingues@gmail.com",
            is_active=True
        )
        db.add(user1)
        db.flush()  # Get ID

        print(f"[SEED] Created user: {user1.email}")

        # Create Groups
        group_vendas = models.Group(
            name="vendas",
            description="Grupo de vendas com acesso a agents premium"
        )
        group_geral = models.Group(
            name="geral",
            description="Grupo geral com acesso básico"
        )
        db.add(group_vendas)
        db.add(group_geral)
        db.flush()

        print(f"[SEED] Created groups: vendas, geral")

        # Associate user with group
        user_group = models.UserGroup(
            user_id=user1.id,
            group_id=group_vendas.id
        )
        db.add(user_group)

        print(f"[SEED] Associated {user1.email} with group vendas")

        # Create Agent
        agent = models.Agent(
            agent_key="diagnostico-vendas",
            name="Diagnóstico de Vendas",
            description="Agent especializado em análise de vendas e métricas de performance",
            llm_provider="anthropic",
            llm_model="claude-3-haiku",
            system_prompt="Você é um especialista em análise de vendas e métricas de performance.",
            is_active=True
        )
        db.add(agent)
        db.flush()

        print(f"[SEED] Created agent: {agent.name}")

        # Create Agent Prompts
        prompts_data = [
            {
                "prompt_text": "Quais são os produtos mais vendidos nos últimos 30 dias?",
                "description": "Top Produtos",
                "display_order": 1
            },
            {
                "prompt_text": "Qual foi o faturamento total do último mês?",
                "description": "Faturamento Mensal",
                "display_order": 2
            },
            {
                "prompt_text": "Quais categorias tiveram melhor performance?",
                "description": "Performance por Categoria",
                "display_order": 3
            }
        ]

        for prompt_data in prompts_data:
            prompt = models.AgentPrompt(
                agent_id=agent.id,
                **prompt_data
            )
            db.add(prompt)

        print(f"[SEED] Created {len(prompts_data)} prompts for agent")

        # Grant permission to group
        permission = models.GroupAgentPermission(
            group_id=group_vendas.id,
            agent_id=agent.id,
            can_access=True
        )
        db.add(permission)

        print(f"[SEED] Granted access to group vendas for agent {agent.name}")

        # Create MCP Configs
        mcp_analytics = models.McpConfig(
            name="analytics-mock",
            type="analytics",
            endpoint="internal://mcp-server",
            is_active=True
        )
        mcp_monitoring = models.McpConfig(
            name="monitoring-mock",
            type="monitoring",
            endpoint="internal://mcp-server",
            is_active=True
        )
        mcp_db = models.McpConfig(
            name="internal-db",
            type="database",
            endpoint="internal://mcp-server",
            is_active=True
        )
        db.add(mcp_analytics)
        db.add(mcp_monitoring)
        db.add(mcp_db)
        db.flush()

        print(f"[SEED] Created MCP configs: analytics, monitoring, database")

        # Associate agent with MCPs
        agent_mcp1 = models.AgentMcp(agent_id=agent.id, mcp_id=mcp_analytics.id, config={"enabled": True})
        agent_mcp2 = models.AgentMcp(agent_id=agent.id, mcp_id=mcp_monitoring.id, config={"enabled": True})
        agent_mcp3 = models.AgentMcp(agent_id=agent.id, mcp_id=mcp_db.id, config={"enabled": True})
        db.add(agent_mcp1)
        db.add(agent_mcp2)
        db.add(agent_mcp3)

        print(f"[SEED] Associated agent {agent.name} with all MCPs")

        # Commit all changes
        db.commit()
        print("[SEED] Database seeded successfully!")

    except Exception as e:
        print(f"[SEED] Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("[SEED] Starting database seed...")
    seed_database()
