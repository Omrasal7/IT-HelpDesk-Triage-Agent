from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Iterable

from .config import DATA_DIR, TICKETS_FILE
from .models import TicketRecord


class TicketStore:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not TICKETS_FILE.exists():
            TICKETS_FILE.write_text("[]", encoding="utf-8")

    def list_tickets(self) -> list[TicketRecord]:
        try:
            raw = json.loads(TICKETS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = []
            TICKETS_FILE.write_text("[]", encoding="utf-8")
        return [TicketRecord.model_validate(item) for item in raw]

    def save_all(self, tickets: Iterable[TicketRecord]) -> None:
        payload = [ticket.model_dump(mode="json") for ticket in tickets]
        TICKETS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def create_ticket(self, ticket: TicketRecord) -> TicketRecord:
        tickets = self.list_tickets()
        tickets.append(ticket)
        self.save_all(tickets)
        return ticket

    def get_ticket(self, ticket_id: str) -> TicketRecord | None:
        for ticket in self.list_tickets():
            if ticket.id == ticket_id:
                return ticket
        return None

    def get_for_requester(self, email: str) -> list[TicketRecord]:
        return [ticket for ticket in self.list_tickets() if ticket.requester_email.lower() == email.lower()]

    def update_ticket(self, ticket_id: str, *, status: str, admin_name: str, admin_note: str) -> TicketRecord | None:
        tickets = self.list_tickets()
        updated_ticket: TicketRecord | None = None
        for index, ticket in enumerate(tickets):
            if ticket.id != ticket_id:
                continue
            ticket.status = status
            ticket.reviewed_by_admin = True
            ticket.admin_name = admin_name
            ticket.admin_note = admin_note
            ticket.resolved = status == "resolved"
            ticket.updated_at = datetime.now(UTC)
            tickets[index] = ticket
            updated_ticket = ticket
            break
        if updated_ticket is not None:
            self.save_all(tickets)
        return updated_ticket
