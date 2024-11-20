import logging
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import os

from websrc.config.settings import Settings
from websrc.api.middleware.telemetry import setup_telemetry
from websrc.api.routes import configuration, frontend, generation, health
from websrc.api.middleware.error_handlers import base_app_error_handler
from websrc.api.exceptions.exceptions import BaseAppError
from websrc.config.logging_config import setup_enhanced_logging
from websrc.services.dependencies import get_llm_generate_service


# Initialize logging first
logger = setup_enhanced_logging()

# Initialize FastAPI app
app = FastAPI(
    title="locaLLM Server",
    description="A cutting-edge LLM and Image Generation server with seamless scalability and observability",
    version="1.1",
)

# Setup middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Setup telemetry with app instance
setup_telemetry(app)

# Register routers with dependencies
app.include_router(configuration.router, tags=["Configuration"])
app.include_router(frontend.router, tags=["Frontend"])
app.include_router(generation.router, tags=["Generation"], dependencies=[Depends(get_llm_generate_service)])
app.include_router(health.router, tags=["Health"])

# Register error handlers
app.add_exception_handler(BaseAppError, base_app_error_handler)

# Initialize templates
templates = Jinja2Templates(directory="src/templates")