from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import field_validator, validator, Field
from src.models.enum import TextRepoName, ImageRepoName
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Model Settings
    GENMODEL_TYPE: str = os.getenv("MODEL_TYPE", "text")
    GENMODEL_NAME: str = os.getenv("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0") 
    ENABLE_LLM_SERVICE: bool = os.getenv("ENABLE_LLM_SERVICE", "True").lower() == "true"

    @field_validator('GENMODEL_TYPE')
    def validate_model_type(cls, v):
        if v not in ['text', 'image']:
            raise ValueError(f"Invalid model type: {v}")
        return v
    
    @field_validator('GENMODEL_NAME')
    def validate_model_name(cls, v, values):
        model_type = values.data.get('GENMODEL_TYPE')
        if model_type == 'text':
            if not TextRepoName.validate(v):
                raise ValueError(f"Invalid text model name: {v}")
        elif model_type == 'image':
            if not ImageRepoName.validate(v):
                raise ValueError(f"Invalid image model name: {v}")
        return v
    
    # Model Resources Settings
    MODEL_RESOURCES_MAX_MEMORY: str = os.getenv("MODEL_RESOURCES_MAX_MEMORY", "4GB")
    MODEL_RESOURCES_CPU_THREADS: int = int(os.getenv("MODEL_RESOURCES_CPU_THREADS", "4"))
    MODEL_RESOURCES_DEVICE: str = os.getenv("MODEL_RESOURCES_DEVICE", "cpu")
    MODEL_RESOURCES_PRECISION: str = os.getenv("MODEL_RESOURCES_PRECISION", "fp16")
    MODEL_RESOURCES_CONTEXT_LENGTH: int = int(os.getenv("MODEL_RESOURCES_CONTEXT_LENGTH", "2048"))
    MODEL_RESOURCES_BATCH_SIZE: int = int(os.getenv("MODEL_RESOURCES_BATCH_SIZE", "1"))
    
    # Database Settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "locallm")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "locallm")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "localdev")
    DATABASE_URL: Optional[str] = None
    
    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Telemetry Settings
    TELEMETRY_ENABLED: bool = os.getenv("TELEMETRY_ENABLED", "True").lower() == "true"
    JAEGER_AGENT_HOST: str = os.getenv("JAEGER_AGENT_HOST", "localhost")
    JAEGER_AGENT_PORT: int = int(os.getenv("JAEGER_AGENT_PORT", "6831"))
    HONEYCOMB_API_KEY: Optional[str] = os.getenv("HONEYCOMB_API_KEY")
    HONEYCOMB_DATASET: Optional[str] = os.getenv("HONEYCOMB_DATASET")
    OTEL_SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "locaLLM_server")
    OTEL_TRACES_EXPORTER: str = os.getenv("OTEL_TRACES_EXPORTER", "otlp")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    OTEL_EXPORTER_OTLP_PROTOCOL: str = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
    
    # Add these new settings
    TELEMETRY_SDK_NAME: str = os.getenv("TELEMETRY_SDK_NAME", "opentelemetry")
    TELEMETRY_SDK_VERSION: str = os.getenv("TELEMETRY_SDK_VERSION", "1.0.0")
    TELEMETRY_SDK_LANGUAGE: str = os.getenv("TELEMETRY_SDK_LANGUAGE", "python")
    OTLP_ENDPOINT: str = os.getenv("OTLP_ENDPOINT", "http://host.docker.internal:4318/v1/traces")
    
    # Application Settings
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "locaLLM")
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.1.0")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Settings
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    DEFAULT_API_KEY: Optional[str] = os.getenv("DEFAULT_API_KEY")

    # Add these missing fields
    MODEL_TYPE: str = Field(default="text")
    MODEL_NAME: str = Field(default="llama-13b")
    OTEL_EXPORTER_OTLP_INSECURE: bool = Field(default=True)

    # OpenTelemetry settings
    OTEL_SERVICE_NAME: str = Field(default="locaLLM_server")
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: bool = Field(default=True)
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://localhost:4317")
    OTEL_EXPORTER_OTLP_PROTOCOL: str = Field(default="grpc")
    OTEL_EXPORTER_OTLP_INSECURE: bool = Field(default=True)

    # Chat Settings
    CHAT_DEFAULT_MODEL: str = Field(default="falcon-40b-instruct")
    CHAT_MAX_LENGTH: int = Field(default=1000, ge=1, le=2000)
    CHAT_TEMPERATURE: float = Field(default=0.7, ge=0, le=2)
    CHAT_TOP_P: float = Field(default=0.9, ge=0, le=1)
    CHAT_TOP_K: int = Field(default=50, ge=1, le=100)
    CHAT_REPETITION_PENALTY: float = Field(default=1.1, ge=0, le=2)
    CHAT_DEFAULT_SYSTEM_PROMPT: str = Field(default="You are a helpful AI assistant.")

    # Add after line 42
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "models")

    # Add to Settings class
    MODEL_STORAGE_DIR: str = os.getenv("MODEL_STORAGE_DIR", "data/models")
    MODEL_STORAGE_PERMISSIONS: int = 0o700  # Restrictive permissions

    class Config:
        env_file = ".env"
        case_sensitive = True
        protected_namespaces = ()
        extra = "allow"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()