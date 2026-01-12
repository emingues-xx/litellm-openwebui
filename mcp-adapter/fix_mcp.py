
"""
Fix missing MCP configurations and associations
"""
import sys
import os

# Adiciona o diretório atual ao path para importar models e database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal
import models

def fix_mcp():
    db = SessionLocal()

    try:
        # 1. Buscar agent
        agent = db.query(models.Agent).filter(
            models.Agent.agent_key == "diagnostico-vendas"
        ).first()

        if not agent:
            print("[FIX] Total error: Agent diagnostico-vendas not found!")
            return

        # 2. Criar MCP Configs (se não existirem)
        mcp_configs = [
            {
                "name": "analytics-mock",
                "type": "analytics",
                "endpoint": "internal://mcp-server",
                "is_active": True
            },
            {
                "name": "monitoring-mock",
                "type": "monitoring",
                "endpoint": "internal://mcp-server",
                "is_active": True
            },
            {
                "name": "internal-db",
                "type": "database",
                "endpoint": "internal://mcp-server",
                "is_active": True
            }
        ]

        created_mcps = []
        for cfg in mcp_configs:
            existing = db.query(models.McpConfig).filter(
                models.McpConfig.name == cfg["name"]
            ).first()
            
            if not existing:
                mcp = models.McpConfig(**cfg)
                db.add(mcp)
                db.flush()
                print(f"[FIX] Created MCP: {cfg['name']}")
                created_mcps.append(mcp)
            else:
                print(f"[FIX] MCP already exists: {cfg['name']}")
                created_mcps.append(existing)

        # 3. Criar associações (se não existirem)
        for mcp in created_mcps:
            existing_assoc = db.query(models.AgentMcp).filter(
                models.AgentMcp.agent_id == agent.id,
                models.AgentMcp.mcp_id == mcp.id
            ).first()

            if not existing_assoc:
                assoc = models.AgentMcp(
                    agent_id=agent.id,
                    mcp_id=mcp.id,
                    config={"enabled": True}
                )
                db.add(assoc)
                print(f"[FIX] Associated agent {agent.agent_key} with {mcp.name}")
            else:
                print(f"[FIX] Association already exists for {mcp.name}")

        db.commit()
        print("[FIX] All done!")

    except Exception as e:
        print(f"[FIX] Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_mcp()
