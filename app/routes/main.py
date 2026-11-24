"""Public shell routes for the monitoring demo."""

from __future__ import annotations

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index() -> str:
    """Home / dashboard placeholder."""
    return render_template("index.html")
