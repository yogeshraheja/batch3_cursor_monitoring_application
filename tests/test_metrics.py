"""Offline parser tests for metric collectors (no real SSH / secrets)."""

from __future__ import annotations

from app.metrics import (
    compute_cpu_percent,
    parse_connection_count,
    parse_listening_ports,
    parse_memory,
    parse_network,
)


def test_parse_memory():
    sample = """
MemTotal:       2048000 kB
MemFree:         512000 kB
MemAvailable:   1024000 kB
""".strip()
    mem = parse_memory(sample)
    assert mem.total_bytes == 2048000 * 1024
    assert mem.available_bytes == 1024000 * 1024
    assert mem.used_bytes == mem.total_bytes - mem.available_bytes
    assert 0 < mem.used_percent < 100


def test_parse_network_cumulative():
    sample = """
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
  eth0: 1000       1    0    0    0     0          0         0 2000       1    0    0    0     0       0          0
    lo: 10         1    0    0    0     0          0         0 10         1    0    0    0     0       0          0
""".strip()
    ifaces = parse_network(sample)
    assert len(ifaces) == 1
    assert ifaces[0].name == "eth0"
    assert ifaces[0].rx_bytes == 1000
    assert ifaces[0].tx_bytes == 2000


def test_compute_cpu_percent():
    first = ((100, 200), [(50, 100), (50, 100)])
    second = ((110, 300), [(55, 150), (55, 150)])
    cpu = compute_cpu_percent(first, second)
    assert 0 <= cpu.overall_percent <= 100
    assert len(cpu.per_core_percent) == 2


def test_parse_listening_and_connections():
    ss = """
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
tcp   LISTEN 0      128    0.0.0.0:22         0.0.0.0:*    users:(("sshd",pid=1,fd=3))
tcp   LISTEN 0      128    127.0.0.1:5777     0.0.0.0:*
""".strip()
    rows = parse_listening_ports(ss)
    assert any(":22" in r.local_address for r in rows)
    assert parse_connection_count("12\n") == 12
