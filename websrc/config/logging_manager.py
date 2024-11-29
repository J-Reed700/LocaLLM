from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
import logging
import logging.handlers
import time
import inspect
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from fastapi import HTTPException, Request
from websrc.api.exceptions.exceptions import BaseAppError
from inspect import getmodule
from pydantic import BaseModel

class LoggingManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Initialize root logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.tracer = trace.get_tracer(__name__)
        
        # Remove existing handlers to prevent duplicates
        self.logger.handlers.clear()
        
        # Create JSON formatter
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s '
            '%(pathname)s %(lineno)d %(funcName)s %(request_info)s '
            '%(response_info)s %(trace_id)s %(span_id)s %(thread)s '
            '%(threadName)s %(process)s %(processName)s %(extra_info)s',
            timestamp=True
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # Main application log with rotation
        app_handler = logging.handlers.RotatingFileHandler(
            'app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        app_handler.setFormatter(formatter)
        app_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(app_handler)
        
        # Separate error log
        error_handler = logging.handlers.RotatingFileHandler(
            'error.log',
            maxBytes=10485760,
            backupCount=5
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)
    
    def log_and_trace(self, operation_name=None):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get the module name and create full span name
                module_name = getmodule(func).__name__
                func_name = func.__name__
                span_name = f"{module_name}.{func_name}"

                with self.tracer.start_as_current_span(span_name) as span:
                    # Add the original operation name as an attribute if provided
                    if operation_name:
                        span.set_attribute("operation.name", operation_name)
                    
                    # Add request properties to span
                    for arg_name, arg_value in kwargs.items():
                        if isinstance(arg_value, Request):
                            # Add FastAPI request attributes
                            span.set_attribute("http.method", arg_value.method)
                            span.set_attribute("http.url", str(arg_value.url))
                            span.set_attribute("http.client_ip", arg_value.client.host)
                            
                            # Add headers as attributes
                            for header_name, header_value in arg_value.headers.items():
                                span.set_attribute(f"http.header.{header_name}", header_value)
                        
                        elif isinstance(arg_value, BaseModel):
                            # Add Pydantic model attributes
                            model_dict = arg_value.model_dump()
                            for key, value in model_dict.items():
                                span.set_attribute(f"request.{arg_name}.{key}", str(value))
                        
                        elif arg_name not in ["self", "cls"]:
                            # Add other arguments as attributes
                            span.set_attribute(f"request.{arg_name}", str(arg_value))
                    
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        self._handle_error(span, e)
                        raise
            return wrapper
        return decorator
    
    def _handle_error(self, span: Optional[trace.Span] = None, error: Exception = None, request: Optional[Request] = None):
        """Handle exceptions by logging them and adding error information to the span"""
        if span:
            span.set_status(Status(StatusCode.ERROR))
            span.set_attribute("error.type", type(error).__name__)
            span.set_attribute("error.message", str(error))
            span.record_exception(error)
        
        # Create error context
        error_context = {
            "error": str(error),
            "error_type": type(error).__name__,
            "function": span.name if span else None,
        }
        
        # Add request information if available
        if request:
            error_context["request_path"] = str(request.url)
            error_context["request_method"] = request.method
        
        # Add stack trace for non-HTTP exceptions
        if not isinstance(error, HTTPException) and not isinstance(error, BaseAppError):
            error_context["stack_trace"] = inspect.trace()
        
        # Add status code for HTTP exceptions
        if isinstance(error, HTTPException):
            error_context["status_code"] = error.status_code
            if span:
                span.set_attribute("error.status_code", error.status_code)
        
        self.logger.error(
            f"Error in {span.name if span else 'unknown'}: {str(error)}",
            extra=error_context,
            exc_info=True
        )
    
    def _sanitize_args(self, data: Any) -> Any:
        """Sanitize sensitive data from logs"""
        if isinstance(data, dict):
            return {k: '***' if k.lower() in {'password', 'token', 'secret', 'key'} else self._sanitize_args(v) 
                   for k, v in data.items()}
        return str(data)
    
    def _sanitize_result(self, result: Any) -> str:
        """Safely convert result to string, truncating if too long"""
        try:
            result_str = str(result)
            return result_str[:1000] + '...' if len(result_str) > 1000 else result_str
        except Exception:
            return '<unprintable result>'