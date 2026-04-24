from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from triage_engine import triage_ticket

st.set_page_config(
    page_title="IT Helpdesk Triage Agent",
    page_icon="??",
    layout="wide",
)

st.title("IT Helpdesk Triage Agent")
st.caption(
    "Reads support tickets, classifies severity, routes them to the right team, and drafts a first response for the engineer."
)

with st.sidebar:
    st.header("Ticket Context")
    requester_name = st.text_input("Requester name", value=" ")
    requester_email = st.text_input("Requester email", value="")
    department = st.selectbox(
        "Department",
        ["Finance", "HR", "Engineering", "Sales", "Operations", "Executive", "Other"],
        index=2,
    )
    impacted_users = st.number_input("Users impacted", min_value=1, value=1, step=1)
    is_vip = st.checkbox("VIP / executive requester")
    has_workaround = st.checkbox("Workaround available")

col1, col2 = st.columns([3, 2])

with col1:
    title = st.text_input(
        "Ticket title",
        value="VPN stopped working after password reset",
    )
    description = st.text_area(
        "Ticket description",
        value=(
            "I changed my password this morning and now the VPN client says authentication failed. "
            "I cannot access internal tools from home and I have a customer call in 30 minutes."
        ),
        height=220,
    )

with col2:
    st.subheader("What the agent returns")
    st.markdown(
        "- Business severity\n"
        "- Recommended routing team\n"
        "- Triage rationale\n"
        "- Suggested engineer first response\n"
        "- Tags and next actions"
    )

if st.button("Analyze Ticket", type="primary"):
    ticket = {
        "title": title,
        "description": description,
        "requester_name": requester_name,
        "requester_email": requester_email,
        "department": department,
        "impacted_users": impacted_users,
        "is_vip": is_vip,
        "has_workaround": has_workaround,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }

    with st.spinner("Reviewing ticket and preparing triage recommendation..."):
        result = triage_ticket(ticket)

    st.success("Ticket analyzed")

    metrics = st.columns(4)
    metrics[0].metric("Severity", result.severity)
    metrics[1].metric("Route To", result.assigned_team)
    metrics[2].metric("Confidence", f"{int(result.confidence * 100)}%")
    metrics[3].metric("Escalate", "Yes" if result.escalate_to_human else "No")

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Summary")
        st.write(result.summary)

        st.subheader("Why this severity")
        st.write(result.severity_reason)

        st.subheader("Why this route")
        st.write(result.routing_reason)

        st.subheader("Recommended first response")
        st.code(result.first_response, language="markdown")

    with right:
        st.subheader("Tags")
        st.write(", ".join(result.tags) if result.tags else "No tags")

        st.subheader("Next actions")
        for item in result.next_actions:
            st.markdown(f"- {item}")

        st.subheader("Used fallback")
        st.write("Yes" if result.used_fallback else "No")

    with st.expander("Structured JSON"):
        st.json(json.loads(result.model_dump_json()))
