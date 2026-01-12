"""
Permission Middleware - Controle de Acesso por Grupo
Intercepta requisições do Open WebUI e injeta Virtual Keys baseado no grupo do usuário
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import Dict, Optional

app = FastAPI()

# Enable CORS for Open WebUI frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8888", "http://127.0.0.1:8888"],  # Open WebUI URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração
LITELLM_URL = os.getenv("LITELLM_URL", "http://litellm:4000")

# Mapeamento: grupo → Virtual Key
GROUP_KEYS = {
    "vendas": os.getenv("VENDAS_KEY", ""),
    "geral": os.getenv("GERAL_KEY", ""),
}

# Mapeamento: email → grupo
USER_GROUPS = {
    "emingues@gmail.com": "vendas",  # Admin - grupo vendas (acesso premium)
    "vendas@company.com": "vendas",
    "geral@company.com": "geral",
}

DEFAULT_GROUP = "geral"


def get_user_from_request(request: Request) -> Optional[Dict]:
    """
    Extrai informações do usuário dos headers do Open WebUI
    """
    email = request.headers.get("X-OpenWebUI-User-Email")
    user_id = request.headers.get("X-OpenWebUI-User-Id")
    role = request.headers.get("X-OpenWebUI-User-Role")

    if email:
        print(f"[AUTH] User detected: {email} (role: {role})")
        return {
            "email": email,
            "id": user_id,
            "role": role,
        }

    print("[AUTH] No user detected (anonymous)")
    return None


def get_user_group(user: Optional[Dict]) -> str:
    """
    Determina o grupo do usuário
    """
    if not user:
        return DEFAULT_GROUP

    email = user.get("email")
    if email and email in USER_GROUPS:
        group = USER_GROUPS[email]
        print(f"[AUTH] User {email} → group {group}")
        return group

    print(f"[AUTH] User {email} → default group {DEFAULT_GROUP}")
    return DEFAULT_GROUP


def get_virtual_key(group: str) -> str:
    """
    Retorna Virtual Key do grupo
    """
    if group not in GROUP_KEYS or not GROUP_KEYS[group]:
        raise HTTPException(
            status_code=403,
            detail=f"No access configured for group '{group}'"
        )
    return GROUP_KEYS[group]


@app.api_route("/v1/api/agents", methods=["GET", "OPTIONS"])
@app.api_route("/api/agents", methods=["GET", "OPTIONS"])
async def get_agents(request: Request):
    """
    API endpoint para UI customizada buscar agents
    Retorna apenas agents (não modelos tradicionais)
    """
    # Handle OPTIONS preflight request
    if request.method == "OPTIONS":
        return {}

    print(f"[API] Fetching agents for custom UI")

    # Identificar usuário
    user = get_user_from_request(request)

    if not user or not user.get("email"):
        return {"success": False, "agents": [], "error": "Usuário não autenticado"}

    user_email = user["email"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "http://mcp-adapter:8001/agents",
                params={"user_email": user_email}
            )

            if response.status_code == 200:
                agents = response.json()
                print(f"[API] Fetched {len(agents)} agents for {user_email}")

                # Transform to UI format
                agents_ui = [
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

                return {"success": True, "agents": agents_ui}
            else:
                return {"success": False, "agents": [], "error": "Falha ao buscar agentes"}

    except Exception as e:
        print(f"[API] Error fetching agents: {e}")
        return {"success": False, "agents": [], "error": str(e)}


@app.api_route("/v1/api/agents/{agent_id}", methods=["GET", "OPTIONS"])
@app.api_route("/api/agents/{agent_id}", methods=["GET", "OPTIONS"])
async def get_agent_detail(agent_id: str, request: Request):
    """
    API endpoint para buscar detalhes de um agent específico
    Retorna agent com todos os prompts
    """
    # Handle OPTIONS preflight request
    if request.method == "OPTIONS":
        return {}

    print(f"[API] Fetching agent details: {agent_id}")

    # Identificar usuário
    user = get_user_from_request(request)

    if not user or not user.get("email"):
        return {"success": False, "agent": None, "error": "Usuário não autenticado"}

    user_email = user["email"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "http://mcp-adapter:8001/agents",
                params={"user_email": user_email}
            )

            if response.status_code == 200:
                agents = response.json()

                # Find specific agent
                agent = next((a for a in agents if a["id"] == agent_id), None)

                if not agent:
                    return {"success": False, "agent": None, "error": "Agente não encontrado"}

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
                return {"success": False, "agent": None, "error": "Falha ao buscar detalhes do agente"}

    except Exception as e:
        print(f"[API] Error fetching agent details: {e}")
        return {"success": False, "agent": None, "error": str(e)}


@app.get("/v1/models")
async def get_models(request: Request):
    """
    Retorna modelos tradicionais do LiteLLM E agents customizados
    """
    print(f"[MODELS] Fetching models and agents")

    # 1. Identificar usuário
    user = get_user_from_request(request)
    user_email = user.get("email") if user else None
    group = get_user_group(user)

    all_models = []

    # 2. Buscar modelos tradicionais do LiteLLM
    try:
        virtual_key = get_virtual_key(group)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{LITELLM_URL}/v1/models",
                headers={"Authorization": f"Bearer {virtual_key}"}
            )

            if response.status_code == 200:
                litellm_response = response.json()
                litellm_models = litellm_response.get("data", [])
                print(f"[MODELS] Fetched {len(litellm_models)} traditional models from LiteLLM")
                all_models.extend(litellm_models)

    except Exception as e:
        print(f"[MODELS] Error fetching LiteLLM models: {e}")

    # 3. Buscar agents customizados do MCP Adapter
    if user_email:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "http://mcp-adapter:8001/agents",
                    params={"user_email": user_email}
                )

                if response.status_code == 200:
                    agents = response.json()
                    print(f"[MODELS] Fetched {len(agents)} agents for {user_email}")

                    for agent in agents:
                        all_models.append({
                            "id": agent["id"],
                            "object": "model",
                            "created": int(1686935002),
                            "owned_by": "custom-agent",
                            "name": agent["name"]
                        })
        except Exception as e:
            print(f"[MODELS] Error fetching agents: {e}")

    return {"data": all_models, "object": "list"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    """
    Proxy que roteia para MCP Adapter (agents) ou LiteLLM (modelos tradicionais)
    """
    print(f"[PROXY] {request.method} /{path}")

    # 1. Identificar usuário
    user = get_user_from_request(request)
    user_email = user.get("email") if user else None

    # 2. Se for chat completions, verificar se é um agent
    if path == "v1/chat/completions" and request.method == "POST":
        body_bytes = await request.body()

        try:
            import json
            body = json.loads(body_bytes)
            model_id = body.get("model", "")

            # Verificar se é um agent - consulta dinâmica no mcp-adapter
            is_agent = False
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    agents_response = await client.get(
                        "http://mcp-adapter:8001/agents",
                        params={"user_email": user_email or "unknown@empresa.com"}
                    )
                    if agents_response.status_code == 200:
                        agents = agents_response.json()
                        is_agent = any(agent["id"] == model_id for agent in agents)
            except Exception as e:
                print(f"[ROUTER] Error checking if {model_id} is an agent: {e}")
                # Se houver erro ao verificar, assume que não é agent e continua para LiteLLM
                is_agent = False

            if is_agent:
                print(f"[ROUTER] Routing to MCP Adapter for agent: {model_id}")

                # Rotear para MCP Adapter
                messages = body.get("messages", [])

                # Extrair mensagem do usuário e histórico
                if messages:
                    user_message = messages[-1].get("content", "")
                    history = messages[:-1]
                else:
                    user_message = ""
                    history = []

                # Chamar MCP Adapter
                async with httpx.AsyncClient(timeout=600.0) as client:
                    response = await client.post(
                        f"http://mcp-adapter:8001/agents/{model_id}/chat",
                        json={
                            "user_email": user_email or "unknown@empresa.com",
                            "message": user_message,
                            "history": history
                        },
                        headers={"Content-Type": "application/json"}
                    )

                    return StreamingResponse(
                        response.aiter_bytes(),
                        status_code=response.status_code,
                        media_type="text/event-stream"
                    )
        except Exception as e:
            print(f"[ROUTER] Error parsing body: {e}")
            # Continua para o proxy normal

    # 3. Proxy normal para LiteLLM (para outros endpoints ou modelos tradicionais)
    group = get_user_group(user)

    try:
        virtual_key = get_virtual_key(group)
        print(f"[AUTH] Using key for group '{group}': {virtual_key[:20]}...")
    except HTTPException as e:
        print(f"[AUTH] Access denied: {e.detail}")
        raise

    url = f"{LITELLM_URL}/{path}"
    headers = dict(request.headers)

    # Remover headers desnecessários
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers.pop("authorization", None)
    headers.pop("Authorization", None)

    # Injetar Virtual Key
    headers["Authorization"] = f"Bearer {virtual_key}"

    # Usar body já lido se disponível
    try:
        body = body_bytes
    except:
        body = await request.body()

    print(f"[DEBUG] Forwarding to: {url}")

    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params
            )

            print(f"[DEBUG] Response status: {response.status_code}")

            if "text/event-stream" in response.headers.get("content-type", ""):
                return StreamingResponse(
                    response.aiter_bytes(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

            return StreamingResponse(
                iter([response.content]),
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except Exception as e:
            print(f"[ERROR] Failed to proxy request: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "permission-middleware",
        "litellm_url": LITELLM_URL,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
