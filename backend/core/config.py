"""Central configuration, loaded once from the environment / .env file."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        self.openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_model: str = os.getenv(
            "OPENROUTER_MODEL", "google/gemini-2.0-flash-001"
        ).strip()
        self.openrouter_base_url: str = "https://openrouter.ai/api/v1"
        self.app_url: str = os.getenv("APP_URL", "http://localhost:3000")
        self.app_name: str = os.getenv("APP_NAME", "TechMart Support Switchboard")
        self.database_url: str = os.getenv("DATABASE_URL", "support.db")
        self.resend_api_key: str = os.getenv("RESEND_API_KEY", "").strip()
        self.vectorstore_dir: Path = BACKEND_DIR / os.getenv("VECTORSTORE_DIR", "vectorstore")
        self.knowledge_base_dir: Path = BACKEND_DIR.parent / "knowledge_base"

    @property
    def llm_enabled(self) -> bool:
        """True when a real key is present; otherwise the app runs in demo mode."""
        return bool(self.openrouter_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
