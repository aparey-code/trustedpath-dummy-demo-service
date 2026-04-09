"""Cryptographic utilities for token generation and validation."""

import hashlib
import hmac
import secrets


def generate_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


def sha256_hex(data: str) -> str:
    """Return the SHA-256 hex digest of a string."""
    return hashlib.sha256(data.encode()).hexdigest()
