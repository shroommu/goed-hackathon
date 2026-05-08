from flask import Flask

from .config import get_config
from .routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__)

    config_class, app_env = get_config()
    app.config.from_object(config_class)
    app.config["APP_ENV"] = app_env

    register_routes(app)
    return app
