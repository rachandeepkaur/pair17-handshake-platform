import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


def _format_validation_error(error: dict) -> str:
    field = ".".join(str(part) for part in error.get("loc", []) if part not in ("body", "query", "path"))
    message = error.get("msg", "Invalid value").removeprefix("Value error, ")
    return f"{field}: {message}" if field else message


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    # The frontend renders `detail` as a string, so collapse Pydantic's list
    # of errors into one readable message and keep the full list alongside.
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        return JSONResponse(
            status_code=422,
            content={
                "detail": _format_validation_error(errors[0]) if errors else "Invalid request",
                "errors": [_format_validation_error(error) for error in errors],
            },
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Integrity error on %s: %s", request.url.path, exc.orig)
        return JSONResponse(status_code=409, content={"detail": "This record conflicts with existing data"})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})
