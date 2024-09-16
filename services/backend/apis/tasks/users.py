"""Users related tasks."""


import asyncio
import random

import aiohttp
import requests
from apis.database import AsyncSessionLocal
from apis.models.users import User
from apis.routers.socketio import update_celery_task_status_socketio
from apis.routers.wesocket import update_celery_task_status
from asgiref.sync import async_to_sync
from celery import shared_task
from celery.signals import task_postrun
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


# ---------------------
# WebSockets
# ---------------------
@task_postrun.connect
def task_postrun_handler(task_id, **kwargs):  # pylint: disable=unused-argument
    """Update the task status callback function."""
    # update websocket
    async_to_sync(update_celery_task_status)(task_id)

    # update socketio
    update_celery_task_status_socketio(task_id)  # new


# ---------------------
# Periodic Task
# ---------------------
@shared_task(name="task_schedule_work")
def task_schedule_work():
    """Periodic task to run every X seconds."""
    logger.info("task_schedule_work run")


# ---------------------
# Dynamic Routing Task
# ---------------------
@shared_task(name="default:dynamic_example_one")
def dynamic_example_one():
    """Dynamic task with default queue."""
    logger.info("Example One")


@shared_task(name="low_priority:dynamic_example_two")
def dynamic_example_two():
    """Dynamic task with low priority."""
    logger.info("Example Two")


@shared_task(name="high_priority:dynamic_example_three")
def dynamic_example_three():
    """Dynamic task with high priority."""
    logger.info("Example Three")


@shared_task()
def task_send_welcome_email(user_pk: int) -> None:
    """Send a welcome email to a user."""

    async def process_email():
        """Process the email."""
        async with AsyncSessionLocal() as session:
            try:
                user = await session.get(User, user_pk)
                if user:
                    print(f"Sending email to {user.email} {user.id}")
                    # Add your email sending logic here
                else:
                    print(f"User with id {user_pk} not found")
            except Exception as e:
                raise ValueError(f"Error processing welcome email for user {user_pk}: {str(e)}")

    # Create a new event loop and run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_email())
    finally:
        loop.close()


# ---------------------
# User Subscription Task
# ---------------------


@shared_task(bind=True, max_retries=3)
def task_add_subscribe(self, user_pk: int) -> None:
    """Add a user to a subscription list."""

    async def process_subscription():
        async with AsyncSessionLocal() as session:
            try:
                user = await session.get(User, user_pk)
                if user:
                    async with aiohttp.ClientSession() as http_session:
                        async with http_session.post(
                            "https://httpbin.org/delay/5", data={"email": user.email}, timeout=10
                        ) as response:
                            await response.text()  # Ensure the request is completed
                    print(f"Added user {user.email} to subscription list")
                else:
                    print(f"User with id {user_pk} not found")
            except Exception as e:
                raise self.retry(exc=e, countdown=60)

    # Create a new event loop and run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_subscription())
    finally:
        loop.close()
