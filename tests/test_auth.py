"""Unit tests for sign-in, logout, and route protection."""

from __future__ import annotations

import os

from app.models import User


def test_login_success(client):
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": os.environ["ADMIN_PASSWORD"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Monitoring" in response.data
    assert b"Signed in successfully" in response.data or b"read-only demo" in response.data


def test_login_failure(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_logout(auth_client):
    response = auth_client.post("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_protected_route_redirects_when_anonymous(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in {302, 303}
    assert "/login" in response.headers.get("Location", "")


def test_password_hash_is_not_plaintext(app):
    with app.app_context():
        user = User.query.filter_by(username="admin").one()
        assert user.password_hash != os.environ["ADMIN_PASSWORD"]
        assert user.password_hash.startswith("scrypt:") or user.password_hash.startswith(
            "pbkdf2:"
        )


def test_unauthenticated_inventory_denied(client):
    response = client.get("/servers/", follow_redirects=False)
    assert response.status_code in {302, 303}
    assert "/login" in response.headers.get("Location", "")
