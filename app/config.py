"""Application configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
import secrets
import warnings
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB = _PROJECT_ROOT / "instance" / "monitoring.db"

# Placeholders / weak values refused when seeding admin (never store these).
WEAK_ADMIN_PASSWORDS = frozenset(
    {
        "",
        "password",
        "admin",
        "admin123",
        "123456",
        "secret",
        "change-me",
        "change-me-strong-password",
        "changeme",
        "replace-with-strong-local-password",
        "replace-with-long-random-string",
    }
)


class Config:
    """Base configuration for the monitoring demo."""

    APP_ENV: str = os.environ.get("APP_ENV", "demo").strip().lower() or "demo"
    SECRET_KEY: str | None = os.environ.get("SECRET_KEY") or None
    ADMIN_PASSWORD: str | None = os.environ.get("ADMIN_PASSWORD") or None
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "5777"))

    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{_DEFAULT_DB}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Session cookie hardening (Flask defaults HttpOnly; reinforce explicitly).
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int | None = None

    SSH_CONNECT_TIMEOUT: int = int(os.environ.get("SSH_CONNECT_TIMEOUT", "8"))
    SSH_COMMAND_TIMEOUT: int = int(os.environ.get("SSH_COMMAND_TIMEOUT", "8"))
    # demo: accept-new (AutoAddPolicy). Set SSH_STRICT_HOST_KEYS=1 to reject unknown hosts.
    SSH_STRICT_HOST_KEYS: bool = os.environ.get("SSH_STRICT_HOST_KEYS", "").strip() in {
        "1",
        "true",
        "True",
    }
    LOGIN_FAILURE_DELAY_SECONDS: float = float(
        os.environ.get("LOGIN_FAILURE_DELAY_SECONDS", "0.4")
    )

    @classmethod
    def apply_secret_key(cls, app: Flask) -> None:
        """Set SECRET_KEY from env, or generate an ephemeral key in demo mode."""
        secret_key = os.environ.get("SECRET_KEY") or cls.SECRET_KEY
        if secret_key:
            app.config["SECRET_KEY"] = secret_key
            return

        if cls.APP_ENV == "demo":
            ephemeral = secrets.token_hex(32)
            app.config["SECRET_KEY"] = ephemeral
            message = (
                "SECRET_KEY is not set; using an ephemeral key for local demo. "
                "Sessions will reset on restart. Set SECRET_KEY in .env for stable sessions."
            )
            warnings.warn(message, UserWarning, stacklevel=2)
            logger.warning(message)
            return

        raise RuntimeError(
            "SECRET_KEY environment variable is required when APP_ENV is not 'demo'. "
            "Copy .env.example to .env and set SECRET_KEY to a long random string."
        )

    @classmethod
    def ensure_instance_path(cls, app: Flask) -> None:
        """Create Flask instance folder for SQLite when using the default path."""
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///") and not db_uri.startswith("sqlite:///:memory:"):
            db_path = Path(db_uri.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
