"""
Groq-powered chat service for Campus Explorer.

Fetches live campus, event, and location data from the database and injects it
as context into a Groq LLM system prompt so the model can answer questions like:
  - "Where is the Tech Fest happening?"
  - "What events are at Chennai campus this week?"
  - "How do I get to the Library from the Academic Block?"
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Optional

from flask import current_app
from groq import Groq

from app.models import Campus, Event


# ---------------------------------------------------------------------------
# Context builder — pulls live data from the DB
# ---------------------------------------------------------------------------

def _build_context() -> str:
    """Return a compact text snapshot of all campuses, locations, and events."""
    lines: list[str] = []

    campuses = Campus.query.filter_by(is_active=True).all()
    events = (
        Event.query
        .filter_by(is_active=True)
        .order_by(Event.date, Event.start_time)
        .all()
    )

    # ── Campus + location data ──────────────────────────────────────────────
    lines.append("=== CAMPUSES & LOCATIONS ===")
    for campus in campuses:
        lines.append(f"\nCampus: {campus.display_name} (id: {campus.id})")
        lines.append(f"  Center: {campus.center_latitude}, {campus.center_longitude}")
        if campus.locations_data:
            loc_names = list(campus.locations_data.keys())
            lines.append(f"  Locations ({len(loc_names)}): {', '.join(loc_names)}")
        else:
            lines.append("  Locations: none recorded yet")

    # ── Event data ──────────────────────────────────────────────────────────
    lines.append("\n=== EVENTS ===")
    if not events:
        lines.append("No events currently scheduled.")
    else:
        today = date.today()
        for ev in events:
            status = "upcoming" if ev.date >= today else "past"
            end = f" – {ev.end_time.strftime('%H:%M')}" if ev.end_time else ""
            campus_name = next(
                (c.display_name for c in campuses if c.id == ev.campus_id),
                ev.campus_id
            )
            lines.append(
                f"- [{status}] \"{ev.name}\" | Campus: {campus_name} | "
                f"Venue: {ev.venue_name} | "
                f"Date: {ev.date.isoformat()} | "
                f"Time: {ev.start_time.strftime('%H:%M')}{end}"
                + (f" | Info: {ev.description}" if ev.description else "")
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are CampusBot, the AI assistant for Campus Explorer — a multi-campus \
navigation and events platform for Amrita Vishwa Vidyapeetham.

Your job is to help students and staff with:
1. Finding events (name, venue, date, time, which campus).
2. Navigating between locations on any campus.
3. General campus information (facilities, hostels, labs, etc.).

Rules:
- Answer ONLY from the live data provided below. Do NOT invent events or locations.
- If the user asks about an event, always mention the campus name and venue.
- If the user asks for directions, describe the route in plain English using the \
  known location names; mention that they can use the interactive map for a visual route.
- Be concise, friendly, and helpful.
- If you don't know something from the data, say so honestly.

--- LIVE DATA (refreshed every request) ---
{context}
--- END OF LIVE DATA ---
"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def get_groq_reply(
    message: str,
    user_context: Optional[dict] = None,
    conversation_history: Optional[list] = None,
) -> str:
    """
    Send `message` to Groq with live campus/event context injected.

    Args:
        message: The user's chat message.
        user_context: Dict with keys like 'campus', 'user_name'.
        conversation_history: List of prior {role, content} dicts (max last 10).

    Returns:
        The assistant's reply string.
    """
    api_key = os.environ.get("GROQ_API_KEY") or current_app.config.get("GROQ_API_KEY")
    if not api_key:
        return (
            "The AI assistant is not configured yet. "
            "Please add GROQ_API_KEY to your .env file."
        )

    try:
        context = _build_context()
        system_prompt = _SYSTEM_PROMPT.format(context=context)

        # Personalise the greeting if we know the user's campus
        campus_hint = ""
        if user_context and user_context.get("campus"):
            campus_hint = (
                f"The user is currently viewing the "
                f"{user_context['campus'].replace('-', ' ').title()} campus. "
            )

        messages: list[dict] = [
            {"role": "system", "content": system_prompt + ("\n" + campus_hint if campus_hint else "")},
        ]

        # Include recent conversation history for multi-turn context
        if conversation_history:
            messages.extend(conversation_history[-10:])  # last 5 exchanges

        messages.append({"role": "user", "content": message})

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            max_tokens=512,
            temperature=0.4,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        current_app.logger.error(f"Groq chat error: {e}")
        return "Sorry, I'm having trouble connecting right now. Please try again in a moment."
