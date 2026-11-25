"""Pytest fixtures for the monitoring demo."""

from __future__ import annotations

import os

import pytest

# Strong dummy values for local/CI tests only — never real secrets.
os.environ.setdefault("APP_ENV", "demo")
os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-not-real")
os.environ.setdefault("ADMIN_PASSWORD", "CiTestAdminPassw0rd!")
os.environ.setdefault("LOGIN_FAILURE_DELAY_SECONDS", "0")


@pytest.fixture()
def app():
    from app import create_app
    from app.extensions import db

    application = create_app(testing=True)
    with application.app_context():
        db.create_all()
        from app.auth import seed_admin_user

        seed_admin_user(os.environ["ADMIN_PASSWORD"])
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": os.environ["ADMIN_PASSWORD"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    return client
