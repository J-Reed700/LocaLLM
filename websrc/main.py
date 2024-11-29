import logging
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

import os

from websrc.api.middleware.telemetry import setup_telemetry
from websrc.api.routes import configuration, frontend, generation, health, conversations
from websrc.api.middleware.error_handlers import base_app_error_handler, generic_exception_handler, validation_exception_handler
from exceptions.exceptions import BaseAppError
from websrc.config.logging_manager import LoggingManager
from src.models.database import Base
from src.db.session import engine
from websrc.api.middleware.logging import RequestLoggingMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

# Initialize logging first
logging_manager = LoggingManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# Initialize FastAPI app
app = FastAPI(
    title="locaLLM Server",
    description="A cutting-edge LLM and Image Generation server with seamless scalability and observability",
    version="1.1",
    lifespan=lifespan
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
app.include_router(generation.router, tags=["Generation"])
app.include_router(health.router, tags=["Health"])
app.include_router(conversations.router, tags=["Conversations"])

# Register error handlers
app.add_exception_handler(BaseAppError, base_app_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Create static directory if it doesn't exist
os.makedirs("websrc/static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="websrc/static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="websrc/templates")

app.add_middleware(RequestLoggingMiddleware)