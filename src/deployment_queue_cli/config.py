"""Configuration settings for the Deployment Queue CLI."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Default paths
CONFIG_DIR = Path.home() / ".config" / "deployment-queue-cli"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"


class Settings(BaseSettings):
    """CLI settings loaded from environment variables."""

    api_url: str = "https://deployments.example.com"
    github_client_id: Optional[str] = None

    # Direct credentials via environment variables
    github_token: Optional[str] = None
    organisation: Optional[str] = None
    username: Optional[str] = None

    # Path to credentials file (overrides default location)
    credentials_file: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="DEPLOYMENT_QUEUE_CLI_",
        env_file=".env",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]
