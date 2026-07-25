"""
AstraX AI — Application Configuration
Uses pydantic-settings for environment-based configuration.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ASTRAX_",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AstraX AI"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@db.xxxxxxxxxxxx.supabase.co:5432/postgres"

    # Storage
    data_dir: Path = Path("./data")
    upload_dir: Path = Path("./data/uploads")
    cache_dir: Path = Path("./data/cache")
    export_dir: Path = Path("./data/exports")

    # Processing
    max_workers: int = 4
    gpu_enabled: bool = False
    chunk_size: int = 1024 * 1024 * 10  # 10MB upload chunks

    # Detection Defaults
    detection_fwhm: float = 3.0
    detection_threshold_sigma: float = 5.0
    motion_threshold: float = 2.0
    confidence_threshold: float = 0.5
    noise_sigma_clip: float = 3.0

    # Task Queue
    celery_broker_url: Optional[str] = None  # None = use in-process tasks
    celery_result_backend: Optional[str] = None

    # AI Service
    llm_provider: Optional[str] = None  # gemini, openai, anthropic, openrouter
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None

    # Security
    secret_key: str = "astrax-dev-secret-change-in-production"

    def setup_dirs(self) -> None:
        """Create required directories."""
        for d in [self.data_dir, self.upload_dir, self.cache_dir, self.export_dir]:
            d.mkdir(parents=True, exist_ok=True)


# Singleton
settings = Settings()
