"""Users related tasks."""

import logging
import random

import requests
from celery import shared_task

logger = logging.getLogger(__name__)


def api_call(email: str):
    """Simulate an api call."""
    logger.info("Processing email: %s", email)
    # used for testing a failed api call
    if random.choice([0, 1]):
        raise ValueError("random processing error")

    # used for simulating a call to a third-party api
    requests.post("https://httpbin.org/delay/5")


@shared_task
def divide(x: int, y: int) -> float:
    """Divide two numbers."""
    return x / y


@shared_task()
def sample_task(email):
    """Sample task to simulate an api call."""
    api_call(email)
