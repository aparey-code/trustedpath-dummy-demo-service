"""HTTP handlers for authentication endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from conf.database import get_db_session
from conf.settings import SESSION_TIMEOUT_SECS
from models.session import AuthSession
from services.auth_service import authenticate_user, create_session, revoke_session, validate_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

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


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


def _get_active_session(db: Session, request: Request) -> AuthSession:
    token = _extract_bearer_token(request)
    session = validate_session(db, token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session


@router.post("/login", response_model=LoginResponse)
def login(
    req: LoginRequest,
    request: Request,
    db: Session = Depends(get_db_session),
) -> LoginResponse:
    """Authenticate a user and return a session token."""
    user = authenticate_user(db, req.username, req.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    session = create_session(
        db,
        user,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("User-Agent", ""),
    )
    db.commit()

    return LoginResponse(session_token=session.session_token, expires_in=SESSION_TIMEOUT_SECS)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    db: Session = Depends(get_db_session),
) -> Response:
    """Revoke the current session."""
    token = _extract_bearer_token(request)
    if not revoke_session(db, token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/session", response_model=SessionInfo)
def get_session(
    request: Request,
    db: Session = Depends(get_db_session),
) -> SessionInfo:
    """Return info about the current session."""
    session = _get_active_session(db, request)
    return SessionInfo(
        user_id=session.user_id,
        username=session.user.username,
        is_mfa_verified=session.is_mfa_verified,
        ip_address=session.ip_address,
    )
