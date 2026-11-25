# TODO: Demo Linux Server Monitoring (Local MVP)

Small increments for AI-assisted development. Complete items **in order**. Each step includes **security** and **docs**. Keep the demo local (Cursor host); skip production/cloud complexity.

Reference: [requirements.md](./requirements.md)

---

## Phase 0 — Project init + basic UI

### 0.1 Scaffold project

- [x] Create Flask app layout (`app/` or package root, `templates/`, `static/`, `tests/`)
- [x] Add `requirements.txt` (Flask + pinned versions) and `.gitignore` (venv, `__pycache__`, `.env`, `*.db`, keys)
- [x] **Security:** Do not commit secrets; add `.env.example` with placeholders only (`SECRET_KEY`, `ADMIN_PASSWORD`)
- [x] **Docs:** Root `README.md` — what the demo is, Python version, how to create venv and run locally (minimal steps)

### 0.2 Basic UI shell

- [x] Add base layout template (nav, footer, simple attractive CSS)
- [x] Add home/dashboard placeholder page (“Monitoring — read-only demo”)
- [x] Wire Flask route `/` to render the shell
- [x] **Security:** Set `SECRET_KEY` from env (fail clearly if missing in non-demo mode, or generate ephemeral with warning for local demo)
- [x] **Docs:** Note in README how to open `http://<host>:5777`

### 0.3 Local run smoke check

- [x] Confirm app starts with `flask run` / `python -m …` bound to **`0.0.0.0:5777`**
- [x] **Security:** Listen on `0.0.0.0:5777` as required for this demo; document that the service is reachable on the network — use only on trusted/lab networks; keep auth enabled
- [x] **Docs:** One-line “verify” checklist in README (`http://0.0.0.0:5777` or host IP on port 5777)

---

## Phase 1 — Sign-in + unit tests

### 1.1 Config and DB bootstrap

- [x] Add SQLite + minimal config (path under project or temp; configurable)
- [x] Add `User` model: `username`, `password_hash`
- [x] Seed single `admin` user from `ADMIN_PASSWORD` env (hash with Werkzeug)
- [x] **Security:** Never store plaintext admin password; refuse empty/default weak password in committed samples; document that `.env` is local-only
- [x] **Docs:** Document env vars and first-run seed behavior in README

### 1.2 Login / logout UI and session

- [x] Login page (username + password); logout action
- [x] Session-based auth; protect non-login routes (redirect to login)
- [x] Flash clear errors on bad credentials (no user enumeration details)
- [x] **Security:** Use Flask session cookie (`HttpOnly`); CSRF on login form (Flask-WTF or equivalent); constant-time hash verify; rate-limit note (optional simple delay) for demo
- [x] **Docs:** Document default username `admin` and that password comes from env (not hard-coded in repo)

### 1.3 Unit tests for auth

- [x] Add `pytest` + Flask test client fixtures
- [x] Tests: login success, login failure, logout, protected route redirects when anonymous
- [x] **Security:** Assert password hash is not plaintext in DB; assert unauthenticated access denied
- [x] **Docs:** Add “Run tests” section (`pytest`) to README

### 1.4 CI/CD — GitHub Actions (auth baseline)

- [x] Add `.github/workflows/ci.yml`: install deps, run `pytest` on push/PR
- [x] Pin Python version; cache pip if simple
- [x] **Security:** CI uses dummy `SECRET_KEY` / `ADMIN_PASSWORD` via workflow `env` only; never use real secrets; no SSH keys in CI yet
- [x] **Docs:** Short “CI” note in README linking to the workflow

---

## Phase 2 — Server inventory (admin only)

### 2.1 Server model

- [x] Add `Server` model fields per PRD (name, host, ssh_port, ssh_username, auth_type, credential fields, last_status, last_checked_at)
- [x] Migration or `create_all` for demo SQLite
- [x] **Security:** Do not log passwords/keys; keep DB file out of git; mark credential fields as sensitive in code comments
- [x] **Docs:** Document Server fields in `docs/` or README data model blurb

### 2.2 Add server form (admin)

- [x] UI form: name, host, port (default 22), username, auth method (password **or** key)
- [x] Validate required fields server-side; reject bad host/port input
- [x] **Security:** CSRF on form; sanitize/validate host (no shell metacharacters passed to local shell); store SSH password only in local SQLite for demo — document risk; prefer key path over pasting key when possible
- [x] **Docs:** How to add a server (minimal steps)

### 2.3 List + remove servers

- [x] Server list page (name, host, port, last status, last checked)
- [x] Remove server action (POST + confirm)
- [x] **Security:** Mutations only when authenticated as admin; use POST for delete (not GET); CSRF
- [x] **Docs:** Update README inventory section

### 2.4 Inventory tests + CI

- [x] Unit/integration tests: add server, list, delete, reject unauthenticated mutation
- [x] Ensure CI still green
- [x] **Security:** Tests must not print credentials; use fake values
- [x] **Docs:** Mention inventory test coverage briefly

---

## Phase 3 — Agentless SSH collection (foundation)

### 3.1 SSH client wrapper

