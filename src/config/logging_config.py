import logging
import inspect
import asyncio
from typing import Optional
from functools import wraps

def setup_enhanced_logging():
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(class_name)s.%(method_name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Create file handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    return root_logger

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
            logger.error(f"Error in {class_name}.{func.__name__}: {str(e)}", exc_info=True)
            raise
            
    return wrapper