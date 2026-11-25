"""Flask application factory for the monitoring demo."""

from __future__ import annotations

import logging
import os

from flask import Flask

from app.config import Config
from app.extensions import csrf, db


def create_app(config_class: type[Config] = Config, *, testing: bool = False) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(config_class)
    if testing:
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test-secret-key-not-for-production"
        # Avoid ephemeral-key warning noise in tests when SECRET_KEY already set.
    else:
        config_class.apply_secret_key(app)

    config_class.ensure_instance_path(app)

    # Prefer live env for admin password (tests set ADMIN_PASSWORD before create_app).
    app.config["ADMIN_PASSWORD"] = os.environ.get(
        "ADMIN_PASSWORD", app.config.get("ADMIN_PASSWORD")
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    db.init_app(app)
    csrf.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.servers import servers_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(servers_bp)

    with app.app_context():
        from app import models  # noqa: F401
        from app.auth import seed_admin_user

        db.create_all()
        if not testing:
            seed_admin_user(app.config.get("ADMIN_PASSWORD"))
        elif os.environ.get("ADMIN_PASSWORD"):
            seed_admin_user(os.environ.get("ADMIN_PASSWORD"))

    return app
