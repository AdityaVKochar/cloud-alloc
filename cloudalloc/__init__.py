from __future__ import annotations

from pathlib import Path

from flask import Flask

from .api import api
from .cli import register_cli
from .config import Config
from .dashboard import dashboard
from .extensions import db, migrate


def create_app(config: type[Config] | dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if isinstance(config, dict):
        app.config.update(config)
    elif config is not None:
        app.config.from_object(config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["ARTIFACT_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(dashboard)
    register_cli(app)

    @app.errorhandler(404)
    def not_found(error):
        if str(getattr(error, "description", "")).startswith("API:"):
            return {"error": "not_found", "message": error.description[4:]}, 404
        return error, 404

    return app

