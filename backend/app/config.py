import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


_load_local_env()


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    app_name: str = "FedLens API"
    llm_provider: str = "openrouter"
    llm_model: str = ""
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    database_url: str | None = None
    usaspending_base_url: str = "https://api.usaspending.gov"
    cors_origins: str = "http://localhost:4173,http://127.0.0.1:4173"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_name=os.getenv("APP_NAME", "FedLens API"),
        llm_provider=os.getenv("LLM_PROVIDER", "openrouter"),
        llm_model=os.getenv("LLM_MODEL", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        database_url=os.getenv("DATABASE_URL"),
        usaspending_base_url=os.getenv("USASPENDING_BASE_URL", "https://api.usaspending.gov"),
        cors_origins=os.getenv(
            "CORS_ORIGINS",
            "http://localhost:4173,http://127.0.0.1:4173",
        ),
    )
