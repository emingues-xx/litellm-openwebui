from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PromptSchema(BaseModel):
    title: str
    content: str


class AgentSchema(BaseModel):
    id: str  # agent_key
    name: str
    description: Optional[str] = None
    llm_provider: str
    llm_model: str
    prompts: List[PromptSchema] = []

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_email: str
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    status: str
    message: Optional[str] = None
