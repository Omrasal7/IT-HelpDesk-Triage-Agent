from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field

Severity = Literal["Low", "Medium", "High", "Critical"]
TicketStatus = Literal["new", "in_progress", "waiting_on_user", "resolved", "escalated", "could_not_reach"]
UserRole = Literal["employee", "admin"]


class LoginRequest(BaseModel):
    role: UserRole
    name: str = Field(min_length=2)
    email: EmailStr
    department: str = Field(min_length=2)


class UserSession(BaseModel):
    name: str
    email: EmailStr
    department: str
    role: UserRole


class TicketSubmission(BaseModel):
    requester_name: str = Field(min_length=2)
    requester_email: EmailStr
    department: str = Field(min_length=2)
    title: str = Field(min_length=4)
    description: str = Field(min_length=10)


class TicketTriageResult(BaseModel):
    summary: str
    severity: Severity
    severity_reason: str
    assigned_team: str
    routing_reason: str
    first_response: str
    next_actions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    escalate_to_human: bool = True
    used_fallback: bool = False


class AdminUpdateRequest(BaseModel):
    status: TicketStatus
    admin_name: str = Field(min_length=2)
    admin_note: str = Field(default="")


class TicketRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"HD-{uuid4().hex[:8].upper()}")
    requester_name: str
    requester_email: EmailStr
    department: str
    title: str
    description: str
    status: TicketStatus = "new"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved: bool = False
    reviewed_by_admin: bool = False
    admin_name: str | None = None
    admin_note: str = ""
    triage: TicketTriageResult


class DashboardSummary(BaseModel):
    total: int
    resolved: int
    unresolved: int
    by_status: dict[str, int]
    by_severity: dict[str, int]
