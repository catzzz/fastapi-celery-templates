"""Implementation of CRUD operations for users."""

from typing import (
    Any,
    Dict,
    Optional,
)

from shared.models.users import User
from shared.redis_interfacce import RedisInterface
from sqlalchemy.orm import Session

from .base_crud import BaseCRUD


class UserCRUD(BaseCRUD[User]):
    """CRUD operations for User model."""

    def __init__(self, redis_interface: RedisInterface):
        super().__init__(User, redis_interface)

    def to_dict(self, obj: User) -> Dict[str, Any]:
        """Convert the User object to a dictionary."""
        return {
            "id": obj.id,
            "username": obj.username,
            "email": obj.email,
        }

    def from_dict(self, data: Dict[str, Any]) -> User:
        """Create a User object from a dictionary."""
        user = User(username=data["username"], email=data["email"])
        if "id" in data:
            user.id = data["id"]
        return user

    # --- Additional methods for UserCRUD ---
    def get_user_by_email(self, db_session: Session, email: str) -> Optional[User]:
        """Get a user by email."""
        return db_session.query(User).filter(User.email == email).first()
