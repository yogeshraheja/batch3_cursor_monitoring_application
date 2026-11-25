"""Authentication helpers and admin seeding."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from flask import flash, redirect, session, url_for

from app.config import WEAK_ADMIN_PASSWORDS
from app.extensions import db
from app.models import User

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

ADMIN_USERNAME = "admin"


def login_required(view: F) -> F:
    """Redirect anonymous users to the login page."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not session.get("user_id"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def seed_admin_user(admin_password: str | None) -> None:
    """Ensure a single hashed admin user exists.

    Refuses empty/weak passwords from committed samples. Password is never stored
    in plaintext — only a Werkzeug hash is persisted.
    """
    existing = User.query.filter_by(username=ADMIN_USERNAME).first()
    if existing is not None:
        return

    if admin_password is None or admin_password.strip() in WEAK_ADMIN_PASSWORDS:
        raise RuntimeError(
            "ADMIN_PASSWORD is missing or too weak to seed the admin user. "
            "Set a strong ADMIN_PASSWORD in .env (local-only; never commit .env). "
            "Do not use placeholders from .env.example."
        )

    user = User(username=ADMIN_USERNAME)
    user.set_password(admin_password)
    db.session.add(user)
    db.session.commit()
    logger.info("Seeded admin user %r (password stored as hash only).", ADMIN_USERNAME)
