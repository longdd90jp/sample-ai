from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError, EntityNotFoundError, ExternalServiceError, ValidationError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    def _validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    @app.exception_handler(EntityNotFoundError)
    def _not_found_error_handler(_: Request, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    @app.exception_handler(ExternalServiceError)
    def _external_service_error_handler(_: Request, exc: ExternalServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    @app.exception_handler(AppError)
    def _generic_app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

