"""SQLAlchemy models for admin user and monitored servers."""

from __future__ import annotations

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    """Single-admin user for the demo."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # Sensitive: Werkzeug password hash only — never store plaintext.
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Server(db.Model):
    """Linux host inventory entry for agentless SSH monitoring."""

    __tablename__ = "servers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    ssh_port = db.Column(db.Integer, nullable=False, default=22)
    ssh_username = db.Column(db.String(120), nullable=False)
    auth_type = db.Column(db.String(20), nullable=False)  # password | key

    # Sensitive demo fields — local SQLite only; never log these values.
    ssh_password = db.Column(db.Text, nullable=True)
    private_key_path = db.Column(db.String(512), nullable=True)
    private_key_content = db.Column(db.Text, nullable=True)

    last_status = db.Column(db.String(40), nullable=True)  # reachable | failed | unknown
    last_checked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def mark_checked(self, status: str) -> None:
        self.last_status = status
        self.last_checked_at = datetime.utcnow()
