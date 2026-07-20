"""Pydantic request/response models — the contract the frontend relies on."""
from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    value = value.strip().lower()
    if not _EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address.")
    return value


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    email: str
    password: str = Field(..., min_length=8, max_length=128)

    _validate = field_validator("email")(_validate_email)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=1, max_length=128)

    _validate = field_validator("email")(_validate_email)


class VerifyRequest(BaseModel):
    email: str
    code: str

    _validate = field_validator("email")(_validate_email)


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: str
    verified: bool = False


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated conversation id.")
    message: str = Field(..., min_length=1)


class Source(BaseModel):
    document: str
    snippet: str
    score: float


class AgentTrace(BaseModel):
    id: str
    name: str
    domain: str
    reason: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    intent: str
    agents: list[AgentTrace]
    sources: list[Source]
    escalated: bool = False
    latency_ms: int = 0
    demo_mode: bool = False


class Turn(BaseModel):
    role: str
    content: str
    agents: list[str] = []
    created_at: str


class HistoryResponse(BaseModel):
    session_id: str
    turns: list[Turn]
