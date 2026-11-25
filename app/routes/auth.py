"""Login and logout routes."""

from __future__ import annotations

import time

from flask import Blueprint, current_app, flash, redirect, render_template, session, url_for

from app.auth import login_required
from app.forms import LoginForm
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        username = (form.username.data or "").strip()
        password = form.password.data or ""
        user = User.query.filter_by(username=username).first()
        # Constant-time-ish path: always hash-verify when user exists; delay on failure.
        is_valid = bool(user and user.check_password(password))
        if not is_valid:
            delay = float(current_app.config.get("LOGIN_FAILURE_DELAY_SECONDS", 0.4))
            if delay > 0:
                time.sleep(delay)
            # Generic message — no user enumeration details.
            flash("Invalid username or password.", "error")
            return render_template("login.html", form=form), 401

        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        flash("Signed in successfully.", "success")
        return redirect(url_for("main.index"))

    return render_template("login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.get("/logout")
@login_required
def logout_get():
    """Allow simple logout link; still requires an authenticated session."""
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"))
