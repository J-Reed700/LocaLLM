import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import os

from src.config.settings import Settings
from src.api.middleware.telemetry import setup_telemetry
from src.api.routes import configuration, frontend, generation
from src.api.middleware.error_handlers import base_app_error_handler
from src.api.exceptions.exceptions import BaseAppError
from src.config.logging_config import setup_enhanced_logging


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

# Setup telemetry
setup_telemetry()
FastAPIInstrumentor.instrument_app(app)

# Register routers
app.include_router(configuration.router, tags=["Configuration"])
app.include_router(frontend.router, tags=["Frontend"])
app.include_router(generation.router, tags=["Generation"])

# Register error handlers
app.add_exception_handler(BaseAppError, base_app_error_handler)

# Initialize templates
templates = Jinja2Templates(directory="src/templates")