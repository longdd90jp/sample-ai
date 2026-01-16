from __future__ import annotations


class AppError(Exception):
    code = "APP_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class ValidationError(AppError):
    code = "VALIDATION_ERROR"


class EntityNotFoundError(AppError):
    code = "ENTITY_NOT_FOUND"


class ExternalServiceError(AppError):
    code = "EXTERNAL_SERVICE_ERROR"

