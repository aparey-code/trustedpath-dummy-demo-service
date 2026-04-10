"""Application factory for the demo service."""

from fastapi import FastAPI

from handlers.audit_handler import router as audit_router
from handlers.auth_handler import router as auth_router
from handlers.device_handler import router as device_router
from handlers.health_handler import router as health_router
from handlers.policy_handler import router as policy_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Trustedpath Demo Service",
        description="A demo microservice for auth, device management, and posture evaluation.",
        version="0.1.0",
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(device_router)
    app.include_router(policy_router)
    app.include_router(audit_router)

    return app
