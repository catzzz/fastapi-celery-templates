"""Users related tasks."""

from celery import shared_task


@shared_task
def divide(x: int, y: int) -> float:
    """Divide two numbers."""
    return x / y
