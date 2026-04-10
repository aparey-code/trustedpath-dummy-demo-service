"""Application settings loaded from environment variables."""

import os


DB_URL = os.getenv("DATABASE_URL", "sqlite:///./demo.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-in-prod")
SESSION_TIMEOUT_SECS = int(os.getenv("SESSION_TIMEOUT_SECS", "3600"))

# Login rate limiting: block an IP after LOGIN_MAX_FAILURES failures within
# a LOGIN_WINDOW_SECS rolling window. Defaults: 5 failures / 10 minutes.
LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
LOGIN_WINDOW_SECS = int(os.getenv("LOGIN_WINDOW_SECS", "600"))

FEATURE_FLAG_POSTURE_CHECK = os.getenv("FF_POSTURE_CHECK", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
