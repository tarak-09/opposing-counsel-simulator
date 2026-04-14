from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = Field(default="Opposing Counsel Simulator")
    api_env: str = Field(default="development")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/opposing_counsel"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_collection: str = Field(default="opposing_counsel_evidence")
    file_storage_root: Path = Field(default=Path("storage"))
    upload_max_mb: int = Field(default=25)
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")
    celery_task_always_eager: bool = Field(default=True)
    llm_provider: str = Field(default="openai_compatible")
    llm_api_key: str = Field(default="")
    llm_base_url: str = Field(default="https://api.openai.com/v1")
    llm_model: str = Field(default="gpt-4.1-mini")
    embedding_provider: str = Field(default="openai_compatible")
    embedding_api_key: str = Field(default="")
    embedding_base_url: str = Field(default="https://api.openai.com/v1")
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_dimension: int = Field(default=1536)
    use_rule_based_ai_fallback: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    @property
    def api_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[4]

    @property
    def packages_root(self) -> Path:
        return self.repo_root / "packages"

    @property
    def prompt_root(self) -> Path:
        return self.packages_root / "prompts"

    @property
    def personas_path(self) -> Path:
        return self.packages_root / "personas" / "builtin_personas.json"

    @property
    def sample_data_root(self) -> Path:
        return self.packages_root / "sample-data"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
