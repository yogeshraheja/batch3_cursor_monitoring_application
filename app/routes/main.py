"""Dashboard routes."""

from __future__ import annotations

from flask import Blueprint, render_template

from app.auth import login_required
from app.models import Server

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
@login_required
def index():
    """Home / dashboard — read-only overview of inventory."""
    servers = Server.query.order_by(Server.name.asc()).all()
    return render_template("index.html", servers=servers)
