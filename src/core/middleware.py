from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import Settings
from src.core.exceptions import AppError, ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        issues: list[object] = []

        for err in exc.errors():
            issues.append(
                {
                    "type": err.get("type"),
                    "loc": err.get("loc"),
                    "msg": err.get("msg"),
                    "input": err.get("input"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [],
                "issues": issues,
            },
        )

    @app.exception_handler(ValidationError)
    async def domain_validation_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "issues": exc.issues,
            },
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        body: dict[str, object] = {
            "success": False,
            "code": exc.code,
            "message": exc.message,
        }

        return JSONResponse(status_code=exc.http_status, content=body)


def register_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
