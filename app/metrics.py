"""Allowlisted remote collectors for CPU, memory, network, and ports.

Only fixed command strings are executed remotely — never user-controlled.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.ssh_client import SSHError, connect_client, run_command

if TYPE_CHECKING:
    from flask import Flask

    from app.models import Server

# Hard allowlist — do not interpolate user input into these strings.
CMD_CPU = "cat /proc/stat"
CMD_MEM = "cat /proc/meminfo"
CMD_NET = "cat /proc/net/dev"
CMD_LISTEN = "ss -lntuh 2>/dev/null || netstat -lntuh 2>/dev/null"
CMD_CONN = "ss -Htn state established 2>/dev/null | wc -l"

_MAX_OUTPUT_CHARS = 200_000
_MAX_PORT_ROWS = 80
_MAX_IFACES = 64


@dataclass
class CpuMetrics:
    overall_percent: float
    per_core_percent: list[float] = field(default_factory=list)


@dataclass
class MemoryMetrics:
    total_bytes: int
    used_bytes: int
    available_bytes: int
    used_percent: float


@dataclass
class NetInterface:
    name: str
    rx_bytes: int
    tx_bytes: int


@dataclass
class ListeningPort:
    protocol: str
    local_address: str
    process: str


@dataclass
class HostMetrics:
    cpu: CpuMetrics | None = None
    memory: MemoryMetrics | None = None
    network: list[NetInterface] = field(default_factory=list)
    listening_ports: list[ListeningPort] = field(default_factory=list)
    established_connections: int | None = None
    error: str | None = None


def _truncate(text: str) -> str:
    if len(text) <= _MAX_OUTPUT_CHARS:
        return text
    return text[:_MAX_OUTPUT_CHARS]


def _parse_cpu_snapshot(stat_text: str) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    """Return ((idle, total), [(idle, total), ...]) for overall and per-core lines."""
    overall: tuple[int, int] | None = None
    cores: list[tuple[int, int]] = []
    for line in stat_text.splitlines():
        if not line.startswith("cpu"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        label = parts[0]
        values = [int(x) for x in parts[1:]]
        total = sum(values)
        idle = values[3] if len(values) > 3 else 0
        if label == "cpu":
            overall = (idle, total)
        elif label.startswith("cpu") and label[3:].isdigit():
            cores.append((idle, total))
    if overall is None:
        raise ValueError("missing cpu aggregate")
    return overall, cores


def compute_cpu_percent(
    first: tuple[tuple[int, int], list[tuple[int, int]]],
    second: tuple[tuple[int, int], list[tuple[int, int]]],
) -> CpuMetrics:
    (idle1, total1), cores1 = first
    (idle2, total2), cores2 = second
    total_delta = max(total2 - total1, 1)
    idle_delta = idle2 - idle1
    overall = max(0.0, min(100.0, (1.0 - idle_delta / total_delta) * 100.0))

    per_core: list[float] = []
    for idx, (c_idle2, c_total2) in enumerate(cores2):
        if idx >= len(cores1):
            break
        c_idle1, c_total1 = cores1[idx]
        c_total_delta = max(c_total2 - c_total1, 1)
        c_idle_delta = c_idle2 - c_idle1
        per_core.append(
            max(0.0, min(100.0, (1.0 - c_idle_delta / c_total_delta) * 100.0))
        )
    return CpuMetrics(overall_percent=round(overall, 1), per_core_percent=per_core)


def parse_memory(meminfo: str) -> MemoryMetrics:
    kv: dict[str, int] = {}
    for line in meminfo.splitlines():
        match = re.match(r"^(\w+):\s+(\d+)", line)
        if not match:
            continue
        # Values are kB in /proc/meminfo
        kv[match.group(1)] = int(match.group(2)) * 1024

    total = kv.get("MemTotal", 0)
    available = kv.get("MemAvailable", kv.get("MemFree", 0))
    used = max(total - available, 0)
    used_percent = round((used / total) * 100.0, 1) if total else 0.0
    return MemoryMetrics(
        total_bytes=total,
        used_bytes=used,
        available_bytes=available,
        used_percent=used_percent,
    )


def parse_network(netdev: str) -> list[NetInterface]:
    """Cumulative bytes in/out since boot (not rates)."""
    interfaces: list[NetInterface] = []
    for line in netdev.splitlines()[2:]:
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        name = name.strip()
        if not name or name == "lo":
            continue
        cols = rest.split()
        if len(cols) < 9:
            continue
        interfaces.append(
            NetInterface(
                name=name,
                rx_bytes=int(cols[0]),
                tx_bytes=int(cols[8]),
            )
        )
        if len(interfaces) >= _MAX_IFACES:
            break
    return interfaces


def parse_listening_ports(ss_text: str) -> list[ListeningPort]:
    rows: list[ListeningPort] = []
    for line in ss_text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("netid") or line.lower().startswith("proto"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        protocol = parts[0]
        # ss: Netid State Recv-Q Send-Q Local Address:Port Peer...
        local = parts[4] if len(parts) > 4 and parts[1] in {"LISTEN", "UNCONN"} else parts[3]
        process = parts[-1] if "users:" in line or len(parts) > 5 else ""
        if local in {"Address:Port", "Local"}:
            continue
        rows.append(ListeningPort(protocol=protocol, local_address=local, process=process))
        if len(rows) >= _MAX_PORT_ROWS:
            break
    return rows


def parse_connection_count(text: str) -> int:
    text = text.strip().splitlines()[0] if text.strip() else "0"
    try:
        return int(text)
    except ValueError:
        return 0


def format_bytes(num: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024.0
    return f"{num} B"


def collect_host_metrics(app: Flask, server: Server) -> HostMetrics:
    """Fetch live metrics over SSH. Errors are sanitized for UI display."""
    timeout = int(app.config.get("SSH_COMMAND_TIMEOUT", 8))
    connect_timeout = int(app.config.get("SSH_CONNECT_TIMEOUT", 8))
    strict = bool(app.config.get("SSH_STRICT_HOST_KEYS", False))
    metrics = HostMetrics()

    try:
        client = connect_client(
            server, timeout=connect_timeout, strict_host_keys=strict
        )
    except SSHError as exc:
        metrics.error = str(exc)
        return metrics

    try:
        first_cpu = _parse_cpu_snapshot(_truncate(run_command(client, CMD_CPU, timeout=timeout).stdout))
        # Short sample window for utilization delta
        import time

        time.sleep(0.35)
        second_cpu = _parse_cpu_snapshot(_truncate(run_command(client, CMD_CPU, timeout=timeout).stdout))
        metrics.cpu = compute_cpu_percent(first_cpu, second_cpu)

        mem_out = _truncate(run_command(client, CMD_MEM, timeout=timeout).stdout)
        metrics.memory = parse_memory(mem_out)

        net_out = _truncate(run_command(client, CMD_NET, timeout=timeout).stdout)
        metrics.network = parse_network(net_out)

        listen_out = _truncate(run_command(client, CMD_LISTEN, timeout=timeout).stdout)
        metrics.listening_ports = parse_listening_ports(listen_out)

        conn_out = _truncate(run_command(client, CMD_CONN, timeout=timeout).stdout)
        metrics.established_connections = parse_connection_count(conn_out)
    except (SSHError, ValueError, OSError):
        metrics.error = "Unable to collect metrics from host."
    finally:
        client.close()

    return metrics
