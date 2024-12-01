from fastapi import HTTPException
from typing import Optional

class BaseAppError(Exception):
    def __init__(self, message: str, code: int = 500) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)

class ModelConfigurationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)

class InvalidModelTypeError(ModelConfigurationError):
    def __init__(self, model_type: str) -> None:
        message = f"Invalid model type: {model_type}"
        super().__init__(message)

class InvalidModelNameError(ModelConfigurationError):
    def __init__(self, model_name: str) -> None:
        message = f"Invalid model name: {model_name}"
        super().__init__(message)

class ModelLoadingError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class TextGenerationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class ImageGenerationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class DatabaseError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=503)

class ValidationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=422)

class AuthenticationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=401)

class AuthorizationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=403)

class NotFoundError(BaseAppError):
    def __init__(self, message: str, source_class: Optional[str] = None) -> None:
        error_context = f" (from {source_class})" if source_class else ""
        super().__init__(f"{error_context}{message}", code=404)

class ModelNotFoundError(NotFoundError):
    def __init__(self, model_id: str) -> None:
        message = f"Model with id {model_id} not found"
        super().__init__(message)

class ModelDownloadError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class ConflictError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=409)

class RateLimitError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=429)

class ServiceNotAvailableError(BaseAppError):
    def __init__(self, service_name: str) -> None:
        message = f"{service_name} service is not available"
        super().__init__(message, code=503)

class InvalidRequestError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)

class ResourceNotFoundError(BaseAppError):
    def __init__(self, resource_type: str, resource_id: str) -> None:
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, code=404)

class RequestValidationError(BaseAppError):
    def __init__(self, errors: list) -> None:
        message = "Request validation failed"
        self.errors = errors
        super().__init__(message, code=422)

class DatabaseConnectionError(DatabaseError):
    def __init__(self) -> None:
        super().__init__("Unable to connect to database")

class CacheError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=503)

class ResourceBusyError(BaseAppError):
    def __init__(self, resource: str) -> None:
        message = f"Resource {resource} is currently busy"
        super().__init__(message, code=429)

class ConfigurationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class TextGenerationValidationError(RequestValidationError):
    """Exception raised for validation errors during text generation"""
    def __init__(self, errors: list) -> None:
        super().__init__(errors)

class NotEnoughDiskSpaceError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=507)



