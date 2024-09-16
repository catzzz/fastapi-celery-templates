"""Configurations for the FastAPI application."""
import os
import pathlib
from functools import lru_cache

from kombu import Queue


def route_task(name, args, kwargs, options, task=None, **kw):  # noqa # pylint:  disable=unused-argument
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "default"}


class BaseConfig:
    """Base configuration settings."""

    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/db.sqlite3")  # noqa
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

    CELERY_TASK_QUEUES: list = (
        # need to define default queue here or exception would be raised
        Queue("default"),
        Queue("high_priority"),
        Queue("low_priority"),
    )
    CELERY_TASK_ROUTES = {
        "project.users.tasks.*": {
            "queue": "high_priority",
        },
    }
    CELERY_TASK_ROUTES = (route_task,)  # noqa


class DevelopmentConfig(BaseConfig):
    """Development configuration settings."""


class ProductionConfig(BaseConfig):
    """Production configuration settings."""


class TestingConfig(BaseConfig):
    """Testing configuration settings."""

    DATABASE_URL: str = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://test_user:test_password@test-db:5433/test_fastapi_celery",
    )
    DATABASE_CONNECT_DICT: dict = {}

    # Override Redis-related settings to use the Docker service name
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    WS_MESSAGE_QUEUE: str = "redis://redis:6379/0"

    # You might want to adjust these for testing
    CELERY_TASK_ALWAYS_EAGER: bool = (
        # Makes Celery tasks run synchronously for easier testing
        True
    )
    CELERY_TASK_EAGER_PROPAGATES: bool = True


@lru_cache()
def get_settings():
    """Get configuration settings."""
    config_cls_dict = {"development": DevelopmentConfig, "production": ProductionConfig, "testing": TestingConfig}

    config_name = os.environ.get("FASTAPI_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls()


settings = get_settings()
