"""MCP Client for connecting to MCP Server"""
import logging
import asyncio
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Cliente MCP simplificado que chama o MCP Server via subprocess
    Para POC, retorna dados mockados diretamente
    """

    def __init__(self):
        # Em um cenário real, isso viria de variáveis de ambiente
        self.server_url = "http://mcp-server:8080"

    async def call_tool(self, mcp_name: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chama uma tool no MCP Server Real via HTTP
        """
        logger.info(f"[MCP] Calling REAL tool: {tool_name} from {mcp_name} with args: {args}")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.server_url}/tools/execute",
                    json={
                        "tool": tool_name,
                        "params": args
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("result", {})
                else:
                    logger.error(f"MCP Server error: {response.status_code} - {response.text}")
                    return {"error": f"Erro no servidor MCP: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Failed to connect to MCP Server: {e}")
            # Fallback para dados internos se o servidor estiver fora
            logger.info("Falling back to internal mock data...")
            return self._get_internal_mock_data(tool_name, args)

    def _get_internal_mock_data(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dados de fallback caso o mcp-server falhe"""
        if tool_name == "db_query_sales":
            return {
                "period": args.get("period", "30d"),
                "results": [
                    {"category": "Eletrônicos", "total_sales": 450, "revenue": 235890.50},
                    {"category": "Periféricos", "total_sales": 320, "revenue": 89450.30}
                ]
            }
        return {"error": "Tool not available in fallback"}
