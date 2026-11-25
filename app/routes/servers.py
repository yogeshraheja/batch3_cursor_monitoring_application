"""Server inventory and metrics detail (admin session)."""

from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)

from app.auth import login_required
from app.extensions import db
from app.forms import DeleteServerForm, ServerForm
from app.metrics import collect_host_metrics, format_bytes
from app.models import Server
from app.ssh_client import SSHError, probe_connectivity

servers_bp = Blueprint("servers", __name__, url_prefix="/servers")


def _check_and_update_status(server: Server) -> str | None:
    """Update reachability. Returns an error message on failure, else None."""
    timeout = int(current_app.config.get("SSH_CONNECT_TIMEOUT", 8))
    strict = bool(current_app.config.get("SSH_STRICT_HOST_KEYS", False))
    try:
        status = probe_connectivity(
            server, timeout=timeout, strict_host_keys=strict
        )
        server.mark_checked(status)
        db.session.commit()
        return None
    except SSHError as exc:
        server.mark_checked("failed")
        db.session.commit()
        return str(exc)


@servers_bp.get("/")
@login_required
def list_servers():
    servers = Server.query.order_by(Server.name.asc()).all()
    delete_form = DeleteServerForm()
    return render_template(
        "servers/list.html", servers=servers, delete_form=delete_form
    )


@servers_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_server():
    form = ServerForm()
    if form.validate_on_submit():
        server = Server(
            name=form.name.data.strip(),
            host=form.host.data.strip(),
            ssh_port=form.ssh_port.data,
            ssh_username=form.ssh_username.data.strip(),
            auth_type=form.auth_type.data,
            ssh_password=(form.ssh_password.data or None)
            if form.auth_type.data == "password"
            else None,
            private_key_path=(form.private_key_path.data or "").strip() or None,
            private_key_content=(form.private_key_content.data or "").strip() or None,
            last_status="unknown",
        )
        if form.auth_type.data == "key":
            server.ssh_password = None
        db.session.add(server)
        db.session.commit()
        error = _check_and_update_status(server)
        flash(f"Server “{server.name}” added.", "success")
        if error:
            flash(error, "error")
        return redirect(url_for("servers.list_servers"))
    return render_template("servers/add.html", form=form)


@servers_bp.post("/<int:server_id>/delete")
@login_required
def delete_server(server_id: int):
    form = DeleteServerForm()
    if not form.validate_on_submit():
        flash("Invalid request.", "error")
        return redirect(url_for("servers.list_servers"))

    server = db.session.get(Server, server_id)
    if server is None:
        abort(404)
    name = server.name
    db.session.delete(server)
    db.session.commit()
    flash(f"Server “{name}” removed.", "success")
    return redirect(url_for("servers.list_servers"))


@servers_bp.post("/<int:server_id>/check")
@login_required
def check_server(server_id: int):
    form = DeleteServerForm()  # CSRF-only POST
    if not form.validate_on_submit():
        flash("Invalid request.", "error")
        return redirect(url_for("servers.list_servers"))
    server = db.session.get(Server, server_id)
    if server is None:
        abort(404)
    error = _check_and_update_status(server)
    if error:
        flash(error, "error")
    else:
        flash(f"Reachability checked for “{server.name}”.", "success")
    return redirect(url_for("servers.list_servers"))


@servers_bp.get("/<int:server_id>")
@login_required
def server_detail(server_id: int):
    server = db.session.get(Server, server_id)
    if server is None:
        abort(404)
    metrics = collect_host_metrics(current_app, server)
    if metrics.error:
        server.mark_checked("failed")
    else:
        server.mark_checked("reachable")
    db.session.commit()
    return render_template(
        "servers/detail.html",
        server=server,
        metrics=metrics,
        format_bytes=format_bytes,
    )
