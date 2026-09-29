from fastapi import FastAPI
from pydantic import BaseModel

from app.core.errors import ErrorResponse, register_exception_handlers


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


def create_app() -> FastAPI:
    application = FastAPI(
        title="MailPilot API",
        version="0.1.0",
        responses={
            500: {
                "model": ErrorResponse,
                "description": "Unexpected server error",
            }
        },
    )

    register_exception_handlers(application)

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
            version=application.version,
        )

    return application


app = create_app()
