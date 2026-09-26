"""Application settings, loaded from environment variables or backend/.env.

Why a settings class instead of reading os.environ everywhere:
- One place lists every setting the app needs.
- Pydantic validates types and fails at startup if something is missing,
  instead of crashing later in the middle of a request.
- Secrets (the API key) stay out of the source code and out of Git.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Field names map to env variables case-insensitively:
    # anthropic_api_key <- ANTHROPIC_API_KEY, and so on.

    # Required: no default, so the app refuses to start without them.
    anthropic_api_key: str
    claude_model: str

    # Comma-separated list of frontend URLs allowed to call the API (CORS).
    # Default = Vite dev server. In production, set the real Vercel domain.
    cors_origins: str = "http://localhost:5173"

    # Path is relative to where uvicorn is started (the backend/ folder).
    # Real environment variables override values in .env, which is how
    # Render will inject secrets later.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        """Split the comma-separated string into a clean list of URLs."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return one shared Settings instance.

    lru_cache means .env is read once, not on every call.
    """
    return Settings()
