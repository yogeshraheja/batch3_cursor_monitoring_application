"""SSH helper tests with Paramiko mocked (offline)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.ssh_client import SSHError, probe_connectivity, run_command


def _fake_server(**overrides):
    base = {
        "id": 1,
        "host": "10.0.0.9",
        "ssh_port": 22,
        "ssh_username": "monitor",
        "auth_type": "password",
        "ssh_password": "fake-password",
        "private_key_path": None,
        "private_key_content": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_probe_success():
    mock_client = MagicMock()
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"Linux demo 6.8\n"
    mock_stdout.channel.recv_exit_status.return_value = 0
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    mock_client.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

    with patch("app.ssh_client.paramiko.SSHClient", return_value=mock_client):
        status = probe_connectivity(
            _fake_server(), timeout=2, strict_host_keys=False
        )
    assert status == "reachable"
    mock_client.connect.assert_called_once()
    assert mock_client.connect.call_args.kwargs.get("allow_agent") is False


def test_probe_failure_is_generic():
    mock_client = MagicMock()
    mock_client.connect.side_effect = Exception("auth failed for user secret=xyz")

    with patch("app.ssh_client.paramiko.SSHClient", return_value=mock_client):
        with pytest.raises(SSHError) as exc_info:
            probe_connectivity(_fake_server(), timeout=2, strict_host_keys=False)

    message = str(exc_info.value)
    assert "secret" not in message
    assert "xyz" not in message
    assert "Unable to reach host" in message


def test_run_command_timeout_generic():
    mock_client = MagicMock()
    mock_client.exec_command.side_effect = TimeoutError("timed out")
    with pytest.raises(SSHError) as exc_info:
        run_command(mock_client, "uname -a", timeout=1)
    assert "timed out" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()
    assert "password" not in str(exc_info.value).lower()
