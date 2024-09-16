"""Configurations for the FastAPI application."""
import os
import pathlib
from functools import lru_cache


class BaseConfig:
    """Base configuration settings."""

    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3")  # noqa
    DATABASE_CONNECT_DICT: dict = {}


class DevelopmentConfig(BaseConfig):
    """Development configuration settings."""


class ProductionConfig(BaseConfig):
    """Production configuration settings."""


class TestingConfig(BaseConfig):
    """Testing configuration settings."""


@lru_cache()
def get_settings():
    """Get configuration settings."""
    config_cls_dict = {"development": DevelopmentConfig, "production": ProductionConfig, "testing": TestingConfig}

    config_name = os.environ.get("FASTAPI_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


settings = get_settings()
