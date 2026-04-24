import requests

from triage_engine import triage_ticket


def generate_response(prompt: str) -> str:
    ticket = {
        "title": "Ad hoc prompt",
        "description": prompt,
        "requester_name": "User",
        "requester_email": "user@example.com",
        "department": "Other",
        "impacted_users": 1,
        "is_vip": False,
        "has_workaround": False,
    }
    result = triage_ticket(ticket)
    return result.first_response
