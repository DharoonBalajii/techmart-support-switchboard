"""The orchestrator: route -> retrieve (RAG) -> generate per agent -> aggregate."""
from __future__ import annotations

import re

from core.config import get_settings
from core.openrouter import chat
from agents.registry import AGENTS
from agents.router import route
from rag.knowledge import get_kb, Retrieved


def _context_block(sources: list[Retrieved]) -> str:
    if not sources:
        return "No knowledge-base context was retrieved."
    return "\n\n".join(f"[{s.document}] {s.snippet}" for s in sources)


def _agent_answer(agent_id: str, message: str, history: list[dict], sources: list[Retrieved]) -> str:
    agent = AGENTS[agent_id]
    system = (
        f"{agent.persona}\n\n"
        "Answer ONLY from the knowledge-base context below when it is relevant. "
        "If the context does not contain the answer, say what you can and offer to "
        "escalate to a human — do not invent policies, prices, or facts.\n\n"
        f"--- KNOWLEDGE BASE CONTEXT ---\n{_context_block(sources)}\n--- END CONTEXT ---"
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(history[-6:])  # short conversation memory
    messages.append({"role": "user", "content": message})
    return chat(messages, temperature=0.3, max_tokens=600)


def _clean_snippet(text: str) -> str:
    """Tidy a raw knowledge-base snippet for display (strip md heading hashes)."""
    lines = [re.sub(r"^#{1,6}\s*", "", ln).strip() for ln in text.splitlines()]
    return " ".join(ln for ln in lines if ln)[:240].rstrip()


def _demo_answer(agent_id: str, sources: list[Retrieved]) -> str:
    if sources:
        top = sources[0]
        return (
            f"Here's the most relevant thing I found in **{top.document}**:\n\n"
            f"> {_clean_snippet(top.snippet)}\n\n"
            "_(Demo mode — add your OpenRouter key in `backend/.env` for full "
            "AI-generated answers.)_"
        )
    return (
        "I'd normally answer this with an LLM grounded in our knowledge base. "
        "_(Demo mode — add your OpenRouter key in `backend/.env` to enable live "
        "responses.)_"
    )


def _aggregate(parts: list[tuple[str, str]]) -> str:
    """Combine multiple agents' answers into one reply."""
    if len(parts) == 1:
        return parts[0][1]
    blocks = []
    for agent_id, text in parts:
        agent = AGENTS[agent_id]
        blocks.append(f"{agent.emoji} **{agent.name}**\n{text}")
    return "\n\n".join(blocks)


def handle(message: str, history: list[dict]) -> dict:
    """Full pipeline for one user turn. Returns a dict matching ChatResponse-ish."""
    settings = get_settings()
    kb = get_kb()

    decision = route(message)
    agent_ids: list[str] = decision["agents"]

    # RAG retrieval, scoped to each agent's domain, de-duplicated by snippet.
    seen: set[str] = set()
    all_sources: list[Retrieved] = []
    per_agent_sources: dict[str, list[Retrieved]] = {}
    for aid in agent_ids:
        domain = AGENTS[aid].domain
        got = kb.retrieve(message, k=3, domain=domain)
        per_agent_sources[aid] = got
        for s in got:
            key = f"{s.document}:{s.snippet[:60]}"
            if key not in seen:
                seen.add(key)
                all_sources.append(s)

    parts: list[tuple[str, str]] = []
    for aid in agent_ids:
        srcs = per_agent_sources[aid]
        if settings.llm_enabled:
            try:
                text = _agent_answer(aid, message, history, srcs)
            except Exception as exc:  # network / model error -> graceful note
                text = f"({AGENTS[aid].name} agent hit an error: {exc}). Please try again."
        else:
            text = _demo_answer(aid, srcs)
        parts.append((aid, text))

    answer = _aggregate(parts)

    return {
        "answer": answer,
        "intent": decision["intent"],
        "agents": [
            {
                "id": AGENTS[aid].id,
                "name": AGENTS[aid].name,
                "domain": AGENTS[aid].domain,
                "reason": decision["reason"],
            }
            for aid in agent_ids
        ],
        "sources": [s.__dict__ for s in all_sources[:6]],
        "escalated": bool(decision["escalate"]),
        "demo_mode": not settings.llm_enabled,
    }
