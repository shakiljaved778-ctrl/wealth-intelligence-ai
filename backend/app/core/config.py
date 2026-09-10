"""Application settings, loaded from environment (prefix ``WIA_``)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WIA_", env_file=".env", extra="ignore")

    env: Literal["dev", "staging", "prod"] = "dev"
    api_v1_prefix: str = "/v1"
    project_name: str = "Wealth Intelligence AI"

    # Auth
    secret_key: str = "dev-only-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 30

    # Storage (scaffold ignores these and uses the in-memory repository)
    database_url: str | None = None
    redis_url: str | None = None

    # Data residency / compliance
    default_data_region: Literal["qa", "eu", "global"] = "global"
    allow_personalized_advice: bool = False

    # AI
    llm_provider: str = "stub"
    llm_model: str = "stub-llm-v0"
    llm_api_key: str | None = None

    # Rate limiting (per API key / minute) — enforced in-process for the scaffold
    default_rate_limit_per_min: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
