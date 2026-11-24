# Level 2: one place for all configuration.
# Values come from environment variables or .env, are validated at startup,
# and every other module asks get_settings() instead of calling os.getenv.
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root (the folder that holds .env), found from this file's location,
# so it works no matter which folder a command is run from.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",  # read values from .env
        extra="ignore",              # ignore unrelated variables in .env
    )

    # Which environment we're running in. A typo (e.g. "prdo") fails at startup.
    environment: Literal["dev", "staging", "prod"] = "dev"

    # Secrets: SecretStr prints as ********** so it can't leak into logs or responses.
    # Read the real value with .get_secret_value().
    database_url: SecretStr  # required: the app refuses to start without it

    # Optional so migrations and DB scripts run without an LLM key;
    # /extract returns a clear 500 error if it's missing (same as Level 1).
    openrouter_api_key: SecretStr | None = None

    # Non-secret settings with defaults; override any of them in .env.
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openrouter/free"
    arxiv_api_base_url: str = "https://export.arxiv.org/api/query"
    
    # Level 3: signs access tokens (JWT). Required: anyone with this key could
    # forge a token for any user, so it lives in .env as a SecretStr.
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"        # HMAC-SHA256: one secret both signs and verifies

    # Level 3: token lifetimes. Short access token (can't be revoked early),
    # long refresh token (stored in the DB, so it can be revoked).
    access_token_minutes: int = 15
    refresh_token_days: int = 7

@lru_cache
def get_settings() -> Settings:
    # Built once on first call, then the same object is reused.
    return Settings()
