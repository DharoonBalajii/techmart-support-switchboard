"""Thin wrapper around the OpenRouter chat API (OpenAI-compatible).

Every LLM call in the system goes through here, so switching models is a
single env var and demo-mode fallback lives in one place.
"""
from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from core.config import get_settings

_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    global _client
    settings = get_settings()
    if not settings.llm_enabled:
        return None
    if _client is None:
        _client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            default_headers={
                "HTTP-Referer": settings.app_url,
                "X-Title": settings.app_name,
            },
        )
    return _client


def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 700,
    json_mode: bool = False,
) -> str:
    """Run one completion. Returns the assistant text (or a JSON string)."""
    client = _get_client()
    settings = get_settings()
    if client is None:
        raise RuntimeError("LLM disabled: no OPENROUTER_API_KEY configured.")

    kwargs: dict[str, Any] = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def chat_json(messages: list[dict[str, str]], **kwargs: Any) -> dict:
    """Chat call that must return a JSON object; tolerant of code fences."""
    raw = chat(messages, json_mode=True, **kwargs)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(cleaned.strip())
