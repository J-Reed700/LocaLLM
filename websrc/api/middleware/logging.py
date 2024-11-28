from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import json
import time
from typing import Callable
from websrc.config.settings import settings

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Extract request body if it exists
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body = body.decode()
            except Exception:
                body = "Could not decode body"

        # Log request details
        logger.info(
            "Incoming request",
            extra={
                "request": {
                    "method": request.method,
                    "url": str(request.url),
                    "client_host": request.client.host if request.client else None,
                    "headers": dict(request.headers),
                    "body": body,
                    "path_params": dict(request.path_params),
                    "query_params": dict(request.query_params),
                }
            }
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception("Unhandled exception during request processing")
            raise  

        # Calculate request duration
        duration = time.time() - start_time
        
        # Log response details
        logger.info(
            "Request completed",
            extra={
                "response": {
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "headers": dict(response.headers)
                }
            }
        )

        return response 