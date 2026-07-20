"""Intent detection + routing: decide which agent(s) handle a query.

Uses the LLM (OpenRouter) for intent when a key is present, and always keeps a
keyword-based fallback so routing works in demo mode and as a safety net.
"""
from __future__ import annotations

from core.config import get_settings
from core.openrouter import chat_json
from agents.registry import AGENTS, DEFAULT_AGENT

VALID = list(AGENTS.keys())

_SYSTEM = (
    "You are the routing brain of a multi-agent customer support system for "
    "TechMart Electronics. Classify the customer's message and pick the specialist "
    "agent(s) that should answer. Available agents:\n"
    "- billing: payments, invoices, subscriptions, refunds\n"
    "- technical: login, password, installation, errors, bugs\n"
    "- product: features, pricing, comparisons, availability, warranty\n"
    "- complaint: frustration, dissatisfaction, escalation\n"
    "- faq: policies, shipping, hours, contact, general questions\n\n"
    "A message can need MORE THAN ONE agent (e.g. 'I paid but Premium is still "
    "locked' -> billing AND technical). Detect frustration -> also include complaint.\n"
    'Respond with JSON only: {"intent": "<short label>", "agents": ["billing", ...], '
    '"escalate": <true|false>, "reason": "<one sentence>"}'
)


def _keyword_route(message: str) -> dict:
    text = message.lower()
    hits: list[tuple[str, int]] = []
    for agent in AGENTS.values():
        n = sum(1 for kw in agent.keywords if kw in text)
        if n:
            hits.append((agent.id, n))
    hits.sort(key=lambda t: t[1], reverse=True)
    agents = [a for a, _ in hits[:2]] or [DEFAULT_AGENT]
    escalate = "complaint" in agents
    intent = agents[0]
    return {
        "intent": intent,
        "agents": agents,
        "escalate": escalate,
        "reason": "Matched on keywords for " + ", ".join(agents) + ".",
    }


def route(message: str) -> dict:
    """Returns {intent, agents:[ids], escalate, reason}. Always valid ids."""
    if not get_settings().llm_enabled:
        return _keyword_route(message)
    try:
        data = chat_json(
            [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": message},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        agents = [a for a in data.get("agents", []) if a in AGENTS]
        if not agents:
            agents = [DEFAULT_AGENT]
        return {
            "intent": str(data.get("intent", agents[0]))[:60],
            "agents": agents[:3],
            "escalate": bool(data.get("escalate", "complaint" in agents)),
            "reason": str(data.get("reason", ""))[:200],
        }
    except Exception:
        return _keyword_route(message)
