from __future__ import annotations

TEAM_ROUTING_RULES = {
    "Identity & Access": {
        "keywords": ["password", "mfa", "multi-factor", "login", "sign in", "authentication", "sso", "account locked"],
        "handles": "password resets, MFA failures, account lockouts, and identity issues",
    },
    "Network & VPN": {
        "keywords": ["vpn", "wifi", "network", "latency", "internet", "dns", "proxy", "remote access"],
        "handles": "vpn failures, connectivity incidents, and office or remote networking issues",
    },
    "Endpoint Support": {
        "keywords": ["laptop", "desktop", "printer", "monitor", "keyboard", "hardware", "driver", "battery"],
        "handles": "device issues, peripherals, printer onboarding, and workstation support",
    },
    "Messaging & Collaboration": {
        "keywords": ["outlook", "email", "teams", "calendar", "meeting", "mailbox", "shared mailbox"],
        "handles": "email, calendar, Teams, and collaboration tooling problems",
    },
    "Business Applications": {
        "keywords": ["sap", "salesforce", "workday", "jira", "servicenow", "crm", "erp", "application"],
        "handles": "line-of-business app incidents and access or usage problems",
    },
    "Security Operations": {
        "keywords": ["phishing", "malware", "ransomware", "breach", "suspicious", "compromised", "unauthorized"],
        "handles": "security alerts, suspected compromise, and malicious activity",
    },
}

SEVERITY_GUIDANCE = {
    "Low": "Routine request, minor inconvenience, or issue with a clear workaround.",
    "Medium": "Single-user or limited-scope issue affecting productivity but not causing a wider outage.",
    "High": "Major business impact, urgent deadline, VIP impact, or core tool unavailable with limited workaround.",
    "Critical": "Full outage, severe business disruption, or security risk affecting many users with no workaround.",
}
