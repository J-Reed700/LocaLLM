from websrc.config.logging_config import LoggerMixin, log_function
import asyncio
import os
from functools import wraps
from typing import Any, Callable, Dict, Optional
from websrc.models.pydantic import ModelType, TextModelName, ImageModelName
from websrc.api.exceptions.exceptions import ModelLoadingError
from websrc.config.settings import settings
from aiocache import Cache, cached
from fastapi import Depends, FastAPI, HTTPException, Request, Form
from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.context.context import Context
from opentelemetry.trace.span import format_span_id, format_trace_id

# Get tracer instance
tracer = trace.get_tracer(__name__)

class Utilities(LoggerMixin):
    @staticmethod
    @log_function
    def get_model_and_tokenizer_sync(model_type: ModelType, model_name: str) -> Dict[str, Any]:
        logger = LoggerMixin().logger
        logger.info(f"Loading model and tokenizer for {model_type.value} model: {model_name}")
        try:
            if model_type == ModelType.TEXT:
                return {"model": None, "tokenizer": None}
            elif model_type == ModelType.IMAGE:
                return {"model": None, "tokenizer": None}
        except Exception as e:
            logger.exception("Failed to load model")
            raise ModelLoadingError(f"Error loading model: {str(e)}")

    @staticmethod
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
                    if request and hasattr(request, 'form'):
                        form_data = await request.form()
                    else:
                        form_data = {}
                    log_message = log_message_func(form_data)
                    attributes = attributes_func(form_data) if attributes_func else {}
                    Utilities.log_and_set_attributes(span, log_message, attributes)
                    return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name) as span:
                    request: Optional[Request] = kwargs.get('request') or (args[0] if args else None)
                    log_message = log_message_func(request)
                    attributes = attributes_func(request) if attributes_func else {}
                    Utilities.log_and_set_attributes(span, log_message, attributes)
                    return func(*args, **kwargs)

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    @log_function
    @staticmethod
    def log_and_set_attributes(span: Any, log_message: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        logger = LoggerMixin().logger
        logger.info(log_message)
        if attributes:
            span.set_attributes(attributes)

    @log_function
    @staticmethod
    def cache_response(ttl: int = 300) -> Callable:
        def decorator(func: Callable) -> Callable:
            return cached(ttl=ttl, cache=Cache.MEMORY)(func)
        return decorator