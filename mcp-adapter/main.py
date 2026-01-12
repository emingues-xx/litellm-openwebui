"""
MCP Adapter - FastAPI service
Orquestra agents, permissões e chamadas MCP
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import httpx
import logging
import json

from database import get_db
import models
import schemas
from config import settings
from mcp_client import MCPClient
from utils.mcp_utils import identify_needed_mcps, get_tool_for_mcp, get_args_for_tool
from utils.format_utils import format_mcp_results

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Adapter",
    description="Orquestra agents customizados com permissões e integração MCP",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    from database import Base, engine
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "service": "mcp-adapter"}


@app.get("/agents", response_model=List[schemas.AgentSchema])
async def list_agents(
    user_email: str,
    db: Session = Depends(get_db)
):
    """
    Lista agents que o usuário pode acessar

    Fluxo:
    1. Busca usuário por email
    2. Busca grupos do usuário
    3. Busca permissões dos grupos
    4. Busca agents permitidos
    5. Para cada agent, busca prompts de exemplo
    """
    logger.info(f"[GET /agents] user_email={user_email}")

    # 1. Busca usuário
    user = db.query(models.User).filter(
        models.User.email == user_email
    ).first()

    if not user:
        logger.warning(f"User not found: {user_email}")
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Busca grupos do usuário
    user_groups = db.query(models.UserGroup).filter(
        models.UserGroup.user_id == user.id
    ).all()

    group_ids = [ug.group_id for ug in user_groups]
    logger.info(f"User {user_email} belongs to {len(group_ids)} groups")

    if not group_ids:
        logger.warning(f"User {user_email} has no groups")
        return []

    # 3. Busca permissões dos grupos
    permissions = db.query(models.GroupAgentPermission).filter(
        models.GroupAgentPermission.group_id.in_(group_ids),
        models.GroupAgentPermission.can_access == True
    ).all()

    agent_ids = [p.agent_id for p in permissions]
    logger.info(f"User {user_email} has access to {len(agent_ids)} agents")

    if not agent_ids:
        logger.info(f"No agents available for user {user_email}")
        return []

    # 4. Busca agents
    agents = db.query(models.Agent).filter(
        models.Agent.id.in_(agent_ids),
        models.Agent.is_active == True
    ).all()

    # 5. Para cada agent, busca prompts
    result = []
    for agent in agents:
        prompts = db.query(models.AgentPrompt).filter(
            models.AgentPrompt.agent_id == agent.id
        ).order_by(models.AgentPrompt.display_order).all()

        result.append(schemas.AgentSchema(
            id=agent.agent_key,
            name=agent.name,
            description=agent.description,
            llm_provider=agent.llm_provider,
            llm_model=agent.llm_model,
            prompts=[
                schemas.PromptSchema(
                    title=p.description,
                    content=p.prompt_text
                )
                for p in prompts
            ]
        ))

    logger.info(f"Returning {len(result)} agents for user {user_email}")
    return result


@app.post("/agents/{agent_key}/chat")
async def chat(
    agent_key: str,
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Processa chat com agent específico

    Fluxo:
    1. Busca agent
    2. Valida permissão do usuário
    3. Registra audit log
    4. Identifica MCPs necessários
    5. Chama MCPs
    6. Enriquece contexto
    7. Chama LiteLLM com streaming
    """
    logger.info(f"[POST /agents/{agent_key}/chat] user={request.user_email}")

    # 1. Busca agent
    agent = db.query(models.Agent).filter(
        models.Agent.agent_key == agent_key,
        models.Agent.is_active == True
    ).first()

    if not agent:
        logger.error(f"Agent não encontrado: {agent_key}")
        raise HTTPException(status_code=404, detail="Agente não encontrado")

    # 2. Busca usuário
    user = db.query(models.User).filter(
        models.User.email == request.user_email
    ).first()

    if not user:
        logger.error(f"Usuário não encontrado: {request.user_email}")
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # 3. Valida permissão
    has_access = db.query(models.GroupAgentPermission).join(
        models.UserGroup,
        models.GroupAgentPermission.group_id == models.UserGroup.group_id
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

        logger.warning(f"Acesso negado para usuário {request.user_email} ao agente {agent_key}")
        raise HTTPException(status_code=403, detail="Acesso negado a este agente")

    # 4. Registra acesso permitido
    audit_log = models.AuditLog(
        user_id=user.id,
        agent_id=agent.id,
        action='chat_started',
        details={'message_preview': request.message[:100]}
    )
    db.add(audit_log)
    db.commit()

    # 5. Busca MCPs configurados para este agent (ORQUESTRAÇÃO: Restaurando Enriquecimento)
    agent_mcps = db.query(models.AgentMcp).filter(
        models.AgentMcp.agent_id == agent.id
    ).all()

    mcp_configs = []
    for am in agent_mcps:
        mcp = db.query(models.McpConfig).filter(
            models.McpConfig.id == am.mcp_id,
            models.McpConfig.is_active == True
        ).first()
        if mcp:
            mcp_configs.append(mcp)

    logger.info(f"Agent {agent_key} has {len(mcp_configs)} MCPs configured for enrichment")

    # 6. Identifica quais MCPs chamar (baseado na pergunta)
    mcps_to_call = identify_needed_mcps(request.message, mcp_configs)
    
    # Se não identificou nada específico mas é o agent de vendas, força os MCPs de dados
    if not mcps_to_call and agent_key == "diagnostico-vendas":
        mcps_to_call = mcp_configs

    logger.info(f"Will call {len(mcps_to_call)} MCPs: {[m.name for m in mcps_to_call]}")

    # 7. Chama MCPs e coleta resultados
    mcp_client = MCPClient()
    mcp_results = {}

    for mcp_config in mcps_to_call:
        # Tenta mapear ferramenta. Se falhar, usa uma padrão por tipo
        tool_name = get_tool_for_mcp(mcp_config.type, request.message)
        tool_args = get_args_for_tool(request.message)

        try:
            logger.info(f"Calling MCP {mcp_config.name} tool {tool_name}")
            result = await mcp_client.call_tool(
                mcp_name=mcp_config.name,
                tool_name=tool_name,
                args=tool_args
            )
            mcp_results[mcp_config.name] = result
        except Exception as e:
            logger.error(f"Error calling MCP {mcp_config.name}: {e}")
            mcp_results[mcp_config.name] = {"error": str(e)}

    # 8. Formata contexto enriquecido
    context = format_mcp_results(mcp_results)
    
    # 9. Monta mensagem enriquecida
    if mcp_results:
        enriched_message = f"""{request.message}

---
DADOS DISPONÍVEIS PARA ANÁLISE (MOCK):

{context}
---

Por favor, analise estes dados e forneça insights acionáveis conforme seu system prompt."""
    else:
        enriched_message = request.message

    logger.info(f"[ROUTER] Forwarding enriched request to LiteLLM for agent {agent_key} (Model: {agent.llm_model})")

    # 10. Prepara mensagens para LLM
    messages = [
        {
            "role": "system",
            "content": agent.system_prompt
        }
    ]

    # Adiciona histórico se existir
    if request.history:
        for msg in request.history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

    # Adiciona a mensagem enriquecida do usuário
    messages.append({
        "role": "user",
        "content": enriched_message
    })

    # 11. Chama LiteLLM com streaming
    async def generate():
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"Calling LiteLLM with model {agent.llm_model}")

                async with client.stream(
                    "POST",
                    f"{settings.litellm_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.litellm_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": agent.llm_model,
                        "messages": messages,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"LiteLLM error: {response.status_code} - {error_text}")
                        
                        friendly_error = "O provedor de IA está sobrecarregado no momento. Por favor, tente novamente em instantes." if response.status_code == 503 else f"Erro ao chamar o modelo: {response.status_code}"
                        
                        yield f"data: {{\"choices\": [ {{\"delta\": {{\"content\": \"\\n\\n⚠️ **{friendly_error}**\"}}, \"index\": 0, \"finish_reason\": \"error\" }} ] }}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    async for line in response.aiter_lines():
                        if line.strip():
                            yield line + "\n"

        except Exception as e:
            logger.error(f"Error in generate: {e}")
            yield f"data: {{\"choices\": [ {{\"delta\": {{\"content\": \"\\n\\n❌ **Erro Inesperado:** {str(e)}\"}}, \"index\": 0 }} ] }}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
