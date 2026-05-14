from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ToolAccess(BaseModel):
    name: str
    description: str
    actions: list[str] = Field(default_factory=list)


class DataAccess(BaseModel):
    reads: list[str] = Field(default_factory=list)
    writes: list[str] = Field(default_factory=list)


class AgentInventoryItem(BaseModel):
    agent_id: str
    name: str
    purpose: str
    owner: str
    environments: list[str]
    risk_level: RiskLevel
    tool_access: list[ToolAccess]
    data_access: DataAccess
    requires_human_review: bool = False


class AgentInventory(BaseModel):
    version: str = "1.0"
    agents: list[AgentInventoryItem]

    def by_id(self) -> dict[str, AgentInventoryItem]:
        return {agent.agent_id: agent for agent in self.agents}


class AgentRunPlan(BaseModel):
    agent_id: str
    agent_name: str
    environment: str
    read_paths: list[str]
    write_paths: list[str]
    user_intent: str


class GuardrailDecision(BaseModel):
    allowed: bool
    reason: str
    blocked_rule: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ProcurementSummary(BaseModel):
    input_file: str
    budget: str | None
    key_needs: list[str]
    restrictions: list[str]
    delivery_target: str | None
    requester: str | None
    summary: str
    output_file: str
    created_at: str


class ReadinessStatus(str, Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class ReadinessResult(BaseModel):
    status: ReadinessStatus
    run_id: str | None
    reasons: list[str]
