# Security notes (local demo only)

This application is a **local lab/demo**, not a production monitoring platform.

## Warnings

- Binds to **`0.0.0.0:5777`** — reachable on all interfaces. Use only on trusted/lab networks.
- **SSH passwords and private key material** for monitored hosts are stored in local SQLite for demo convenience. Anyone with filesystem access to the DB can read them.
- Prefer **private key path** on the Cursor host over pasting key contents into the form.
- Admin password is stored as a **Werkzeug hash** only. Set `ADMIN_PASSWORD` in a local `.env` (never commit `.env`).
- Default host-key policy is **accept-new** (`AutoAddPolicy`) for demo ease. Set `SSH_STRICT_HOST_KEYS=1` to reject unknown hosts.
- Remote collection uses a **fixed allowlist** of read-only commands (`/proc`, `ss`/`netstat`). User input is never interpolated into remote shells.
- CSRF protection (Flask-WTF) is enabled on forms; session cookies are `HttpOnly`.
- CI uses dummy `SECRET_KEY` / `ADMIN_PASSWORD` in workflow `env` only. No SSH private keys or production passwords belong in Actions secrets for this demo.

## Not for production

Do not expose this service to the public internet, reuse it as a multi-tenant SaaS, or treat stored SSH credentials as safely encrypted.
