from fastapi import APIRouter, Depends, Request
from sqlalchemy.engine import make_url

from core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/")
def home():
    return {"message": "Welcome to Synth"}


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/config-check")
def config_check(request: Request, settings: Settings = Depends(get_settings)):
    """Which environment and settings are active. Never returns secret values."""
    # Parse the DB URL so we can show where it points without the password.
    db_url = make_url(settings.database_url.get_secret_value())
    api_key = settings.openrouter_api_key

    return {
        "environment": settings.environment,
        "version": request.app.version,
        "database": {
            "driver": db_url.drivername,
            "host": db_url.host,
            "port": db_url.port,
            "name": db_url.database,
            # user and password are deliberately left out
        },
        "llm": {
            "model": settings.llm_model,
            "base_url": settings.openrouter_base_url,
            # Only whether a key is set, never the key itself.
            "api_key_configured": api_key is not None and bool(api_key.get_secret_value()),
        },
        "arxiv_api_base_url": settings.arxiv_api_base_url,
                # Level 3: token settings, but never the signing key itself.
        "auth": {
            "jwt_algorithm": settings.jwt_algorithm,
            "access_token_minutes": settings.access_token_minutes,
            "refresh_token_days": settings.refresh_token_days,
            "jwt_secret_key_configured": bool(settings.jwt_secret_key.get_secret_value()),
        },
    }
