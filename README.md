# Demo Linux Server Monitoring (Local MVP)

Read-only Flask demo for **agentless** live monitoring of Linux servers (CPU, memory, network, ports). Runs locally on the Cursor host — no cloud services.

**Python:** 3.10+

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; edit SECRET_KEY / ADMIN_PASSWORD
python run.py
```

Open **`http://<host>:5777`** (this machine’s hostname or IP, port **5777**).

Equivalent Flask CLI bind:

```bash
export FLASK_APP=run.py
flask run --host=0.0.0.0 --port=5777
```

## Verify

- Browser loads the shell at `http://0.0.0.0:5777` or `http://<host-ip>:5777` and shows **Monitoring — read-only demo**.

## Security notes

- Do not commit `.env` or real secrets. Use `.env.example` placeholders only.
- `SECRET_KEY` comes from the environment. In `APP_ENV=demo` (default), a missing key gets an ephemeral value with a warning. Outside demo mode, startup fails if `SECRET_KEY` is unset.
- The app listens on **`0.0.0.0:5777`** (all interfaces). Use only on trusted/lab networks; keep authentication enabled (Phase 1+).

## Project layout

```
app/           Flask factory, config, routes, templates, static
tests/         Smoke / unit tests
run.py         Local entry point (0.0.0.0:5777)
docs/          PRD and incremental TODO
```
