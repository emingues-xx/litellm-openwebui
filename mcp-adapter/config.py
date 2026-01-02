from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:change-me-in-production@postgres:5432/litellm"

    # LiteLLM
    litellm_url: str = "http://litellm:4000"
    litellm_api_key: str = "sk-1234-change-this-master-key"

    # MCP Server
    mcp_server_command: str = "docker exec -i mcp-server python /app/server.py"

    # Langfuse (optional)
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: Optional[str] = "http://langfuse:3000"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
