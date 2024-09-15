# project/app/config.py
"""FastAPI configuration settings."""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings

log = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    """FastAPI configuration settings."""

    environment: str = "dev"
    testing: bool = 0


@lru_cache()
def get_settings() -> BaseSettings:
    """Get the configuration settings."""
    log.info("Loading config settings from the environment...")
    return Settings()
