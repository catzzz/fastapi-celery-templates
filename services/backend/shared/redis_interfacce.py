"""Redis Interface."""

import json
from functools import wraps
from typing import (
    Any,
    Optional,
)

import redis
from apis.config import settings


class SharedRedisClient:
    """Shared Redis client."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Get Redis instance."""
        if cls._instance is None:
            cls._instance = redis.Redis(
                host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
            )
        return cls._instance


class RedisInterface:
    """Interface to interact with Redis."""

    def __init__(self):
        self.redis = SharedRedisClient.get_instance()

    def set(self, key: str, value: Any, ex: Optional[int] = None):
        """Set a key-value pair in Redis, with optional expiration time."""
        self.redis.set(key, json.dumps(value), ex=ex)

    def get(self, key: str) -> Any:
        """Get a value from Redis by key."""
        value = self.redis.get(key)
        return json.loads(value) if value else None

    def delete(self, key: str):
        """Delete a key from Redis."""
        self.redis.delete(key)

    def cache(self, ex: Optional[int] = None):
        """Cache the results in Redis."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create a unique key based on the function name and arguments
                key = f"{func.__name__}:{args}:{kwargs}"  # noqa E231, E501
                result = self.get(key)
                if result is None:
                    result = func(*args, **kwargs)
                    self.set(key, result, ex=ex)
                return result

            return wrapper

        return decorator


def get_redis_interface():
    """Return a RedisInterface instance."""
    return redis_interface


# Create a global instance
redis_interface = RedisInterface()
