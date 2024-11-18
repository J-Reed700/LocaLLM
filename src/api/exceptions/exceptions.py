class BaseAppError(Exception):
    def __init__(self, message: str, code: int = 500) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)

class ModelConfigurationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)

class InvalidModelTypeError(ModelConfigurationError):
    pass

class InvalidModelNameError(ModelConfigurationError):
    pass

class ModelLoadingError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class TextGenerationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)

class ImageGenerationError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=500)


