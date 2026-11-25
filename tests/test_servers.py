"""Inventory add / list / delete tests (fake credentials only)."""

from __future__ import annotations

from unittest.mock import patch

from app.extensions import db
from app.models import Server


def test_add_list_delete_server(auth_client, app):
    with patch("app.routes.servers.probe_connectivity", return_value="reachable"):
        add_resp = auth_client.post(
            "/servers/add",
            data={
                "name": "lab-box",
                "host": "10.0.0.50",
                "ssh_port": 22,
                "ssh_username": "monitor",
                "auth_type": "password",
                "ssh_password": "fake-ssh-password-not-real",
                "private_key_path": "",
                "private_key_content": "",
            },
            follow_redirects=True,
        )
    assert add_resp.status_code == 200
    assert b"lab-box" in add_resp.data

    list_resp = auth_client.get("/servers/")
    assert list_resp.status_code == 200
    assert b"10.0.0.50" in list_resp.data

    with app.app_context():
        server = Server.query.filter_by(name="lab-box").one()
        server_id = server.id

    del_resp = auth_client.post(
        f"/servers/{server_id}/delete",
        follow_redirects=True,
    )
    assert del_resp.status_code == 200
    with app.app_context():
        assert db.session.get(Server, server_id) is None


def test_reject_unauthenticated_mutation(client):
    response = client.post(
        "/servers/add",
        data={
            "name": "nope",
            "host": "10.0.0.1",
            "ssh_port": 22,
            "ssh_username": "root",
            "auth_type": "password",
            "ssh_password": "fake",
        },
        follow_redirects=False,
    )
    assert response.status_code in {302, 303}
    assert "/login" in response.headers.get("Location", "")


def test_reject_bad_host(auth_client):
    response = auth_client.post(
        "/servers/add",
        data={
            "name": "evil",
            "host": "host;rm -rf /",
            "ssh_port": 22,
            "ssh_username": "root",
            "auth_type": "password",
            "ssh_password": "fake",
        },
    )
    assert response.status_code == 200
    assert b"shell metacharacters" in response.data or b"Host must be" in response.data
