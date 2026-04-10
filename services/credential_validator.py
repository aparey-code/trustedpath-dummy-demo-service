"""Input validation for login credentials.

Defence-in-depth notes
----------------------
* The primary protection against SQL injection is the use of parameterised
  queries (SQLAlchemy ORM) in the data layer. The SQL-pattern check here is
  an early-rejection layer that prevents obviously malicious input from ever
  reaching the database, but it MUST NOT be relied on as a substitute for
  parameterisation.
* SQL injection pattern scanning is applied to the username field only.
  Passwords are not checked for injection patterns because password managers
  legitimately generate passwords containing characters such as quotes and
  semicolons; restricting those characters would lock out valid users.
  Passwords are protected by parameterised queries and by the fact that they
  are never interpolated into queries directly.
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuneable limits
# ---------------------------------------------------------------------------

USERNAME_MIN_LEN: int = 1
USERNAME_MAX_LEN: int = 64

PASSWORD_MIN_LEN: int = 8
PASSWORD_MAX_LEN: int = 128  # prevents DoS via slow PBKDF2 on huge inputs

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Strict allowlist for usernames: alphanumeric plus a small set of
# punctuation that is common in email-style and Unix-style usernames.
# Any character outside this set is rejected, which implicitly blocks most
# SQL metacharacters (', ", ;, --, etc.).
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._@-]{1,64}$")

# SQL injection heuristics applied to the username field as defence-in-depth.
# Patterns are matched case-insensitively.  The list targets the most common
# injection primitives; it is intentionally conservative to avoid false
# positives on legitimate usernames that happen to contain short words.
_SQL_INJECTION_RE = re.compile(
    r"""
    --|                     # SQL line comment
    /\*  |  \*/  |          # SQL block comment delimiters
    \bunion\b               |  # UNION-based exfiltration
    \bselect\b              |  # SELECT keyword
    \binsert\b              |  # INSERT keyword
    \bupdate\b              |  # UPDATE keyword
    \bdelete\b              |  # DELETE keyword
    \bdrop\b                |  # DROP keyword
    \btruncate\b            |  # TRUNCATE keyword
    \bexec(?:ute)?\b        |  # EXEC / EXECUTE
    \bcast\s*\(             |  # CAST( function
    \bconvert\s*\(          |  # CONVERT( function
    \bxp_                   |  # extended stored procedures (MSSQL)
    \bor\s+['"\d]           |  # OR '... / OR 1 (boolean injection)
    \band\s+['"\d]             # AND '... / AND 1 (boolean injection)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of a credential validation check.

    Attributes:
        is_valid: True if all checks passed.
        error:    Human-readable reason for rejection, or None on success.
                  Callers should log this value but MUST NOT surface it
                  verbatim in HTTP responses (use a generic message instead).
    """

    is_valid: bool
    error: str | None = None


def validate_login_credentials(username: str, password: str) -> ValidationResult:
    """Validate and sanitize login credentials before authentication.

    Checks performed (in order):
    1. Both values must be plain strings.
    2. Username must match the allowed character allowlist and length bounds.
    3. Username must not contain SQL injection patterns (defence-in-depth).
    4. Password must meet minimum and maximum length requirements.

    Args:
        username: The username supplied by the client.
        password: The plaintext password supplied by the client.

    Returns:
        A :class:`ValidationResult`.  On failure, ``error`` contains a
        diagnostic suitable for logging; callers should return a generic
        HTTP 422 body to avoid leaking which check failed.
    """
    # 1. Type guard — guard against unexpected serialisation quirks
    if not isinstance(username, str) or not isinstance(password, str):
        logger.warning("Non-string credential type received during validation")
        return ValidationResult(False, "Credentials must be plain strings")

    # 2. Username character allowlist + length
    if not _USERNAME_RE.match(username):
        logger.warning(
            "Username failed allowlist check: length=%d leading_char=%r",
            len(username),
            username[:1] if username else "",
        )
        return ValidationResult(
            False,
            "Username must be 1–64 characters and contain only letters, "
            "digits, and the characters . _ @ -",
        )

    # 3. SQL injection patterns in username (defence-in-depth)
    if _SQL_INJECTION_RE.search(username):
        logger.warning(
            "SQL injection pattern detected in username field (length=%d)",
            len(username),
        )
        return ValidationResult(False, "Username contains disallowed patterns")

    # 4. Password length bounds
    pwd_len = len(password)
    if pwd_len < PASSWORD_MIN_LEN:
        logger.warning("Password too short: %d chars", pwd_len)
        return ValidationResult(
            False,
            f"Password must be at least {PASSWORD_MIN_LEN} characters",
        )
    if pwd_len > PASSWORD_MAX_LEN:
        logger.warning("Password too long: %d chars", pwd_len)
        return ValidationResult(
            False,
            f"Password must not exceed {PASSWORD_MAX_LEN} characters",
        )

    return ValidationResult(True)
