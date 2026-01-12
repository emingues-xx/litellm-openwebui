#!/usr/bin/env python3
"""
Update agent to use Claude instead of GPT-4
"""
import sys
sys.path.insert(0, '/app')

from database import SessionLocal
import models

def update_agent():
    db = SessionLocal()

    try:
        # Find the diagnostico-vendas agent
        agent = db.query(models.Agent).filter(
            models.Agent.agent_key == "diagnostico-vendas"
        ).first()

        if agent:
            print(f"[UPDATE] Found agent: {agent.name}")
            print(f"[UPDATE] Current: {agent.llm_provider} / {agent.llm_model}")

            # Update to Claude
            agent.llm_provider = "anthropic"
            agent.llm_model = "claude-3-haiku"

            db.commit()

            print(f"[UPDATE] Updated to: {agent.llm_provider} / {agent.llm_model}")
            print("[UPDATE] ✅ Agent updated successfully!")
        else:
            print("[UPDATE] ❌ Agent not found")

    except Exception as e:
        print(f"[UPDATE] ❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("[UPDATE] Updating agent configuration...")
    update_agent()
