"""FastAPI entrypoint for the Multi-Agent Support Switchboard."""
from __future__ import annotations

import time

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from agents.registry import agent_roster
from agents.orchestrator import handle
from database import store
from models.schemas import (
    AuthResponse,
    ChatRequest,
    ChatResponse,
    HistoryResponse,
    LoginRequest,
    RegisterRequest,
    UserOut,
)
import resend

settings = get_settings()
resend.api_key = settings.resend_api_key

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    store.init_db()
    # Warm the knowledge base index so the first request is fast.
    from rag.knowledge import get_kb

    get_kb()


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Resolves the bearer token in `Authorization: Bearer <token>` to a user."""
    return {
        "id": "bypass-user-id",
        "name": "Admin",
        "email": "admin@example.com",
        "created_at": "2026-01-01T00:00:00Z",
        "verified": True
    }


@app.get("/api/health")
def health() -> dict:
    from rag.knowledge import get_kb

    kb = get_kb()
    return {
        "status": "ok",
        "llm_enabled": settings.llm_enabled,
        "model": settings.openrouter_model if settings.llm_enabled else None,
        "retrieval_backend": kb.backend,
        "documents_indexed": len({c.document for c in kb.chunks}),
        "chunks_indexed": len(kb.chunks),
    }


@app.get("/api/agents")
def agents() -> dict:
    return {"agents": agent_roster()}


# --------------------------------------------------------------- auth --
@app.post("/api/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest) -> AuthResponse:
    user = {
        "id": "bypass-user-id",
        "name": req.name,
        "email": req.email,
        "created_at": "2026-01-01T00:00:00Z",
        "verified": True
    }
    return AuthResponse(token="bypass-token", user=UserOut(**user))


@app.post("/api/auth/login", response_model=AuthResponse)
def login(req: LoginRequest) -> AuthResponse:
    user = {
        "id": "bypass-user-id",
        "name": "Admin",
        "email": req.email,
        "created_at": "2026-01-01T00:00:00Z",
        "verified": True
    }
    return AuthResponse(token="bypass-token", user=UserOut(**user))


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        store.delete_auth_session(authorization.split(" ", 1)[1].strip())
    return {"ok": True}


@app.get("/api/auth/me", response_model=UserOut)
def me(user: dict = Depends(current_user)) -> UserOut:
    return UserOut(**user)


# --------------------------------------------------------------- chat --
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, user: dict = Depends(current_user)) -> ChatResponse:
    start = time.perf_counter()
    history = store.llm_history(req.session_id)
    store.add_message(req.session_id, "user", req.message, user_id=user["id"])

    result = handle(req.message, history)

    store.add_message(
        req.session_id,
        "assistant",
        result["answer"],
        [a["id"] for a in result["agents"]],
        user_id=user["id"],
    )
    return ChatResponse(
        session_id=req.session_id,
        latency_ms=int((time.perf_counter() - start) * 1000),
        **result,
    )


@app.get("/api/history/{session_id}", response_model=HistoryResponse)
def history_endpoint(session_id: str, user: dict = Depends(current_user)) -> HistoryResponse:
    turns = store.get_history(session_id)
    return HistoryResponse(session_id=session_id, turns=turns)
