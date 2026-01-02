"""
MCP Server - Model Context Protocol Server
Fornece tools simuladas para agents consumirem
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import random

app = FastAPI()


class ToolRequest(BaseModel):
    tool: str
    params: Dict[str, Any] = {}


# =============================================================================
# Mock Tools - Dados simulados para POC
# =============================================================================

def get_analytics_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simula dados de analytics (Google Analytics, etc)
    """
    metric = params.get("metric", "cart_abandonment")

    if metric == "cart_abandonment":
        return {
            "metric": "cart_abandonment",
            "period": "last_7_days",
            "abandonment_rate": 68.5,
            "carts_created": 3250,
            "carts_abandoned": 2226,
            "top_abandonment_step": "payment",
            "status": "CRITICAL",
            "details": {
                "step_breakdown": {
                    "cart": 100,
                    "shipping": 245,
                    "payment": 1245,
                    "confirmation": 636
                }
            }
        }

    elif metric == "conversion_rate":
        return {
            "metric": "conversion_rate",
            "period": "last_7_days",
            "conversion_rate": 2.3,
            "visitors": 45000,
            "conversions": 1035,
            "status": "WARNING"
        }

    return {"error": f"Unknown metric: {metric}"}


def get_monitoring_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simula dados de monitoring (DataDog, New Relic, etc)
    """
    metric = params.get("metric", "checkout_errors")

    if metric == "checkout_errors":
        return {
            "metric": "checkout_errors",
            "period": "last_hour",
            "total_errors": 325,
            "error_rate": 15.2,  # %
            "status": "CRITICAL",
            "top_errors": [
                {
                    "message": "Payment gateway timeout after 30s",
                    "count": 178,
                    "percentage": 54.8
                },
                {
                    "message": "Invalid credit card validation",
                    "count": 89,
                    "percentage": 27.4
                },
                {
                    "message": "Database connection pool exhausted",
                    "count": 58,
                    "percentage": 17.8
                }
            ]
        }

    elif metric == "api_latency":
        return {
            "metric": "api_latency",
            "period": "last_hour",
            "p50": 245,  # ms
            "p95": 1250,  # ms
            "p99": 4500,  # ms
            "status": "WARNING"
        }

    return {"error": f"Unknown metric: {metric}"}


def search_knowledge_base(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simula busca em base de conhecimento interna
    """
    query = params.get("query", "")

    # Simular resultados baseados na query
    if "checkout" in query.lower() or "payment" in query.lower():
        return {
            "results": [
                {
                    "title": "Checkout Flow - Known Issues",
                    "content": "Payment gateway has known timeout issues during peak hours (6pm-8pm). Recommended solution: implement retry logic and increase timeout to 45s.",
                    "relevance": 0.95
                },
                {
                    "title": "Credit Card Validation Rules",
                    "content": "Updated validation rules on Dec 15. Some international cards may fail validation. Whitelist: Visa, Mastercard, Amex.",
                    "relevance": 0.82
                }
            ],
            "total_results": 2
        }

    return {
        "results": [],
        "total_results": 0
    }


# Tool registry
TOOLS = {
    "get_analytics": get_analytics_data,
    "get_monitoring": get_monitoring_data,
    "search_knowledge": search_knowledge_base,
}


# =============================================================================
# API Endpoints
# =============================================================================

@app.post("/tools/execute")
async def execute_tool(request: ToolRequest):
    """
    Executa uma tool e retorna o resultado
    """
    tool_name = request.tool

    if tool_name not in TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available: {list(TOOLS.keys())}"
        )

    try:
        result = TOOLS[tool_name](request.params)
        return {
            "tool": tool_name,
            "result": result,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )


@app.get("/tools")
async def list_tools():
    """
    Lista tools disponíveis
    """
    return {
        "tools": [
            {
                "name": "get_analytics",
                "description": "Get analytics data (cart abandonment, conversion, etc)",
                "params": {
                    "metric": "string (cart_abandonment, conversion_rate)"
                }
            },
            {
                "name": "get_monitoring",
                "description": "Get monitoring data (errors, latency, etc)",
                "params": {
                    "metric": "string (checkout_errors, api_latency)"
                }
            },
            {
                "name": "search_knowledge",
                "description": "Search internal knowledge base",
                "params": {
                    "query": "string"
                }
            }
        ]
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "mcp-server",
        "tools_available": len(TOOLS)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
