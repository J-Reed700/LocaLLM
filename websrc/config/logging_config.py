import logging
import json
from pythonjsonlogger import jsonlogger
from functools import wraps
import inspect

def setup_enhanced_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s %(extra)s'
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