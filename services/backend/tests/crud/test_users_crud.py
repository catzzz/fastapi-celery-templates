"""Test cases for the UserCRUD class."""

import json
import logging

import pytest
from shared.crud.users import UserCRUD
from shared.models.users import User
from shared.redis_interfacce import RedisInterface
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@pytest.fixture
def user_crud(mock_redis_interface):
    """Return a UserCRUD instance with a mock Redis interface."""
    print("Creating UserCRUD instance")
    return UserCRUD(redis_interface=mock_redis_interface)


def test_redis_interface(mock_shared_redis_client):
    """Test RedisInterface set method."""
    redis_interface = RedisInterface()
    redis_interface.set("test_key", "test_value")
    mock_shared_redis_client.set.assert_called_once_with("test_key", '"test_value"', ex=None)


def test_create_user(db_session: Session, user_crud: UserCRUD, mock_redis_interface):
    """Test create user functionality."""
    logger.debug("Starting test_create_user")
    # Prepare test data
    user_data = {"username": "testuser", "email": "testuser@example.com"}

    # Call the create method
    logger.debug("Calling create method")
    created_user = user_crud.create(db_session, obj_in=user_data)

    # Assertions
    assert isinstance(created_user, User)
    assert created_user.username == user_data["username"]
    assert created_user.email == user_data["email"]
    assert created_user.id is not None

    # Verify that the user was added to the database
    db_user = db_session.query(User).filter(User.id == created_user.id).first()
    assert db_user is not None
    assert db_user.username == user_data["username"]
    assert db_user.email == user_data["email"]

    # Debug logging
    logger.debug("Mock Redis interface: %s", mock_redis_interface)
    logger.debug("Mock Redis interface set method called: %s", mock_redis_interface.set.called)
    logger.debug("Mock Redis interface set method call count: %s", mock_redis_interface.set.call_count)
    logger.debug("Mock Redis interface set method call args: %s", mock_redis_interface.set.call_args)

    # Verify that Redis cache was called
    mock_redis_interface.set.assert_called_once()
    cache_key = user_crud.get_cache_key(created_user.id)
    expected_cache_value = json.dumps(user_crud.to_dict(created_user))
    mock_redis_interface.set.assert_called_with(cache_key, expected_cache_value, ex=3600)


def test_create_user_duplicate_username(db_session: Session, user_crud: UserCRUD):
    """Test creating a user with a duplicate username."""
    logger.debug("Starting test_create_user_duplicate_username")
    # Create initial user
    user_data = {"username": "testuser", "email": "testuser@example.com"}
    user_crud.create(db_session, obj_in=user_data)

    # Attempt to create user with duplicate username
    duplicate_username_data = {
        "username": "testuser",  # Same username
        "email": "another@example.com",  # Different email
    }

    with pytest.raises(ValueError) as exc_info:
        user_crud.create(db_session, obj_in=duplicate_username_data)

    assert str(exc_info.value) == "Object with these details already exists"

    # Verify only one user exists in the database
    user_count = db_session.query(User).count()
    assert user_count == 1


def test_create_user_duplicate_email(db_session: Session, user_crud: UserCRUD):
    """Test creating a user with a duplicate email."""
    logger.debug("Starting test_create_user_duplicate_email")
    # Create initial user
    user_data = {"username": "testuser", "email": "testuser@example.com"}
    user_crud.create(db_session, obj_in=user_data)

    # Attempt to create user with duplicate email
    duplicate_email_data = {
        "username": "anotheruser",  # Different username
        "email": "testuser@example.com",  # Same email
    }

    with pytest.raises(ValueError) as exc_info:
        user_crud.create(db_session, obj_in=duplicate_email_data)

    assert str(exc_info.value) == "Object with these details already exists"

    # Verify only one user exists in the database
    user_count = db_session.query(User).count()
    assert user_count == 1


def test_get_user(db_session: Session, user_crud: UserCRUD, mock_redis_interface):
    """Test getting a user."""
    # Create a user
    user_data = {"username": "testuser", "email": "testuser@example.com"}
    user = user_crud.create(db_session, obj_in=user_data)

    # Reset mock to clear the call from create operation
    mock_redis_interface.set.reset_mock()

    # Test cache miss
    mock_redis_interface.get.return_value = None
    retrieved_user = user_crud.get(db_session, obj_id=user.id)
    assert retrieved_user.id == user.id
    assert retrieved_user.username == user.username
    assert retrieved_user.email == user.email

    # Check that set was called once during the get operation (cache miss)
    mock_redis_interface.set.assert_called_once()
    mock_redis_interface.set.assert_called_with(
        f"User: {user.id}", json.dumps({"id": user.id, "username": user.username, "email": user.email}), ex=3600
    )

    # Reset mock for cache hit test
    mock_redis_interface.set.reset_mock()
    mock_redis_interface.get.reset_mock()

    # Test cache hit
    cached_user_data = json.dumps({"id": user.id, "username": user.username, "email": user.email})
    mock_redis_interface.get.return_value = cached_user_data
    retrieved_user = user_crud.get(db_session, obj_id=user.id)
    assert retrieved_user.id == user.id
    assert retrieved_user.username == user.username
    assert retrieved_user.email == user.email

    # Ensure set is not called on cache hit
    mock_redis_interface.set.assert_not_called()

    # Ensure get was called with the correct key
    mock_redis_interface.get.assert_called_once_with(f"User: {user.id}")


def test_get_multi_users(db_session: Session, user_crud: UserCRUD):
    """Test getting multiple users."""
    # Create multiple users
    users_data = [
        {"username": "user1", "email": "user1@example.com"},
        {"username": "user2", "email": "user2@example.com"},
        {"username": "user3", "email": "user3@example.com"},
    ]
    for user_data in users_data:
        user_crud.create(db_session, obj_in=user_data)

    # Test get_multi
    users = user_crud.get_multi(db_session, skip=0, limit=2)
    assert len(users) == 2
    assert users[0].username == "user1"
    assert users[1].username == "user2"

    users = user_crud.get_multi(db_session, skip=1, limit=2)
    assert len(users) == 2
    assert users[0].username == "user2"
    assert users[1].username == "user3"


def test_update_user(db_session: Session, user_crud: UserCRUD, mock_redis_interface):
    """Test updating a user."""
    # Create a user
    user_data = {"username": "testuser", "email": "testuser@example.com"}
    user = user_crud.create(db_session, obj_in=user_data)

    # Update user
    update_data = {"username": "updateduser"}
    updated_user = user_crud.update(db_session, db_obj=user, obj_in=update_data)
    assert updated_user.id == user.id
    assert updated_user.username == "updateduser"
    assert updated_user.email == user.email

    # Check if cache was updated
    mock_redis_interface.set.assert_called_with(
        user_crud.get_cache_key(user.id), json.dumps(user_crud.to_dict(updated_user)), ex=3600
    )


def test_delete_user(db_session: Session, user_crud: UserCRUD, mock_redis_interface):
    """Tesst deleting a user."""
    # Create a user
    user_data = {"username": "testuser", "email": "testuser@example.com"}
    user = user_crud.create(db_session, obj_in=user_data)

    # Delete user
    deleted_user = user_crud.delete(db_session, obj_id=user.id)
    assert deleted_user.id == user.id

    # Check if user was deleted from database
    assert db_session.query(User).filter(User.id == user.id).first() is None

    # Check if cache was cleared
    mock_redis_interface.delete.assert_called_with(user_crud.get_cache_key(user.id))
