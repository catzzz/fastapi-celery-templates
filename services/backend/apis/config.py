"""Configurations for the FastAPI application."""

import os
import pathlib
from functools import lru_cache
from typing import (
    Any,
    Dict,
)

from kombu import Queue


def route_task(name: str) -> Dict[str, Any]:  # noqa # pylint:  disable=unused-argument
    """Route tasks to different queues based on the task name."""
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "default"}


class BaseConfig:
    """Base configuration settings."""

    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent

    DATABASE_NAME: str = os.environ["DATABASE_NAME"]
    DATABASE_USER: str = os.environ["DATABASE_USER"]
    DATABASE_PASSWORD: str = os.environ["DATABASE_PASSWORD"]
    DATABASE_HOST: str = os.environ["DATABASE_HOST"]
    DATABASE_PORT: str = os.environ["DATABASE_PORT"]

    DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"  # noqa: E231, E501

    # DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3")  # noqa
    DATABASE_CONNECT_DICT: dict = {}
    # Celery
    CELERY_BROKER_URL: str = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")  # NEW
    CELERY_RESULT_BACKEND: str = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")  # NEW
    # WebSockets
    WS_MESSAGE_QUEUE: str = os.environ.get("WS_MESSAGE_QUEUE", "redis://127.0.0.1:6379/0")

    CELERY_BEAT_SCHEDULE: dict = {
        "task-schedule-work": {
            "task": "task_schedule_work",
            "schedule": 5.0,  # five seconds
        },
    }
    CELERY_TASK_DEFAULT_QUEUE: str = "default"

    # Force all queues to be explicitly listed in `CELERY_TASK_QUEUES` to help prevent typos
    CELERY_TASK_CREATE_MISSING_QUEUES: bool = False

    CELERY_TASK_QUEUES: tuple = (
        # need to define default queue here or exception would be raised
        Queue("default"),
        Queue("high_priority"),
        Queue("low_priority"),
    )
    # dynamic routing
    CELERY_TASK_ROUTES: tuple = (route_task,)


class DevelopmentConfig(BaseConfig):
    """Development configuration settings."""


class ProductionConfig(BaseConfig):
    """Production configuration settings."""


class TestingConfig(BaseConfig):
    """Testing configuration settings."""


@lru_cache()
def get_settings() -> BaseConfig:
    """Get configuration settings."""
    config_cls_dict = {"development": DevelopmentConfig, "production": ProductionConfig, "testing": TestingConfig}

    config_name = os.environ.get("FASTAPI_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


settings = get_settings()
