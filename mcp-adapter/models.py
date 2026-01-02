from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Date, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB, INET, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    user_groups = relationship("UserGroup", back_populates="user")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())

    user_groups = relationship("UserGroup", back_populates="group")
    permissions = relationship("GroupAgentPermission", back_populates="group")


class UserGroup(Base):
    __tablename__ = "user_groups"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime, default=func.current_timestamp())

    user = relationship("User", back_populates="user_groups")
    group = relationship("Group", back_populates="user_groups")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    llm_provider = Column(String(50), nullable=False)
    llm_model = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    prompts = relationship("AgentPrompt", back_populates="agent")
    mcps = relationship("AgentMcp", back_populates="agent")
    permissions = relationship("GroupAgentPermission", back_populates="agent")


class AgentPrompt(Base):
    __tablename__ = "agent_prompts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    prompt_text = Column(Text, nullable=False)
    description = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.current_timestamp())

    agent = relationship("Agent", back_populates="prompts")


class McpConfig(Base):
    __tablename__ = "mcp_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    endpoint = Column(String(500))
    credentials_encrypted = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())

    agent_mcps = relationship("AgentMcp", back_populates="mcp")


class AgentMcp(Base):
    __tablename__ = "agent_mcps"

    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    mcp_id = Column(Integer, ForeignKey("mcp_configs.id", ondelete="CASCADE"), primary_key=True)
    config = Column(JSONB)

    agent = relationship("Agent", back_populates="mcps")
    mcp = relationship("McpConfig", back_populates="agent_mcps")


class GroupAgentPermission(Base):
    __tablename__ = "group_agent_permissions"

    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    can_access = Column(Boolean, default=True)
    granted_at = Column(DateTime, default=func.current_timestamp())

    group = relationship("Group", back_populates="permissions")
    agent = relationship("Agent", back_populates="permissions")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"))
    title = Column(String(500))
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    mcp_data = Column(JSONB)
    created_at = Column(DateTime, default=func.current_timestamp())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp(), index=True)


class SalesData(Base):
    __tablename__ = "sales_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    customer_id = Column(String(50))
    source = Column(String(50), index=True)
    created_at = Column(DateTime, default=func.current_timestamp())
