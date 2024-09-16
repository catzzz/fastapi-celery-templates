"""Users related tasks."""


import random

import requests
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


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


@shared_task(bind=True)
def task_process_notification(self):
    """Task to process notification."""
    try:
        if not random.choice([0, 1]):
            # mimic random error
            raise ValueError("random processing error")

        # this would block the I/O
        requests.post("https://httpbin.org/delay/5")
    except Exception as e:
        logger.error("exception raised, it would be retry after 5 seconds")
        raise self.retry(exc=e, countdown=5)