- [x] Add Paramiko (or equivalent) helper: connect with password or key, timeout, disconnect
- [x] Run a single safe read-only command (e.g. `uname -a`) as connectivity probe
- [x] **Security:** Disable agent forwarding; strict timeouts; never `shell=True` locally; validate inputs; do not echo credentials in exceptions; known_hosts policy documented for demo (accept-new vs reject — pick and document)
- [x] **Docs:** Note that Cursor host must reach target SSH; firewall/SSH prerequisites

### 3.2 Reachability status on list

- [x] On demand or after add: update `last_status` / `last_checked_at`
- [x] Show reachable / failed on list UI
- [x] **Security:** Cap concurrent SSH attempts; short timeout so UI cannot hang indefinitely
- [x] **Docs:** Explain status meanings

### 3.3 SSH unit tests (mocked)

- [x] Mock Paramiko; test success and failure paths without real hosts
- [x] **Security:** Ensure failure messages are generic in UI (no credential leakage)
- [x] **Docs:** How tests mock SSH
- [x] **CI:** Keep tests offline (no real SSH in GitHub Actions)

---

## Phase 4 — Live metrics (read-only)

### 4.1 CPU metrics over SSH

- [x] Collect overall + per-core CPU % via read-only remote commands (`/proc` or equivalent)
- [x] Render on server detail page (read-only)
- [x] **Security:** Allowlist remote commands only; no user-controlled remote command strings
- [x] **Docs:** Document what CPU fields mean

### 4.2 Memory metrics

- [x] Total / used / free or available (bytes + %)
- [x] **Security:** Same allowlisted collectors; handle parse errors safely
- [x] **Docs:** Document memory fields

### 4.3 Network metrics

- [x] Per-interface bytes in/out; label whether rate or cumulative
- [x] **Security:** Bound output size parsed from remote
- [x] **Docs:** Clarify rate vs cumulative in UI + README

### 4.4 Ports + connections

- [x] Listening ports (port, protocol, process/PID if available)
- [x] Active connections summary (keep UI readable)
- [x] **Security:** Read-only remote queries (`ss`/`netstat`); truncate huge outputs; no privilege escalation assumptions beyond SSH user rights
- [x] **Docs:** Document port/connection display limits

### 4.5 Error states

- [x] SSH/timeout/parse failures show clear error on detail page; app stays up
- [x] **Security:** Sanitize error strings shown to UI
- [x] **Docs:** Troubleshooting unreachable hosts (minimal)

### 4.6 Metrics tests + CI

- [x] Unit tests with mocked SSH command outputs for CPU/mem/net/ports
- [x] **Security:** Fixtures contain no real secrets
- [x] **CI:** All metric parsers covered offline in GitHub Actions
- [x] **Docs:** Update acceptance checklist progress

---

## Phase 5 — UX polish (still demo-minimal)

### 5.1 Auto-refresh

- [x] Client-side refresh of metrics every **10 seconds** (meta refresh or light JS fetch)
- [x] **Security:** Refresh only over same-origin authenticated session; no CORS wildcards
- [x] **Docs:** Note 10s interval and that many hosts may feel slow

### 5.2 Read-only UI pass

- [x] Confirm metrics views have no edit controls; inventory mutations only on admin forms
- [x] Visual polish pass on list + detail (still one clear layout)
- [x] **Security:** Final check — CSRF on all POSTs; session login required everywhere except login
- [x] **Docs:** Screenshot or short UI map in README (optional)

---

## Phase 6 — Hardening checklist + CI finalize

### 6.1 Security sweep (demo-appropriate)

- [x] Confirm `.gitignore` covers `.env`, `*.db`, private keys, `venv/`
- [x] Confirm bind address `0.0.0.0` and port `5777`; hashed admin password; no secrets in repo or workflow files
- [x] Confirm SSH command allowlist only; timeouts set
- [x] **Docs:** Add `docs/SECURITY.md` — demo warnings (stored SSH creds, local-only, not for production)

### 6.2 Documentation sweep

- [x] README: quick start, env vars, tests, CI badge/link, link to PRD + this TODO
- [x] Mark completed acceptance criteria in [requirements.md](./requirements.md) when done
- [x] **Security:** README states “local demo only — not production”

### 6.3 CI/CD finalize

- [x] GitHub Actions: lint (optional `ruff`/`flake8`) + `pytest` on push/PR
- [x] Fail CI if tests fail; no deploy job required (local demo)
- [x] **Security:** No SSH private keys or production passwords in Actions secrets for this demo
- [x] **Docs:** Document that “deploy” = run locally; CI is verify-only

---

## Suggested implement order (summary)

1. Phase 0 — init + basic UI  
2. Phase 1 — sign-in + tests + first GitHub Actions workflow  
3. Phase 2 — server inventory  
4. Phase 3 — SSH foundation  
5. Phase 4 — live metrics  
6. Phase 5 — 10s refresh + read-only polish  
7. Phase 6 — security/docs/CI finalize  

Work **one checkbox group at a time**; keep diffs small and tests green before moving on.
