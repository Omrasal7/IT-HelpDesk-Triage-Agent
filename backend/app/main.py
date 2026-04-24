from __future__ import annotations

from collections import Counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import AdminUpdateRequest, DashboardSummary, LoginRequest, TicketRecord, TicketSubmission, UserSession
from .storage import TicketStore
from .triage import triage_ticket

app = FastAPI(title="IT Helpdesk Triage API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = TicketStore()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=UserSession)
def login(payload: LoginRequest) -> UserSession:
    return UserSession(**payload.model_dump())


@app.get("/api/tickets", response_model=list[TicketRecord])
def list_tickets(role: str, email: str | None = None) -> list[TicketRecord]:
    if role == "admin":
        tickets = store.list_tickets()
        return sorted(tickets, key=lambda ticket: ticket.updated_at, reverse=True)
    if role == "employee" and email:
        tickets = store.get_for_requester(email)
        return sorted(tickets, key=lambda ticket: ticket.updated_at, reverse=True)
    raise HTTPException(status_code=400, detail="employee email is required")


@app.get("/api/dashboard", response_model=DashboardSummary)
def dashboard() -> DashboardSummary:
    tickets = store.list_tickets()
    status_counts = Counter(ticket.status for ticket in tickets)
    severity_counts = Counter(ticket.triage.severity for ticket in tickets)
    resolved = sum(1 for ticket in tickets if ticket.resolved)
    return DashboardSummary(
        total=len(tickets),
        resolved=resolved,
        unresolved=len(tickets) - resolved,
        by_status=dict(status_counts),
        by_severity=dict(severity_counts),
    )


@app.post("/api/tickets", response_model=TicketRecord)
def create_ticket(payload: TicketSubmission) -> TicketRecord:
    triage = triage_ticket(payload.model_dump())
    ticket = TicketRecord(**payload.model_dump(), triage=triage)
    return store.create_ticket(ticket)


@app.patch("/api/tickets/{ticket_id}", response_model=TicketRecord)
def update_ticket(ticket_id: str, payload: AdminUpdateRequest) -> TicketRecord:
    ticket = store.update_ticket(
        ticket_id,
        status=payload.status,
        admin_name=payload.admin_name,
        admin_note=payload.admin_note,
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
