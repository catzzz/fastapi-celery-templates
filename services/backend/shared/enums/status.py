"""Status Enum."""

from enum import Enum


class Status(str, Enum):
    """Status Enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
