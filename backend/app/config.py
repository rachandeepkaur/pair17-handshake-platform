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

    ollama_model: str = "llama3"
    ollama_host: str = "http://localhost:11434"

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
