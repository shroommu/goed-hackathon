import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _normalized_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "sqlite:///goed_hackathon.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _openrouter_http_referer() -> str:
    """Site URL for OpenRouter attribution headers (see openrouter.ai/docs/requests)."""
    explicit = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
    if explicit:
        return explicit
    vercel = os.getenv("VERCEL_URL", "").strip()
    if vercel:
        return vercel if vercel.startswith("http") else f"https://{vercel}"
    return "https://goed-hackathon-backend.vercel.app"


class BaseConfig:
    APP_NAME = os.getenv("APP_NAME", "goed-hackathon-api")
    BUILD_VERSION = os.getenv("BUILD_VERSION", "dev")
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False
    SQLALCHEMY_DATABASE_URI = _normalized_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # OpenRouter / LLM Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    OPENROUTER_HTTP_REFERER = _openrouter_http_referer()
    OPENROUTER_APP_TITLE = os.getenv("OPENROUTER_APP_TITLE", "GoED Navigator")
    LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))


class LocalConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }


if os.getenv("DB_SSLMODE"):
    BaseConfig.SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
        "sslmode": os.getenv("DB_SSLMODE", "require")
    }
    LocalConfig.SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
        "sslmode": os.getenv("DB_SSLMODE", "require")
    }
    ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
        "sslmode": os.getenv("DB_SSLMODE", "require")
    }


CONFIG_BY_ENV = {
    "local": LocalConfig,
    "production": ProductionConfig,
}


def get_config() -> tuple[type[BaseConfig], str]:
    app_env = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "local")).lower()
    config_class = CONFIG_BY_ENV.get(app_env, LocalConfig)
    return config_class, app_env
