import os


class BaseConfig:
    APP_NAME = os.getenv("APP_NAME", "goed-hackathon-api")
    BUILD_VERSION = os.getenv("BUILD_VERSION", "dev")
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False


class LocalConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIG_BY_ENV = {
    "local": LocalConfig,
    "production": ProductionConfig,
}


def get_config() -> tuple[type[BaseConfig], str]:
    app_env = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "local")).lower()
    config_class = CONFIG_BY_ENV.get(app_env, LocalConfig)
    return config_class, app_env
