# Demo Linux Server Monitoring (Local MVP)

Read-only Flask demo for **agentless** live monitoring of Linux servers (CPU, memory, network, ports). Runs locally on the Cursor host — **local demo only, not production**.

**Python:** 3.10+

Docs: [PRD](docs/requirements.md) · [TODO](docs/TODO.md) · [SECURITY](docs/SECURITY.md)

[![CI](https://github.com/yogeshraheja/batch3_cursor_monitoring_application/actions/workflows/ci.yml/badge.svg)](https://github.com/yogeshraheja/batch3_cursor_monitoring_application/actions/workflows/ci.yml)

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set strong SECRET_KEY and ADMIN_PASSWORD (required to seed admin)
python run.py
```

Open **`http://<host>:5777`** → sign in as **`admin`** with the password from `ADMIN_PASSWORD`.

Bind is **`0.0.0.0:5777`** (all interfaces). Use only on trusted/lab networks.

```bash
export FLASK_APP=run.py
flask run --host=0.0.0.0 --port=5777
```

## Verify

- `http://0.0.0.0:5777` or `http://<host-ip>:5777` redirects anonymous users to login.
- After sign-in, dashboard shows **Monitoring — read-only demo**.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Flask session signing. Ephemeral + warning in `APP_ENV=demo` if unset; required otherwise. |
| `ADMIN_PASSWORD` | Used once to seed hashed `admin` user. Weak/placeholder values are refused. `.env` is local-only. |
| `APP_ENV` | `demo` (default) or stricter modes. |
| `DATABASE_URL` | Optional SQLite URL (default under `instance/monitoring.db`). |
| `SSH_STRICT_HOST_KEYS` | `1` = reject unknown SSH hosts; default accept-new for demo. |

**First-run seed:** On startup the app creates tables and inserts `admin` with a Werkzeug password hash if missing. The plaintext password is never stored.

Default username: **`admin`**. Password comes from env — not hard-coded in the repo.

## Add a server

1. Sign in as `admin`.
2. **Servers → Add server**: name, host, SSH port (default 22), username, password **or** key path/content.
3. Reachability is probed after add (`uname -a` over SSH). Status meanings: `reachable`, `failed`, `unknown`.
4. Open a server for live metrics (CPU, memory, cumulative network bytes, listening ports / connection count). Detail page auto-refreshes every **10 seconds**.

The Cursor host must reach the target over SSH. Prefer key path over pasting keys. SSH credentials in SQLite are demo-only — see [SECURITY.md](docs/SECURITY.md).

### Data model (blurb)

- **User:** `username`, `password_hash`
- **Server:** name, host, ssh_port, ssh_username, auth_type, credential fields (sensitive), last_status, last_checked_at, created_at

## Run tests

```bash
source .venv/bin/activate
pytest -q
```

Coverage includes auth, inventory mutations, mocked SSH, and offline metric parsers. Inventory/SSH tests use fake credentials and never print secrets. SSH is mocked so CI stays offline.

## CI

GitHub Actions workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) installs dependencies and runs `pytest` on push/PR. CI sets dummy `SECRET_KEY` / `ADMIN_PASSWORD` via workflow `env` only — no real secrets or SSH keys. There is no deploy job; “deploy” means run locally. CI is verify-only.

## Security notes

- Do not commit `.env`, `*.db`, or private keys.
- Session cookie is `HttpOnly`; CSRF on forms; hashed admin password; SSH command allowlist + timeouts.
- Service is network-reachable on `0.0.0.0:5777` — keep auth enabled; lab networks only.

## Project layout

```
app/                 Flask factory, models, SSH/metrics, routes, templates, static
tests/               Auth, inventory, SSH mocks, metric parsers
.github/workflows/   CI (pytest)
docs/                PRD, TODO, SECURITY
run.py               Local entry point (0.0.0.0:5777)
```
