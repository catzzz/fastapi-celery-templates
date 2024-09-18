"""Factory for User model."""

import factory
from apis.database import SessionLocal
from apis.models.users import User
from factory import (
    Faker,
    LazyAttribute,
)


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for User model."""

    class Meta:
        """Factory for User model."""

        model = User
        sqlalchemy_session = SessionLocal()
        sqlalchemy_get_or_create = ("username",)
        sqlalchemy_session_persistence = "commit"

    username = Faker("user_name")
    email = LazyAttribute(lambda o: "%s@example.com" % o.username)
