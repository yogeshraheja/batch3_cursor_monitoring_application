"""Local entry point: bind the demo on 0.0.0.0:5777."""

from __future__ import annotations

import os

from app import create_app
from app.config import Config

app = create_app()


if __name__ == "__main__":
    # Debug stays off by default: the app binds 0.0.0.0 and must not expose the
    # Werkzeug debugger on the network. Set FLASK_DEBUG=1 for local breakpoints.
    debug = os.environ.get("FLASK_DEBUG", "").strip() in {"1", "true", "True"}
    app.run(host=Config.HOST, port=Config.PORT, debug=debug)
