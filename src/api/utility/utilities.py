# /app.py

import asyncio
import logging
import os
from functools import wraps
from typing import Any, Callable, Dict, Optional
from src.models.pydantic import ModelType, TextModelName, ImageModelName
from src.api.exceptions.exceptions import ModelLoadingError
from aiocache import Cache, cached
from fastapi import Depends, FastAPI, HTTPException, Request, Form


from app import settings, logger, tracer

# Utility Functions
def get_model_and_tokenizer_sync(model_type: ModelType, model_name: str) -> Dict[str, Any]:
    logger.info(f"Loading model and tokenizer for {model_type.value} model: {model_name}")
    try:
        if model_type == ModelType.TEXT:
            return {"model": None, "tokenizer": None}
        elif model_type == ModelType.IMAGE:
            return {"model": None, "tokenizer": None}
    except Exception as e:
        logger.exception("Failed to load model")
        raise ModelLoadingError(f"Error loading model: {str(e)}")

def trace_and_log(
    span_name: str,
    log_message_func: Callable[..., str],
    attributes_func: Optional[Callable[..., Dict[str, Any]]] = None
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                request: Optional[Request] = kwargs.get('request') or (args[0] if args else None)
                form_data = await request.form()
                log_message = log_message_func(form_data)
                attributes = attributes_func(form_data) if attributes_func else {}
                log_and_set_attributes(span, log_message, attributes)
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with tracer.start_as_current_span(span_name) as span:
                request: Optional[Request] = kwargs.get('request') or (args[0] if args else None)
                log_message = log_message_func(request)
                attributes = attributes_func(request) if attributes_func else {}
                log_and_set_attributes(span, log_message, attributes)
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

def log_and_set_attributes(span: Any, log_message: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    logger.info(log_message)
    if attributes:
        span.set_attributes(attributes)

def cache_response(ttl: int = settings.CACHE_TTL):
    def decorator(func: Callable):
        return cached(ttl=ttl, cache=Cache.MEMORY)(func)
    return decorator