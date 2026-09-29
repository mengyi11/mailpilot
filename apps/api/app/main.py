import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import ErrorResponse, register_exception_handlers
from app.core.logging import configure_logging


logger = logging.getLogger("mailpilot.api")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        responses={
            500: {
                "model": ErrorResponse,
                "description": "Unexpected server error",
            }
        },
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    register_exception_handlers(application)

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started_at = perf_counter()

        response = await call_next(request)
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "environment": settings.app_env,
            },
        )
        return response

    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["system"],
        summary="Check API health",
    )
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service="mailpilot-api",
            version=settings.app_version,
        )

    return application


app = create_app()
