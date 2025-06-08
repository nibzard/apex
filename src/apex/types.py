"""Shared type definitions for APEX."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of APEX agents."""

    SUPERVISOR = "supervisor"
    CODER = "coder"
    ADVERSARY = "adversary"


class SessionState(str, Enum):
    """Session states."""

    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    FAILED = "failed"


class ProjectConfig(BaseModel):
    """Project configuration."""

    project_id: str
    name: str
    description: str
    tech_stack: List[str]
    project_type: str
    features: List[str]
    created_at: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """Agent state information."""

    agent_type: AgentType
    status: str
    started_at: Optional[datetime] = None
    process_id: Optional[int] = None
    last_activity: Optional[datetime] = None
    current_task: Optional[str] = None


class TaskInfo(BaseModel):
    """Task information."""

    task_id: str
    description: str
    assigned_to: AgentType
    priority: str = "medium"
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    depends_on: List[str] = Field(default_factory=list)


class StreamEvent(BaseModel):
    """Stream event from Claude CLI."""

    type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str
    agent_id: str
    raw_event: Dict[str, Any]


class MCPToolCall(BaseModel):
    """MCP tool call information."""

    tool_id: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
