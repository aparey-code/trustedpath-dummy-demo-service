"""Authentication service handling login, MFA verification, and session management."""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User
from models.session import AuthSession
from conf.settings import SESSION_TIMEOUT_SECS

logger = logging.getLogger(__name__)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with PBKDF2-SHA256. Returns (hash, salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations=600_000)
    return dk.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash."""
    computed, _ = hash_password(password, salt)
    return secrets.compare_digest(computed, stored_hash)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Validate credentials and return user if valid."""
    stmt = select(User).where(User.username == username, User.is_active.is_(True))
    user = db.execute(stmt).scalar_one_or_none()

    if user is None:
        logger.warning("Login attempt for unknown user: %s", username)
        return None

    parts = user.hashed_password.split("$")
    if len(parts) != 2:
        logger.error("Malformed password hash for user %s", username)
        return None

    salt, stored_hash = parts
    if not verify_password(password, stored_hash, salt):
        logger.warning("Invalid password for user: %s", username)
        return None

    user.last_login_at = datetime.now(timezone.utc)
    return user


def create_session(db: Session, user: User, ip_address: str, user_agent: str) -> AuthSession:
    """Create a new authenticated session for a user."""
    token = secrets.token_urlsafe(48)
    session = AuthSession(
        session_token=token,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=SESSION_TIMEOUT_SECS),
    )
    db.add(session)
    db.flush()
    logger.info("Session created for user %s from %s", user.username, ip_address)
    return session


def validate_session(db: Session, token: str) -> AuthSession | None:
    """Look up and validate a session token."""
    stmt = select(AuthSession).where(AuthSession.session_token == token)
    session = db.execute(stmt).scalar_one_or_none()

    if session is None:
        return None
    if not session.is_valid:
        logger.info("Expired/revoked session access attempt: %s", token[:12])
        return None

    return session


def revoke_session(db: Session, token: str) -> bool:
    """Revoke an active session (logout)."""
    session = validate_session(db, token)
    if session is None:
        return False

    session.revoked_at = datetime.now(timezone.utc)
    logger.info("Session revoked for user_id=%d", session.user_id)
    return True
