from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["Low", "Medium", "High", "Critical"]


class TicketTriageResult(BaseModel):
    summary: str
    severity: Severity
    severity_reason: str
    assigned_team: str
    routing_reason: str
    first_response: str
    next_actions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    escalate_to_human: bool = True
    used_fallback: bool = False
