"""DX-RAG configuration — loads all Section 8.1 parameters from environment variables."""

import json
from typing import List, Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from env vars / .env file.

    SEC Section 8.1 — 22 parameters.
    SEC Section 8.2 — secrets via env vars only, never in code.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # --- API Keys (Secret) ---
    DEEPSEEK_API_KEY: Optional[SecretStr] = Field(default=None)
    DASHSCOPE_API_KEY: Optional[SecretStr] = Field(default=None)

    # --- Application ---
    APP_NAME: str = "dx-rag-demo"

    # --- CORS ---
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # --- ChromaDB ---
    CHROMA_COLLECTION: str = "knowledge_chunks"
    CHROMA_PERSIST_DIR: str = "chroma_db"

    # --- Embedding ---
    EMBED_MODEL: str = "models/bge-small-zh-v1.5"

    # --- File Storage ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # --- Chunking ---
    MAX_CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # --- LLM ---
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 2048
    LLM_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 2

    # --- Retrieval ---
    DEFAULT_TOP_K: int = 5
    TOP_K_MIN: int = 1
    TOP_K_MAX: int = 20

    # --- Conversation ---
    MAX_HISTORY_LENGTH: int = 20

    # --- RAG Context ---
    MAX_CONTEXT_CHARS: int = 4000

    # --- File Preview ---
    MAX_PREVIEW_CHARS: int = 5000

    # --- Hybrid Retrieval ---
    MIN_RELEVANCE_SCORE: float = 0.30

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> List[str]:
        """Handle CORS_ORIGINS from env var (JSON, already decoded by pydantic-settings)
        or from programmatic string input (JSON array or comma-separated)."""
        if isinstance(v, list):
            return [str(item) for item in v]
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return list(v)  # type: ignore[return-value]

    def get_deepseek_key(self) -> Optional[str]:
        """Return the plain-text DeepSeek API key, or None."""
        if self.DEEPSEEK_API_KEY is not None:
            return self.DEEPSEEK_API_KEY.get_secret_value()
        return None

    def get_dashscope_key(self) -> Optional[str]:
        """Return the plain-text DashScope API key, or None."""
        if self.DASHSCOPE_API_KEY is not None:
            return self.DASHSCOPE_API_KEY.get_secret_value()
        return None


# Module-level singleton
settings = Settings()


def get_settings() -> Settings:
    """Return the module-level Settings singleton."""
    return settings
