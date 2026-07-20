"""The specialized agents: identity, persona, and lexical routing hints.

`accent` / `emoji` are surfaced to the frontend so each agent keeps a
consistent color across the whole UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Agent:
    id: str
    name: str
    domain: str
    accent: str          # hex, matches the frontend agent palette
    emoji: str
    blurb: str           # shown in the UI roster
    persona: str         # system prompt for this agent
    keywords: tuple[str, ...] = field(default_factory=tuple)


AGENTS: dict[str, Agent] = {
    "billing": Agent(
        id="billing",
        name="Billing",
        domain="billing",
        accent="#10B981",
        emoji="💳",
        blurb="Payments, invoices, subscriptions, refunds",
        persona=(
            "You are the Billing agent for TechMart Electronics. You handle payments, "
            "invoices, subscriptions, and refunds. Be precise about amounts, timelines, "
            "and eligibility. Quote the refund/pricing policy when relevant."
        ),
        keywords=(
            "bill", "billing", "charge", "charged", "payment", "pay", "paid", "invoice",
            "subscription", "premium", "refund", "money", "card", "price", "overcharg",
        ),
    ),
    "technical": Agent(
        id="technical",
        name="Technical",
        domain="technical",
        accent="#3B82F6",
        emoji="🛠️",
        blurb="Login, setup, errors, bugs, installation",
        persona=(
            "You are the Technical Support agent for TechMart Electronics. You handle "
            "login problems, password resets, installation, setup, errors, and bugs. "
            "Give clear numbered troubleshooting steps."
        ),
        keywords=(
            "login", "log in", "sign in", "password", "reset", "install", "setup",
            "error", "bug", "crash", "not working", "broken", "unlock", "locked",
            "update", "connect", "wifi", "driver",
        ),
    ),
    "product": Agent(
        id="product",
        name="Product",
        domain="product",
        accent="#8B5CF6",
        emoji="📦",
        blurb="Features, pricing, comparisons, availability",
        persona=(
            "You are the Product agent for TechMart Electronics. You explain features, "
            "pricing tiers, product comparisons, availability, and warranty coverage. "
            "Be helpful and specific; never invent products not in the knowledge base."
        ),
        keywords=(
            "feature", "features", "spec", "specs", "compare", "comparison", "which",
            "recommend", "available", "in stock", "warranty", "model", "plan", "tier",
        ),
    ),
    "complaint": Agent(
        id="complaint",
        name="Complaint",
        domain="complaint",
        accent="#F43F5E",
        emoji="🚩",
        blurb="Complaints, escalation, dissatisfaction",
        persona=(
            "You are the Complaint Handling agent for TechMart Electronics. You respond "
            "to frustrated or dissatisfied customers with empathy, acknowledge the issue, "
            "and set a clear next step. If the issue is unresolved or severe, escalate to "
            "a human and say so plainly."
        ),
        keywords=(
            "complaint", "complain", "terrible", "awful", "angry", "furious", "worst",
            "unacceptable", "disappointed", "frustrated", "ridiculous", "sue", "escalate",
            "manager", "cancel my", "never again",
        ),
    ),
    "faq": Agent(
        id="faq",
        name="FAQ",
        domain="faq",
        accent="#06B6D4",
        emoji="💬",
        blurb="Policies, general questions, contact info",
        persona=(
            "You are the FAQ agent for TechMart Electronics. You answer general questions "
            "about company policies, shipping, hours, and contact information from the "
            "knowledge base. Keep answers short and friendly."
        ),
        keywords=(
            "hours", "contact", "email", "phone", "where", "policy", "shipping", "deliver",
            "return", "how long", "faq", "help", "support",
        ),
    ),
}

DEFAULT_AGENT = "faq"


def agent_roster() -> list[dict]:
    """Lightweight metadata for the frontend roster."""
    return [
        {
            "id": a.id,
            "name": a.name,
            "domain": a.domain,
            "accent": a.accent,
            "emoji": a.emoji,
            "blurb": a.blurb,
        }
        for a in AGENTS.values()
    ]
