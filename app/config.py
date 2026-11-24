"""Application configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
import secrets
import warnings

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Base configuration for the monitoring demo."""

    APP_ENV: str = os.environ.get("APP_ENV", "demo").strip().lower() or "demo"
    SECRET_KEY: str | None = os.environ.get("SECRET_KEY") or None
    # Reserved for Phase 1 seeding; keep present so .env.example stays valid.
    ADMIN_PASSWORD: str | None = os.environ.get("ADMIN_PASSWORD") or None
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "5777"))

    @classmethod
    def apply_secret_key(cls, app: Flask) -> None:
        """Set SECRET_KEY from env, or generate an ephemeral key in demo mode."""
        secret_key = cls.SECRET_KEY
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
