# PRD: Demo Linux Server Monitoring (Local MVP)

## 1. Overview

Local demo web app for **agentless** live monitoring of Linux servers. Internal teams (L1 / L2 / L3, infra and app) can view CPU, memory, network, and port usage in a browser instead of SSH-ing into hosts.

**Scope:** Demo only. Runs where Cursor is running (localhost). No production hardening, HA, or multi-tenant design.

## 2. Problem

Today, operators must log into each Linux server to inspect real-time memory, CPU, network, and port usage. That is slow and inconsistent across teams.

## 3. Goals

- Single Flask UI to view live Linux host metrics (read-only for viewers).
- Admin can add/remove Linux servers (SSH-based collection).
- Metrics refresh every **10 seconds**.
- Minimal local setup; no external cloud services.

## 4. Non-Goals (Out of Scope)

- Alerting / thresholds / email / Slack
- Historical charts or long-term metrics storage
- Windows / non-Linux hosts
- Role-based access (L1 vs L2 vs L3)
- Agents, Docker/K8s monitoring, auto-discovery
- Multi-user accounts beyond one admin

## 5. Users & Access

| Role | Who | Capabilities |
|------|-----|----------------|
| Admin | Single built-in user (`admin`) | Sign in, add/remove servers, view all metrics |
| Viewer | Same session after login (demo) | View dashboards only; no inventory changes |

- Sign-in: username **`admin`** + password verified against a **hashed** store (e.g. Werkzeug/passlib).
- One admin account for MVP; no self-registration.
- Logout required.
- UI is **read-only** for metrics and dashboards; only admin actions mutate server inventory.

## 6. Features

### 6.1 Sign-in

- Login page with username + password.
- Default user: `admin` with hashed password (seeded at first run or via env/config).
- Protect all monitoring and inventory routes; redirect unauthenticated users to login.

### 6.2 Server inventory (admin)

Admin can add a Linux server with:

| Field | Required | Notes |
|-------|----------|--------|
| Display name | Yes | Human-friendly label |
| Host | Yes | Hostname or IP |
| SSH port | Yes | Default `22` |
| SSH username | Yes | |
| Auth method | Yes | Password **or** private key |
| Password | If password auth | Stored for SSH use (demo; local DB only) |
| Private key path / content | If key auth | Path on the Cursor host or pasted key |

Admin can **remove** a server from monitoring.

List view shows: name, host, port, last reachability status, last check time.

### 6.3 Live metrics (read-only UI)

For each reachable server, show (auto-refresh **every 10 seconds**):

**CPU**

- Overall utilization (%)
- Per-core utilization (%)

**Memory**

- Total, used, free/available (bytes and %)

**Network**

- Per interface: bytes in / bytes out (rates or cumulative since last sample — pick one and label clearly)

**Ports**

- Listening ports (port, protocol, process/PID if available)
- Active connections summary (counts and/or notable rows; keep UI readable)

Unreachable / SSH failure: show clear error state on that server card/detail page; do not crash the app.

### 6.4 UI

- Flask-rendered front end; clean, attractive, usable on desktop.
- Server list → server detail (metrics).
- Layout/theme left to implementer; must feel intentional (not bare default forms only).
- No write actions on metric views.

## 7. Technical Approach

| Area | Choice |
|------|--------|
| Language | Python 3 |
| Web | Flask (server-rendered HTML + light JS for 10s refresh) |
| Collection | **Agentless** over SSH from the app host |
| Persistence | Local DB (SQLite is enough) for admin user + server inventory |
| Secrets | Hash admin password; store SSH credentials only for local demo |
| Deploy | Local process on the machine where Cursor runs |
| Bind | **`0.0.0.0:5777`** (all interfaces, port 5777) |

Suggested collection: open SSH session, run safe read-only commands (e.g. via `psutil` remotely is not available — use standard Linux tools such as `/proc`, `ss`/`netstat`, `free`, etc., or a small remote one-liner). Prefer Paramiko (or equivalent) from Python.

## 8. Data Model (minimal)

- **User:** id, username, password_hash
- **Server:** id, name, host, ssh_port, ssh_username, auth_type, password_encrypted_or_plain_demo, private_key_ref, created_at, last_status, last_checked_at

Metrics are **live** (fetched on demand / on refresh interval), not historically archived.

## 9. Local Run (minimal)

1. Create venv, install dependencies from `requirements.txt`.
2. Set optional env (e.g. `SECRET_KEY`, `ADMIN_PASSWORD` for initial hash).
3. Initialize DB / seed `admin`.
4. Run app bound to **`0.0.0.0`** on port **`5777`** (e.g. `flask run --host=0.0.0.0 --port=5777` or equivalent in `app.py`).
5. Open browser at `http://<host>:5777` → login as `admin` → add a reachable Linux host → view metrics.

Target hosts must accept SSH from the Cursor machine with the credentials provided.

## 10. Acceptance Criteria

- [ ] Unauthenticated user cannot see metrics or inventory.
- [ ] `admin` logs in with hashed-password verification.
- [ ] Admin can add a Linux server (host, port, user, password or key).
- [ ] Admin can remove a server.
- [ ] Detail view shows CPU (overall + per-core), memory, network per interface, listening ports + connection info.
- [ ] UI refreshes metrics about every 10 seconds.
- [ ] SSH/connection failures are shown without breaking the app.
- [ ] App runs locally with SQLite (or equivalent) and no cloud dependencies.
- [ ] App listens on `0.0.0.0:5777`.
- [ ] Metrics views have no edit/write controls.

## 11. Risks & Demo Notes

- SSH latency may make a full 10s refresh feel tight on many hosts; keep per-host fetch bounded/timeouts short.
- Storing SSH passwords locally is acceptable **only** for this demo.
- Live metrics require real network path and valid credentials to target Linux servers.
- Binding to `0.0.0.0:5777` exposes the UI on all interfaces — use only on trusted/lab networks; authentication remains required.
