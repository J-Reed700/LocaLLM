from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any
from websrc.config.logging_manager import LoggingManager
import time
import logging

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logging_manager = LoggingManager()
    
    async def dispatch(self, request: Request, call_next: Callable):
        with self.logging_manager.tracer.start_as_current_span("http_request") as span:
            return await self._handle_request(request, call_next, span)
    
    async def _handle_request(self, request: Request, call_next: Callable, span):
        start_time = time.time()
        
        # Log request
        request_info = await self._get_request_info(request)
        self.logging_manager.logger.info(
            "Incoming request",
            extra={"request": request_info}
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            duration = (time.time() - start_time) * 1000
            self.logging_manager.logger.info(
                "Request completed",
                extra={
                    "response": {
                        "status_code": response.status_code,
                        "duration_ms": round(duration, 2),
                        "headers": dict(response.headers)
                    }
                }
            )
            
            return response
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logging_manager._handle_error(
                span=span,
                error=e,
                log_context={
                    "request": request_info,
                    "function": f"{request.method} {request.url.path}"
                },
                start_time=start_time
            )
            raise

    async def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract relevant request information for logging"""
        info = {
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "headers": dict(request.headers),
            "path_params": dict(request.path_params),
            "query_params": dict(request.query_params)
        }

        # Only attempt to get body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                info["body"] = body.decode() if body else None
            except Exception:
                info["body"] = "Could not decode body"

        return info