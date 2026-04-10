"""HTTP handlers for authentication endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    session_token: str
    expires_in: int


class SessionInfo(BaseModel):
    user_id: int
    username: str
    is_mfa_verified: bool
    ip_address: str | None


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request):
    """Authenticate a user and return a session token."""
    from services.auth_service import authenticate_user, create_session
    from conf.settings import SESSION_TIMEOUT_SECS

    # TODO: inject db session via dependency
    raise HTTPException(status_code=501, detail="DB session injection not yet wired")


@router.post("/logout")
async def logout(request: Request):
    """Revoke the current session."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # TODO: inject db session via dependency
    raise HTTPException(status_code=501, detail="DB session injection not yet wired")


@router.get("/session", response_model=SessionInfo)
async def get_session(request: Request):
    """Return info about the current session."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # TODO: inject db session via dependency
    raise HTTPException(status_code=501, detail="DB session injection not yet wired")
