from pydantic_settings import BaseSettings
from typing_extensions import Literal

class Settings(BaseSettings):
    DEBUG: bool = False
    MODEL_TYPE: Literal["text", "image"] = "text"
    MODEL_NAME: str = "falcon-40b-instruct"
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    HONEYCOMB_API_KEY: str
    HONEYCOMB_DATASET: str
    MAX_WORKERS: int = 4
    CACHE_TTL: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = True