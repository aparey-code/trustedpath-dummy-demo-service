"""HTTP handlers for authentication endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.login_rate_limiter import get_login_rate_limiter
from conf.settings import LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECS

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

    client_ip = request.client.host if request.client else "unknown"
    limiter = get_login_rate_limiter()

    if limiter.is_limited(client_ip):
        logger.warning(
            "Rate limit exceeded for IP %s — returning 429", client_ip
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    f"Too many failed login attempts. "
                    f"Try again after {LOGIN_WINDOW_SECS // 60} minutes."
                )
            },
            headers={"Retry-After": str(LOGIN_WINDOW_SECS)},
        )

    # TODO: inject db session via dependency; replace the stub below once wired.
    # When the DB session is available the login flow should be:
    #
    #   user = authenticate_user(db, req.username, req.password)
    #   if user is None:
    #       limiter.record_failure(client_ip)
    #       raise HTTPException(status_code=401, detail="Invalid username or password")
    #   limiter.reset(client_ip)
    #   session = create_session(db, user, client_ip, request.headers.get("User-Agent", ""))
    #   return LoginResponse(session_token=session.session_token,
    #                        expires_in=SESSION_TIMEOUT_SECS)
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
