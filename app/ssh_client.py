"""Agentless SSH helper (Paramiko) for connectivity and allowlisted collectors.

Security notes for this local demo:
- Agent forwarding is disabled.
- Timeouts are enforced on connect and command execution.
- Never use local subprocess shell=True; remote commands are fixed allowlists only.
- Credentials must never be echoed in exceptions or logs.
- Host key policy: accept-new (AutoAddPolicy) by default for demo convenience;
  set SSH_STRICT_HOST_KEYS=1 to reject unknown hosts (RejectPolicy).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import paramiko

if TYPE_CHECKING:
    from app.models import Server

logger = logging.getLogger(__name__)


class SSHError(Exception):
    """Generic SSH failure safe for UI display (no credentials)."""


@dataclass(frozen=True)
class SSHResult:
    stdout: str
    stderr: str
    exit_code: int


def _load_pkey(server: Server) -> paramiko.PKey:
    """Load private key from path or pasted content. Sensitive — do not log."""
    key_data: str | None = None
    if server.private_key_content:
        key_data = server.private_key_content
    elif server.private_key_path:
        with open(server.private_key_path, encoding="utf-8") as handle:
            key_data = handle.read()
    if not key_data:
        raise SSHError("Private key is not configured for this server.")

    last_error: Exception | None = None
    for key_cls in (paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey):
        try:
            return key_cls.from_private_key(io.StringIO(key_data))
        except Exception as exc:  # noqa: BLE001 — try next key type
            last_error = exc
    raise SSHError("Unable to load private key.") from last_error


def connect_client(
    server: Server,
    *,
    timeout: int,
    strict_host_keys: bool,
) -> paramiko.SSHClient:
    """Open an SSH client for the inventory server. Caller must close it."""
    client = paramiko.SSHClient()
    if strict_host_keys:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    else:
        # Demo accept-new: auto-add unknown hosts (not for production).
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs: dict = {
        "hostname": server.host,
        "port": server.ssh_port,
        "username": server.ssh_username,
        "timeout": timeout,
        "allow_agent": False,
        "look_for_keys": False,
        "banner_timeout": timeout,
        "auth_timeout": timeout,
    }

    try:
        if server.auth_type == "password":
            connect_kwargs["password"] = server.ssh_password or ""
        elif server.auth_type == "key":
            connect_kwargs["pkey"] = _load_pkey(server)
        else:
            raise SSHError("Unsupported authentication type.")

        client.connect(**connect_kwargs)
    except SSHError:
        client.close()
        raise
    except Exception as exc:
        client.close()
        logger.info("SSH connect failed for host_id=%s: %s", server.id, type(exc).__name__)
        raise SSHError("Unable to reach host over SSH.") from exc

    return client


def run_command(
    client: paramiko.SSHClient,
    command: str,
    *,
    timeout: int,
) -> SSHResult:
    """Execute a single remote command with a timeout."""
    try:
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        return SSHResult(stdout=out, stderr=err, exit_code=exit_code)
    except Exception as exc:
        logger.info("SSH command failed: %s", type(exc).__name__)
        raise SSHError("Remote command failed or timed out.") from exc


def probe_connectivity(
    server: Server,
    *,
    timeout: int,
    strict_host_keys: bool,
) -> str:
    """Run a safe read-only probe (`uname -a`). Returns 'reachable' or raises SSHError."""
    client = connect_client(
        server, timeout=timeout, strict_host_keys=strict_host_keys
    )
    try:
        result = run_command(client, "uname -a", timeout=timeout)
        if result.exit_code != 0:
            combined = f"{result.stdout} {result.stderr}".lower()
            if "not available" in combined or "nologin" in combined:
                raise SSHError(
                    "SSH authenticated, but the account shell cannot run commands "
                    "(often /usr/sbin/nologin). Use a user with a login shell "
                    "(e.g. /bin/bash), or change this account's shell."
                )
            raise SSHError("Connectivity probe failed.")
        return "reachable"
    finally:
        client.close()
