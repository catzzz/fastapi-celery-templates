"""User model."""

from apis.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
)


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(128), unique=True, nullable=False)
    email = Column(String(128), unique=True, nullable=False)

    def __init__(self, username, email):
        """Initialize User model."""
        self.username = username
        self.email = email
