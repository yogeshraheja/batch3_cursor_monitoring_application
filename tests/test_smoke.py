"""Smoke tests for authenticated shell."""

from __future__ import annotations


def test_index_requires_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in {302, 303}


def test_index_renders_after_login(auth_client):
    response = auth_client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Monitoring" in body
    assert "read-only demo" in body
