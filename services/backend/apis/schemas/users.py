"""User schema."""
from pydantic import BaseModel


class UserBody(BaseModel):
    """UserBody schema."""

    username: str
    email: str
