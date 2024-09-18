import asyncio
import time
from unittest import mock

import pytest
import requests
from apis.models.users import User
from apis.routers.users import users_router
from apis.tasks.users import (
    task_add_subscribe,
    task_send_welcome_email,
)
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_pytest_setup(async_client: AsyncClient, db_session):
    """Test pytest setup."""
    # test view
    response = await async_client.get(users_router.url_path_for("form_example_get"))
    assert response.status_code == 200

    # test db
    user = User(username="test", email="test@example.com")
    with db_session.begin():
        db_session.add(user)
    assert user.id


def test_view_with_eager_mode(client, settings, monkeypatch):
    """Test the view with eager mode."""
    mock_requests_post = mock.MagicMock()
    monkeypatch.setattr(requests, "post", mock_requests_post)

    monkeypatch.setattr(settings, "CELERY_TASK_ALWAYS_EAGER", True, raising=False)

    user_name = "michaelyin"
    user_email = f"{user_name}@accordbox.com"
    response = client.post(
        users_router.url_path_for("user_subscribe"),
        json={"email": user_email, "username": user_name},
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "send task to Celery successfully",
    }

    mock_requests_post.assert_called_with("https://httpbin.org/delay/5", data={"email": user_email})


def test_user_subscribe_view(client, db_session, monkeypatch, user_factory):
    """Test the user_subscribe view."""
    user = user_factory.build()

    mock_task_add_subscribe = mock.MagicMock(name="task_add_subscribe")
    mock_task_add_subscribe.return_value = mock.MagicMock(task_id="task_id")
    monkeypatch.setattr(task_add_subscribe, "delay", mock_task_add_subscribe)

    response = client.post(
        users_router.url_path_for("user_subscribe"), json={"email": user.email, "username": user.username}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "send task to Celery successfully",
    }

    # query from the db again
    user = db_session.query(User).filter_by(username=user.username).first()
    mock_task_add_subscribe.assert_called_with(user.id)


@pytest.mark.asyncio
async def test_transaction_celery(async_client, db_session, monkeypatch):
    """Test the transaction_celery endpoint."""

    def mock_random_username():
        return "test_user"

    monkeypatch.setattr("apis.routers.users.random_username", mock_random_username)

    # Mock the Celery task
    mock_task_send_welcome_email = mock.MagicMock(name="task_send_welcome_email")
    mock_task_send_welcome_email.return_value = mock.MagicMock(task_id="mocked_task_id")
    monkeypatch.setattr(task_send_welcome_email, "delay", mock_task_send_welcome_email)

    # Make the request to the endpoint
    response = await async_client.get("/users/transaction_celery/")

    # Check the response
    assert response.status_code == 200
    assert response.json() == {"message": "done"}

    # Check if a user was created in the database
    users = db_session.query(User).all()
    assert len(users) == 1
    user = users[0]

    # Check if the user has the expected attributes
    assert user.username == "test_user"
    assert user.email == "test_user@test.com"

    # Check if the Celery task was called with the correct user ID
    mock_task_send_welcome_email.assert_called_once_with(user.id)


@pytest.mark.asyncio
async def test_transaction_celery_concurrency(async_client, db_session, monkeypatch):
    """Test the transaction_celery endpoint with concurrency."""
    # Mock the random_username function to return unique usernames
    username_counter = 0

    def mock_random_username():
        nonlocal username_counter
        username_counter += 1
        return f"test_user_{username_counter}"

    monkeypatch.setattr("apis.routers.users.random_username", mock_random_username)

    # Mock the Celery task
    mock_task_send_welcome_email = mock.MagicMock(name="task_send_welcome_email")
    mock_task_send_welcome_email.return_value = mock.MagicMock(task_id="mocked_task_id")
    monkeypatch.setattr(task_send_welcome_email, "delay", mock_task_send_welcome_email)

    # Function to make a single request
    async def make_request():
        response = await async_client.get("/users/transaction_celery/")
        assert response.status_code == 200
        assert response.json() == {"message": "done"}
        return response

    # Make 5 concurrent requests
    _ = await asyncio.gather(*[make_request() for _ in range(5)])

    # Check if 5 users were created in the database
    users = db_session.query(User).all()
    assert len(users) == 5

    # Check if each user has the expected attributes
    for i, user in enumerate(users, start=1):
        assert user.username == f"test_user_{i}"
        assert user.email == f"test_user_{i}@test.com"

    # Check if the Celery task was called 5 times with correct user IDs
    assert mock_task_send_welcome_email.call_count == 5
    for user in users:
        mock_task_send_welcome_email.assert_any_call(user.id)

    # Optional: Check for unique user IDs
    user_ids = [user.id for user in users]
    assert len(set(user_ids)) == 5, "All user IDs should be unique"


@pytest.mark.asyncio
async def test_transaction_celery_concurrency_with_timing(async_client, db_session, monkeypatch):
    """Test the transaction_celery endpoint with concurrency and timing."""
    # Mock the random_username function to return unique usernames
    username_counter = 0

    def mock_random_username():
        nonlocal username_counter
        username_counter += 1
        return f"test_user_{username_counter}"

    monkeypatch.setattr("apis.routers.users.random_username", mock_random_username)

    # Mock the Celery task
    mock_task_send_welcome_email = mock.MagicMock(name="task_send_welcome_email")
    mock_task_send_welcome_email.return_value = mock.MagicMock(task_id="mocked_task_id")
    monkeypatch.setattr(task_send_welcome_email, "delay", mock_task_send_welcome_email)

    # Function to make a single request with timing
    async def make_request():
        start_time = time.time()
        response = await async_client.get("/users/transaction_celery/")
        end_time = time.time()
        assert response.status_code == 200
        assert response.json() == {"message": "done"}
        return end_time - start_time

    # Make 5 concurrent requests and measure time
    start_time = time.time()
    request_times = await asyncio.gather(*[make_request() for _ in range(5)])
    total_time = time.time() - start_time

    # Print timing results
    print(f"Total time for all requests: {total_time:.2f} seconds")  # noqa: E231, E501
    print(f"Individual request times: {[f'{t:.2f}' for t in request_times]} seconds")  # noqa: E231, E501

    # Check if 5 users were created in the database
    users = db_session.query(User).all()
    assert len(users) == 5

    # Check if each user has the expected attributes
    for i, user in enumerate(users, start=1):
        assert user.username == f"test_user_{i}"
        assert user.email == f"test_user_{i}@test.com"

    # Check if the Celery task was called 5 times with correct user IDs
    assert mock_task_send_welcome_email.call_count == 5
    for user in users:
        mock_task_send_welcome_email.assert_any_call(user.id)

    # Analyze concurrency
    if max(request_times) < total_time * 0.6:  # Adjust threshold as needed
        print("Requests appear to be processed concurrently")
    else:
        print("Requests appear to be processed mostly sequentially")

    return total_time, request_times
