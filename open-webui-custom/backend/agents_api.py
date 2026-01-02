"""
Custom API endpoints for Agents UI
Extends Open WebUI with agents sidebar and prompt cards
"""

from fastapi import APIRouter, Request, HTTPException
from typing import List, Dict
import httpx
import os

router = APIRouter()

MCP_ADAPTER_URL = os.getenv("MCP_ADAPTER_URL", "http://mcp-adapter:8001")


def get_user_email(request: Request) -> str:
    """Extract user email from request"""
    # Open WebUI stores user in request.state after authentication
    user = getattr(request.state, "user", None)
    if user:
        return user.email
    return "unknown@empresa.com"


@router.get("/api/agents")
async def list_agents(request: Request):
    """
    List all agents available for the current user

    Returns agents with their prompts for display in the sidebar
    """
    user_email = get_user_email(request)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{MCP_ADAPTER_URL}/agents",
                params={"user_email": user_email}
            )

            if response.status_code == 200:
                agents = response.json()

                # Transform to UI format
                return {
                    "success": True,
                    "agents": [
                        {
                            "id": agent["id"],
                            "name": agent["name"],
                            "description": agent.get("description", ""),
                            "llm_model": agent["llm_model"],
                            "llm_provider": agent["llm_provider"],
                            "prompt_count": len(agent.get("prompts", []))
                        }
                        for agent in agents
                    ]
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch agents"
                )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/{agent_id}")
async def get_agent_details(agent_id: str, request: Request):
    """
    Get detailed information about a specific agent

    Returns agent with all prompt cards for the detail view
    """
    user_email = get_user_email(request)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{MCP_ADAPTER_URL}/agents",
                params={"user_email": user_email}
            )

            if response.status_code == 200:
                agents = response.json()

                # Find specific agent
                agent = next((a for a in agents if a["id"] == agent_id), None)

                if not agent:
                    raise HTTPException(status_code=404, detail="Agent not found")

                return {
                    "success": True,
                    "agent": {
                        "id": agent["id"],
                        "name": agent["name"],
                        "description": agent.get("description", ""),
                        "llm_model": agent["llm_model"],
                        "llm_provider": agent["llm_provider"],
                        "prompts": agent.get("prompts", [])
                    }
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch agent details"
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/agents/{agent_id}/chat")
async def start_agent_chat(agent_id: str, request: Request):
    """
    Start a new chat with an agent

    Creates a new chat session and returns the chat ID
    This is called when user clicks on a prompt card
    """
    user_email = get_user_email(request)
    body = await request.json()

    prompt_content = body.get("prompt", "")

    if not prompt_content:
        raise HTTPException(status_code=400, detail="Prompt content required")

    # This will be handled by Open WebUI's existing chat creation
    # We just return the formatted request
    return {
        "success": True,
        "model": agent_id,
        "message": prompt_content,
        "user_email": user_email
    }
