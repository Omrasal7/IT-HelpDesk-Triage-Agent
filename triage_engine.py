from __future__ import annotations

import json
import re
from typing import Any

import requests

from config import MAX_DESCRIPTION_CHARS, OLLAMA_MODEL, OLLAMA_URL, REQUEST_TIMEOUT
from knowledge_base import SEVERITY_GUIDANCE, TEAM_ROUTING_RULES
from schemas import TicketTriageResult


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
        "impacted_users": max(int(ticket.get("impacted_users", 1) or 1), 1),
        "is_vip": bool(ticket.get("is_vip", False)),
        "has_workaround": bool(ticket.get("has_workaround", False)),
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

Your job:
1. Read the support ticket.
2. Classify severity as Low, Medium, High, or Critical.
3. Route the ticket to the best support team.
4. Draft a polished first-response reply for the support engineer.
5. Recommend next actions.

Severity guidance:
{severity_rules}

Routing teams:
{routing_rules}

Return ONLY valid JSON with this schema:
{{
  "summary": "short summary",
  "severity": "Low|Medium|High|Critical",
  "severity_reason": "why",
  "assigned_team": "team name",
  "routing_reason": "why this team",
  "first_response": "engineer-ready response to send to requester",
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

    next_actions = _build_next_actions(assigned_team, severity, ticket)
    first_response = _build_first_response(ticket, assigned_team, severity)

    return TicketTriageResult(
        summary=_build_summary(ticket, assigned_team),
        severity=severity,
        severity_reason=_build_severity_reason(severity, ticket, haystack),
        assigned_team=assigned_team,
        routing_reason=f"Matched keywords and issue pattern consistent with {assigned_team.lower()} ownership.",
        first_response=first_response,
        next_actions=next_actions,
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
    impacted_users = ticket["impacted_users"]
    urgent_keywords = ["outage", "cannot access", "down", "security", "breach", "phishing", "customer call", "production"]
    critical_keywords = ["ransomware", "compromised", "many users", "entire company", "all users"]

    if any(word in haystack for word in critical_keywords):
        return "Critical"
    if impacted_users >= 25 and not ticket["has_workaround"]:
        return "Critical"
    if any(word in haystack for word in urgent_keywords) or ticket["is_vip"]:
        return "High"
    if impacted_users >= 5:
        return "High"
    if ticket["has_workaround"]:
        return "Low"
    return "Medium"


def _build_summary(ticket: dict[str, Any], team: str) -> str:
    return (
        f"{ticket['title']} reported by {ticket.get('requester_name', 'the requester')} "
        f"is most likely owned by {team}."
    )


def _build_severity_reason(severity: str, ticket: dict[str, Any], haystack: str) -> str:
    reasons = [SEVERITY_GUIDANCE[severity]]
    if ticket["is_vip"]:
        reasons.append("Requester is marked as VIP.")
    if ticket["impacted_users"] > 1:
        reasons.append(f"Reported impact includes {ticket['impacted_users']} users.")
    if "customer call" in haystack or "urgent" in haystack:
        reasons.append("The ticket mentions a near-term business deadline.")
    if ticket["has_workaround"]:
        reasons.append("A workaround is available, which lowers immediate business risk.")
    return " ".join(reasons)


def _build_first_response(ticket: dict[str, Any], team: str, severity: str) -> str:
    requester = ticket.get("requester_name", "there")
    return (
        f"Hi {requester},\n\n"
        f"Thanks for reporting this. I have triaged your request as {severity} severity and routed it to the {team} team for investigation. "
        "We are reviewing the details now and will keep you updated on the next troubleshooting step.\n\n"
        "If anything changes, please reply with any recent error messages, screenshots, or steps already attempted."
    )


def _build_next_actions(team: str, severity: str, ticket: dict[str, Any]) -> list[str]:
    actions = [
        f"Assign the ticket to {team}.",
        "Validate the issue against recent incidents and known problems.",
        "Confirm device, location, timestamp, and exact error details with the requester.",
    ]
    if severity in {"High", "Critical"}:
        actions.append("Start engineer review immediately and monitor for broader impact.")
    if ticket["is_vip"]:
        actions.append("Apply VIP handling and provide a proactive status update.")
    return actions


def _build_tags(team: str, severity: str, haystack: str) -> list[str]:
    tags = [severity.lower(), team.lower().replace(" & ", "-").replace(" ", "-")]
    if "vpn" in haystack:
        tags.append("vpn")
    if "password" in haystack:
        tags.append("password-reset")
    if "outlook" in haystack:
        tags.append("outlook")
    if "phishing" in haystack:
        tags.append("security")
    return tags
