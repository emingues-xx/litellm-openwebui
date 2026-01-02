"""Utility functions for MCP decision making"""
from typing import List, Dict
import models


def identify_needed_mcps(message: str, available_mcps: List[models.McpConfig]) -> List[models.McpConfig]:
    """
    Identifica quais MCPs chamar baseado na mensagem do usuário

    Args:
        message: Mensagem do usuário
        available_mcps: Lista de MCPs disponíveis para este agent

    Returns:
        Lista de MCPs que devem ser chamados
    """
    keywords = {
        "analytics": ["conversão", "tráfego", "visitas", "sessions", "funil", "taxa", "conversion"],
        "monitoring": ["latência", "erro", "performance", "api", "timeout", "latency", "error"],
        "database": ["vendas", "receita", "produto", "cliente", "ticket", "sales", "revenue"]
    }

    message_lower = message.lower()
    needed_mcps = []

    for mcp in available_mcps:
        mcp_keywords = keywords.get(mcp.type, [])
        if any(kw in message_lower for kw in mcp_keywords):
            needed_mcps.append(mcp)

    # Se nenhum keyword, usa conjunto padrão para diagnóstico
    if not needed_mcps and available_mcps:
        # Para agent de vendas, usa analytics + database por padrão
        needed_mcps = [
            mcp for mcp in available_mcps
            if mcp.type in ["analytics", "database"]
        ]

    return needed_mcps


def get_tool_for_mcp(mcp_type: str, message: str) -> str:
    """
    Retorna nome da tool a chamar no MCP Server baseado no tipo de MCP e mensagem

    Args:
        mcp_type: Tipo do MCP (analytics, monitoring, database)
        message: Mensagem do usuário

    Returns:
        Nome da tool a ser chamada
    """
    message_lower = message.lower()

    if mcp_type == "analytics":
        if "conversão" in message_lower or "conversion" in message_lower:
            return "analytics_get_conversion"
        else:
            return "analytics_get_traffic"

    elif mcp_type == "monitoring":
        if "latência" in message_lower or "latency" in message_lower:
            return "monitoring_get_latency"
        else:
            return "monitoring_get_errors"

    else:  # database
        return "db_query_sales"


def get_args_for_tool(message: str) -> Dict:
    """
    Extrai argumentos para a tool baseado na mensagem

    Args:
        message: Mensagem do usuário

    Returns:
        Dicionário de argumentos
    """
    args = {}

    # Detecta período
    if "30 dias" in message.lower() or "30d" in message.lower():
        args["period"] = "30d"
    elif "7 dias" in message.lower() or "7d" in message.lower():
        args["period"] = "7d"
    else:
        args["period"] = "30d"  # default

    # Detecta agrupamento para queries de banco
    if "categoria" in message.lower() or "category" in message.lower():
        args["group_by"] = "category"
    elif "fonte" in message.lower() or "source" in message.lower():
        args["group_by"] = "source"
    else:
        args["group_by"] = "category"  # default

    return args
