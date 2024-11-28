import logging
import json
from pythonjsonlogger import jsonlogger
from functools import wraps
import inspect
import time
from fastapi import Request
from websrc.api.exceptions.exceptions import BaseAppError
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from typing import Type, Union, Tuple
from fastapi import HTTPException

def setup_enhanced_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s '
        '%(pathname)s %(lineno)d %(funcName)s %(request_info)s %(response_info)s %(extra_info)s',
        timestamp=True
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

class LoggerMixin:
    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

def log_async_function(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        frame = inspect.currentframe()
        class_name = frame.f_back.f_locals.get('self').__class__.__name__ if frame.f_back and 'self' in frame.f_back.f_locals else ''
        
        logger.info(f"Entering {class_name}.{func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Exiting {class_name}.{func.__name__}")
            return result
        except Exception as e:
            span = trace.get_current_span()
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error(f"Error in {class_name}.{func.__name__}: {str(e)}", exc_info=True)
            raise
            
    return wrapper

def log_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        frame = inspect.currentframe()
        class_name = frame.f_back.f_locals.get('self').__class__.__name__ if frame.f_back and 'self' in frame.f_back.f_locals else ''
        
        logger.info(f"Entering {class_name}.{func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Exiting {class_name}.{func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {class_name}.{func.__name__}: {str(e)}", exc_info=True)
            raise
            
    return wrapper

def log_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        request = next(
            (arg for arg in args if isinstance(arg, Request)), 
            kwargs.get('request')
        )
        
        log_data = {
            'request_info': {
                'method': request.method if request else None,
                'url': str(request.url) if request else None,
                'client_host': request.client.host if request and request.client else None,
                'headers': dict(request.headers) if request else None,
            } if request else None,
            'response_info': None,
            'extra_info': {}
        }

        logger.info(f"Entering endpoint {func.__name__}", extra=log_data)
        try:
            response = await func(*args, **kwargs)
            log_data['response_info'] = {'status_code': getattr(response, 'status_code', None)}
            logger.info(f"Exiting endpoint {func.__name__}", extra=log_data)
            return response
        except Exception as e:
            log_data['extra_info']['error'] = str(e)
            logger.exception(f"Error in endpoint {func.__name__}", extra=log_data)
            raise
    
    return wrapper

def track_span_exceptions():
    """
    Decorator to handle exceptions and track them in the current span.
    Automatically handles BaseAppError exceptions with their defined status codes
    and provides a default 500 status code for other exceptions.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseAppError as e:
                span = trace.get_current_span()
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                raise
            except Exception as e:
                span = trace.get_current_span()
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                raise HTTPException(status_code=500, detail=str(e))
        return wrapper
    return decorator