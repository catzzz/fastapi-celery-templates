from unittest import mock

import pytest
from apis.models.users import User
from apis.routers.users import users_router
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_form_example_get_setup(async_client, db_session: AsyncSession):
    """Test the form_example_get endpoint."""
    # test view
    response = await async_client.get(users_router.url_path_for("form_example_get"))
    assert response.status_code == 200

    # test db
    user = User(username="test", email="test@example.com")
    async with db_session.begin():
        db_session.add(user)
        await db_session.flush()
    assert user.id is not None


@pytest.mark.asyncio
async def test_user_subscribe_with_eager_mode(
    async_client: AsyncClient, db_session: AsyncSession, settings, monkeypatch
):
    """Test the user_subscribe endpoint with eager mode enabled."""
    mock_task_add_subscribe = mock.Mock()
    monkeypatch.setattr("apis.routers.users.task_add_subscribe.delay", mock_task_add_subscribe)

    monkeypatch.setattr(settings, "CELERY_TASK_ALWAYS_EAGER", True, raising=False)

    user_name = "michaelyin"
    user_email = f"{user_name}@accordbox.com"

    response = await async_client.post(
        users_router.url_path_for("user_subscribe"),
        json={"email": user_email, "username": user_name},
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Sent task to Celery successfully",
    }

    # Check if the user was created in the database
    async with db_session.begin():
        result = await db_session.execute(select(User).filter_by(username=user_name))
        user = result.scalars().first()

    assert user is not None
    assert user.email == user_email

    # Check if the Celery task was called
    mock_task_add_subscribe.assert_called_once_with(user.id)

    # Clean up: delete the user
    async with db_session.begin():
        await db_session.delete(user)
        await db_session.commit()
