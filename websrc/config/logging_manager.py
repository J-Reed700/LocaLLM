from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
import logging
import time
import inspect
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from fastapi import HTTPException, Request
from websrc.api.exceptions.exceptions import BaseAppError

class LoggingManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        
        # JSON formatter setup with expanded fields
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s '
            '%(pathname)s %(lineno)d %(funcName)s %(request_info)s '
            '%(response_info)s %(trace_id)s %(span_id)s %(thread)s '
            '%(threadName)s %(process)s %(processName)s',
            timestamp=True
        )
        
        # Console handler with custom formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            'app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            'error.log',
            maxBytes=10485760,
            backupCount=5
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
        
        # Initialize tracer
        self.tracer = trace.get_tracer(__name__)
    
    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)
    
    def log_and_trace(
        self,
        span_name: str,
        log_level: int = logging.INFO,
        include_args: bool = False,
        include_result: bool = False,
        exclude_fields: Optional[list] = None
    ):
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(span_name) as span:
                    start_time = time.time()
                    
                    # Extract class name if method
                    frame = inspect.currentframe()
                    try:
                        class_name = (
                            frame.f_back.f_locals.get('self').__class__.__name__
                            if frame and frame.f_back and 'self' in frame.f_back.f_locals
                            else ''
                        )
                    finally:
                        del frame  # Prevent reference cycles
                    
                    # Prepare log context with enhanced metadata
                    log_context = {
                        "function": f"{class_name}.{func.__name__}" if class_name else func.__name__,
                        "trace_id": span.get_span_context().trace_id,
                        "span_id": span.get_span_context().span_id,
                        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    
                    # Add request context if available
                    request = next((arg for arg in args if isinstance(arg, Request)), None)
                    if request:
                        log_context["request_id"] = getattr(request.state, "request_id", None)
                        log_context["client_ip"] = request.client.host
                        log_context["method"] = request.method
                        log_context["path"] = request.url.path
                    
                    if include_args and not exclude_fields:
                        log_context["args"] = self._sanitize_args(args)
                        log_context["kwargs"] = self._sanitize_args(kwargs)
                    
                    try:
                        # Log entry with correlation ID
                        self.logger.log(
                            log_level,
                            f"Entering {log_context['function']}",
                            extra=log_context
                        )
                        
                        result = await func(*args, **kwargs)
                        
                        # Enhanced success logging
                        duration = (time.time() - start_time) * 1000
                        log_context.update({
                            "duration_ms": round(duration, 2),
                            "status": "success"
                        })
                        
                        if include_result:
                            log_context["result"] = self._sanitize_result(result)
                        
                        self.logger.log(
                            log_level,
                            f"Completed {log_context['function']}",
                            extra=log_context
                        )
                        
                        return result
                        
                    except BaseAppError as e:
                        self._handle_error(span, e, log_context, start_time)
                        raise
                    except Exception as e:
                        self._handle_error(span, e, log_context, start_time)
                        if not isinstance(e, HTTPException):
                            raise HTTPException(status_code=500, detail=str(e))
                        raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(span_name) as span:
                    start_time = time.time()
                    log_context = self._prepare_log_context(func, span, args, include_args, exclude_fields)
                    
                    try:
                        self.logger.log(log_level, f"Entering {log_context['function']}", extra=log_context)
                        result = func(*args, **kwargs)
                        self._log_success(log_context, result, start_time, include_result, log_level)
                        return result
                    except Exception as e:
                        self._handle_error(span, e, log_context, start_time)
                        raise
            
            return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _handle_error(self, span: trace.Span, error: Exception, log_context: Dict[str, Any], start_time: float):
        span.set_status(Status(StatusCode.ERROR))
        span.set_attribute("error.type", type(error).__name__)
        span.set_attribute("error.message", str(error))
        span.record_exception(error)
        
        duration = (time.time() - start_time) * 1000
        log_context.update({
            "error": str(error),
            "error_type": type(error).__name__,
            "duration_ms": round(duration, 2),
            "status": "error",
            "stack_trace": inspect.trace()
        })
        
        self.logger.error(
            f"Error in {log_context['function']}: {str(error)}",
            extra=log_context,
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