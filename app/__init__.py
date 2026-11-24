"""Flask application factory for the monitoring demo."""

from __future__ import annotations

import logging

from flask import Flask

from app.config import Config


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(config_class)
    config_class.apply_secret_key(app)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from app.routes.main import main_bp

    app.register_blueprint(main_bp)

    return app
