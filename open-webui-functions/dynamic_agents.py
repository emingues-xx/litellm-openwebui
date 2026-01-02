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
        self.type = "pipe"  # Pipe que intercepta todas as chamadas
        self.id = "ai-platform-agents"
        self.name = "AI Platform Agents"
        self.valves = self.Valves()
        self.pipelines = []  # Cache de agents

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
                    "data": {"content": "Você não tem permissão para acessar este agent."}
                })
                return {"status": "error"}

            elif response.status_code != 200:
                await __event_emitter__({
                    "type": "message",
                    "data": {"content": f"Erro ao processar: {response.status_code}"}
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
                "data": {"content": "Timeout ao processar requisição"}
            })
            return {"status": "error"}

        except Exception as e:
            logger.error(f"Error in pipe: {e}")
            await __event_emitter__({
                "type": "message",
                "data": {"content": f"Erro: {str(e)}"}
            })
            return {"status": "error"}
