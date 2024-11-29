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
