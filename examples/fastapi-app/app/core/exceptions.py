"""Domain exception hierarchy with HTTP mapping."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(message=f"{resource} '{identifier}' not found.", code="NOT_FOUND", status_code=404)


class ValidationError(AppError):
    """Business rule validation failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422)


async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map domain exceptions to JSON error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
