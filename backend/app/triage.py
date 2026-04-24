from __future__ import annotations

import json
import re
from typing import Any

import requests

from .config import MAX_DESCRIPTION_CHARS, OLLAMA_MODEL, OLLAMA_URL, REQUEST_TIMEOUT
from .knowledge_base import SEVERITY_GUIDANCE, TEAM_ROUTING_RULES
from .models import TicketTriageResult


def triage_ticket(ticket: dict[str, Any]) -> TicketTriageResult:
    normalized = _normalize_ticket(ticket)
    prompt = _build_prompt(normalized)

    try:
        llm_output = _generate_response(prompt)
        parsed = _parse_llm_json(llm_output)
        result = TicketTriageResult(**parsed)
        result.used_fallback = False
        return result
    except Exception:
        return _fallback_triage(normalized)


def _normalize_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    description = str(ticket.get("description", "")).strip()
    return {
        **ticket,
        "title": str(ticket.get("title", "")).strip() or "Untitled ticket",
        "description": description[:MAX_DESCRIPTION_CHARS],
    }


def _build_prompt(ticket: dict[str, Any]) -> str:
    routing_rules = "\n".join(
        f"- {team}: {details['handles']}"
        for team, details in TEAM_ROUTING_RULES.items()
    )
    severity_rules = "\n".join(
        f"- {severity}: {meaning}"
        for severity, meaning in SEVERITY_GUIDANCE.items()
    )

    return f"""
You are an enterprise IT helpdesk triage agent.

Read the support ticket and return valid JSON only.
Classify severity as Low, Medium, High, or Critical.
Route to the best support team.
Draft a first-response reply written in first person as the engineer replying directly to the employee.
Recommend next actions.

Severity guidance:
{severity_rules}

Routing teams:
{routing_rules}

Return JSON with this schema:
{{
  "summary": "short summary",
  "severity": "Low|Medium|High|Critical",
  "severity_reason": "why",
  "assigned_team": "team name",
  "routing_reason": "why this team",
  "first_response": "engineer-ready first-person response to send to requester",
  "next_actions": ["action 1", "action 2"],
  "tags": ["tag1", "tag2"],
  "confidence": 0.0,
  "escalate_to_human": true
}}

Ticket:
{json.dumps(ticket, indent=2)}
""".strip()


def _generate_response(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


def _parse_llm_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("Empty LLM response")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _fallback_triage(ticket: dict[str, Any]) -> TicketTriageResult:
    haystack = f"{ticket['title']} {ticket['description']}".lower()
    assigned_team = _route_team(haystack)
    severity = _classify_severity(haystack, ticket)

    return TicketTriageResult(
        summary=f"{ticket['title']} reported by {ticket.get('requester_name', 'the requester')} is most likely owned by {assigned_team}.",
        severity=severity,
        severity_reason=_build_severity_reason(severity, haystack),
        assigned_team=assigned_team,
        routing_reason=f"Matched keywords and issue pattern consistent with {assigned_team.lower()} ownership.",
        first_response=_build_first_response(ticket, assigned_team, severity),
        next_actions=_build_next_actions(assigned_team, severity),
        tags=_build_tags(assigned_team, severity, haystack),
        confidence=0.72,
        escalate_to_human=severity in {"High", "Critical"},
        used_fallback=True,
    )


def _route_team(haystack: str) -> str:
    best_team = "Service Desk"
    best_score = 0
    for team, details in TEAM_ROUTING_RULES.items():
        score = sum(1 for keyword in details["keywords"] if keyword in haystack)
        if score > best_score:
            best_score = score
            best_team = team
    return best_team


def _classify_severity(haystack: str, ticket: dict[str, Any]) -> str:
    if any(word in haystack for word in ["ransomware", "compromised", "breach", "all users", "entire company"]):
        return "Critical"
    if any(word in haystack for word in ["outage", "cannot access", "down", "phishing", "urgent", "customer call", "production"]):
        return "High"
    if any(word in haystack for word in ["slow", "error", "issue", "failed"]):
        return "Medium"
    return "Low"


def _build_severity_reason(severity: str, haystack: str) -> str:
    reason = SEVERITY_GUIDANCE[severity]
    if "customer call" in haystack or "urgent" in haystack:
        reason += " The ticket mentions a near-term business deadline."
    return reason


def _build_first_response(ticket: dict[str, Any], team: str, severity: str) -> str:
    requester = ticket.get("requester_name", "there")
    return (
        f"Hi {requester},\n\n"
        f"I have reviewed your ticket and classified it as {severity} severity. I am routing it to the {team} team so we can investigate it right away. "
        "I am checking the details now and will update you with the next step shortly.\n\n"
        "Please reply with any screenshots, exact error messages, and when the issue first started if you have them."
    )


def _build_next_actions(team: str, severity: str) -> list[str]:
    actions = [
        f"Assign the ticket to {team}.",
        "Check for related incidents or duplicates.",
        "Confirm device, location, and exact error details with the requester.",
    ]
    if severity in {"High", "Critical"}:
        actions.append("Start engineer review immediately and monitor for broader impact.")
    return actions


def _build_tags(team: str, severity: str, haystack: str) -> list[str]:
    tags = [severity.lower(), team.lower().replace(" & ", "-").replace(" ", "-")]
    for word in ["vpn", "password", "outlook", "printer", "phishing"]:
        if word in haystack:
            tags.append(word)
    return tags
