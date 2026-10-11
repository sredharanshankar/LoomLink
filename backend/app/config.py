from __future__ import annotations
from functools import lru_cache
from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: Literal["development", "production", "test"] = "development"
    public_base_url: str = "https://localhost:5173"
    demo_mode: bool = True
    demo_clock_start: str = ""
    mill_timezone: str = "Asia/Kolkata"

    # Database
    database_url: str = "postgresql+psycopg://loomlink:loomlink@db:5432/loomlink"

    # Auth
    jwt_secret: str = "change-me-32-chars-min"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # CORS
    cors_origins: str = "https://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Logging
    log_level: str = "INFO"

    # Ripple / intelligence
    ripple_debounce_ms: int = 500
    llm_provider: Literal["none", "anthropic"] = "none"
    anthropic_api_key: str = ""
    llm_model: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
