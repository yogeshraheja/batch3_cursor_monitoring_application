"""Smoke tests for Phase 0 shell."""

from __future__ import annotations

from app import create_app


def test_index_renders_placeholder() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Monitoring" in body
    assert "read-only demo" in body
