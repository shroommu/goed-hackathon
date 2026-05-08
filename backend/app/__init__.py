from flask import Flask

from .commands.seed import register_seed_command
from .config import get_config
from .extensions import db, migrate
from . import models  # noqa: F401
from .routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__)

    config_class, app_env = get_config()
    app.config.from_object(config_class)
    app.config["APP_ENV"] = app_env

    db.init_app(app)
    migrate.init_app(app, db)

    register_seed_command(app)

    register_routes(app)
    return app
