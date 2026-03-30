from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APERTURE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    database_url: str = "postgresql+psycopg://aperture:aperture@localhost:5432/aperture"
    redis_url: str = "redis://localhost:6379/0"

    google_places_api_key: str = ""
    ses_region: str = "ap-south-1"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""

    openclaw_command: str = "openclaw"
    openclaw_config: str = ""
    openclaw_status_timeout_seconds: int = 15
    openclaw_agent_timeout_seconds: int = 90
    openclaw_agent_enrichment: str = "lead-enrichment"
    openclaw_agent_contact_discovery: str = "contact-discovery"
    openclaw_agent_site_audit: str = "site-audit"
    openclaw_agent_draft_email: str = "draft-email"
    openclaw_agent_draft_whatsapp: str = "draft-whatsapp"
    openclaw_agent_reply_classifier: str = "reply-classifier"

    outreach_domain: str = "outreach.example.com"
    email_daily_cap: int = 30
    whatsapp_daily_cap: int = 50
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    skip_db_init: bool = False
    openclaw_host_label: str = "agency-openclaw-vps"

    @property
    def openclaw_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        if self.openclaw_config:
            # Current OpenClaw releases resolve the config file from
            # OPENCLAW_CONFIG_PATH; keep OPENCLAW_CONFIG as a fallback for
            # older installs.
            env["OPENCLAW_CONFIG_PATH"] = self.openclaw_config
            env["OPENCLAW_CONFIG"] = self.openclaw_config
        return env


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
