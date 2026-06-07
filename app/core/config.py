from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "citywalk"
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_PROXY: str = ""
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
