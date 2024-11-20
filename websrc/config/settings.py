from pydantic_settings import BaseSettings
from typing_extensions import Literal
from typing import Optional

class Settings(BaseSettings):
    DEBUG: bool = False
    MODEL_TYPE: Literal["text", "image"] = "text"
    MODEL_NAME: str = "falcon-40b-instruct"
    ENABLE_LLM_SERVICE: bool = True
    
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "locallm"
    POSTGRES_USER: str = "locallm"
    POSTGRES_PASSWORD: str = "localdev"
    DATABASE_URL: Optional[str] = None
    
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None
    
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    HONEYCOMB_API_KEY: Optional[str] = None
    HONEYCOMB_DATASET: Optional[str] = None
    MAX_WORKERS: int = 4
    CACHE_TTL: int = 300

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()