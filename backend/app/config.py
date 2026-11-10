from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> project root is two levels up from backend/
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    pair: int = 17
    port_base: int = 9170
    db_prefix: str = "p17"
    seed: int = 17
    city_set: str = ""

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "p17_handshake"

    jwt_secret: str = "data260Lab1"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # qwen3 supports Ollama's native tool-calling format used by the assistant.
    ollama_model: str = "qwen3:8b"
    ollama_host: str = "http://localhost:11434"
    # On CPU-only machines an 8B model can need over a minute for a long answer.
    ollama_timeout_seconds: float = 360.0
    # Tool schemas + system prompt take ~1.2k tokens; 8k leaves room for follow-ups.
    ollama_num_ctx: int = 8192

    # Containerized deployment (Lab 2). Defaults keep the local monolith working.
    service_name: str = "monolith"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:9170"
    # Empty means "not configured": the health check skips that dependency.
    mongo_uri: str = ""
    mongo_db: str = "p17_handshake"
    kafka_bootstrap_servers: str = ""
    # Platform services the assistant depends on, as "name=url" pairs separated by commas.
    platform_service_urls: str = ""
    health_timeout_seconds: float = 2.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def platform_services(self) -> dict[str, str]:
        pairs = (item.split("=", 1) for item in self.platform_service_urls.split(",") if "=" in item)
        return {name.strip(): url.strip().rstrip("/") for name, url in pairs if name.strip() and url.strip()}

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cities(self) -> list[str]:
        return [city.strip() for city in self.city_set.split(",") if city.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
