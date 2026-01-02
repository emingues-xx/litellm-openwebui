"""Utility functions for formatting MCP results"""
import json
from typing import Dict, Any


def format_mcp_results(results: Dict[str, Any]) -> str:
    """
    Formata resultados MCP para incluir no contexto do LLM

    Args:
        results: Dicionário com resultados de cada MCP

    Returns:
        String formatada em markdown
    """
    formatted = []

    for mcp_name, data in results.items():
        if "error" in data:
            continue  # Pula erros

        formatted.append(f"### {mcp_name}")
        formatted.append(format_single_mcp(mcp_name, data))

    return "\n\n".join(formatted) if formatted else "Nenhum dado disponível."


def format_single_mcp(mcp_name: str, data: Dict[str, Any]) -> str:
    """
    Formata um resultado MCP específico

    Args:
        mcp_name: Nome do MCP
        data: Dados retornados pelo MCP

    Returns:
        String formatada em markdown
    """
    if "analytics" in mcp_name:
        return _format_analytics(data)
    elif "monitoring" in mcp_name:
        return _format_monitoring(data)
    elif "database" in mcp_name or "internal-db" in mcp_name:
        return _format_database(data)
    else:
        # Fallback: JSON formatado
        return f"```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"


def _format_analytics(data: Dict[str, Any]) -> str:
    """Formata dados de analytics"""
    result = []

    if "conversion_rate" in data:
        cr = data["conversion_rate"]
        comp = data.get("comparison", {})

        result.append(f"**Taxa de Conversão**: {cr.get('formatted', cr.get('value', 'N/A'))}")

        if comp:
            direction = comp.get("direction", "")
            change = comp.get("change_percent", 0)
            result.append(f"**Variação**: {direction} {change}% vs período anterior")

        result.append("\n**Por Fonte:**")
        for item in data.get("breakdown_by_source", []):
            rate = item.get("rate", 0) * 100
            sessions = item.get("sessions", 0)
            source = item.get("source", "Unknown")
            result.append(f"- {source}: {rate:.2f}% ({sessions:,} sessões)")

        if data.get("top_pages"):
            result.append("\n**Páginas com Melhor Conversão:**")
            for page in data["top_pages"][:3]:
                rate = page.get("rate", 0) * 100
                visitors = page.get("visitors", 0)
                result.append(f"- {page['page']}: {rate:.2f}% ({visitors:,} visitantes)")

    elif "total_sessions" in data:
        result.append(f"**Total de Sessões**: {data['total_sessions']:,}")
        result.append(f"**Visitantes Únicos**: {data.get('unique_visitors', 0):,}")
        result.append(f"**Taxa de Rejeição**: {data.get('bounce_rate', 0)*100:.1f}%")
        result.append(f"**Duração Média**: {data.get('avg_session_duration', 0)} segundos")

        result.append("\n**Por Fonte:**")
        for item in data.get("by_source", []):
            result.append(f"- {item['source'].capitalize()}: {item['sessions']:,} ({item['percent']:.1f}%)")

    return "\n".join(result)


def _format_monitoring(data: Dict[str, Any]) -> str:
    """Formata dados de monitoring"""
    result = []

    if "average_latency" in data:
        latency = data["average_latency"]
        result.append(f"**Latência Média**: P50={latency['p50']}ms, P95={latency['p95']}ms, P99={latency['p99']}ms")

        result.append("\n**Por Endpoint:**")
        for ep in data.get("endpoints", []):
            alert = f" ⚠️ {ep['alert']}" if ep.get('alert') else ""
            status_emoji = "⚠️" if ep.get('status') == 'degraded' else "✅"
            result.append(f"- {status_emoji} {ep['endpoint']}: P95={ep['p95']}ms{alert}")

    elif "error_rate" in data:
        result.append(f"**Taxa de Erros**: {data['error_rate']*100:.2f}%")
        result.append(f"**Total de Erros**: {data['total_errors']:,} de {data['total_requests']:,} requisições")

        result.append("\n**Por Tipo:**")
        for item in data.get("by_type", []):
            result.append(f"- {item['type']}: {item['count']} ocorrências")

        if data.get("top_failing_endpoints"):
            result.append("\n**Endpoints com Mais Erros:**")
            for ep in data["top_failing_endpoints"]:
                result.append(f"- {ep['endpoint']}: {ep['errors']} erros ({ep['error_rate']*100:.2f}%)")

    return "\n".join(result)


def _format_database(data: Dict[str, Any]) -> str:
    """Formata dados de database"""
    result = []

    if "results" in data:
        group_by = data.get('group_by', 'N/A')
        period = data.get('period', 'N/A')

        result.append(f"**Período**: {period}")
        result.append(f"**Agrupado por**: {group_by}\n")

        for row in data["results"][:5]:  # Top 5
            # Pega primeiro valor (category ou source)
            key = list(row.keys())[0]
            value = row[key]

            total_sales = row.get('total_sales', 0)
            revenue = row.get('revenue', 0)

            result.append(f"- **{value}**: {total_sales} vendas, R$ {revenue:,.2f}")

    return "\n".join(result)
