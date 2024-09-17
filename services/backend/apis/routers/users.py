"""User router."""

import logging
import random
from string import ascii_lowercase
from typing import Dict

from apis.celery_utils import get_task_info
from apis.database import get_db_session
from apis.models.users import User
from apis.schemas.users import UserBody
from apis.tasks.users import (
    sample_task,
    task_add_subscribe,
    task_process_notification,
    task_send_welcome_email,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

users_router = APIRouter(
    prefix="/users",
)

templates = Jinja2Templates(directory="apis/templates/users")


@users_router.get("/form/")
async def form_example_get(request: Request) -> templates.TemplateResponse:
    """Get a form."""
    return templates.TemplateResponse(name="form.html", request={"request": request})


@users_router.post("/form/")
async def form_example_post(user_body: UserBody) -> JSONResponse:
    """Post a user."""
    task = sample_task.delay(user_body.email)
    return JSONResponse({"task_id": task.task_id})


@users_router.get("/task_status/")
async def task_status(task_id: str) -> JSONResponse:
    """Get the status of a task."""
    response = get_task_info(task_id)
    return JSONResponse(response)


@users_router.post("/webhook_test_async/")
async def webhook_test_async() -> str:
    """Test async task notification."""
    task_process_notification.delay()
    return "pong"


@users_router.get("/form_ws/")
def form_ws_example(request: Request) -> templates.TemplateResponse:
    """Get a form with websocket."""
    return templates.TemplateResponse("form_ws.html", {"request": request})


@users_router.get("/form_socketio/")
def form_socketio_example(request: Request) -> templates.TemplateResponse:
    """Get a form with socketio."""
    return templates.TemplateResponse("form_socketio.html", {"request": request})


@users_router.post("/user_subscribe")
async def user_subscribe(user_body: UserBody, session: AsyncSession = Depends(get_db_session)) -> Dict[str, str]:
    """Create a new user and add them to a subscription list."""
    try:
        async with session.begin():
            result = await session.execute(select(User).filter_by(username=user_body.username))
            user = result.scalars().first()
            if not user:
                user = User(
                    username=user_body.username,
                    email=user_body.email,
                )
                session.add(user)
                await session.flush()  # Flush to get the new user.id

        # Move this outside of the session context
        task_add_subscribe.delay(user.id)
        return {"message": "Sent task to Celery successfully"}
    except Exception as e:
        logger.error("Error in user_subscribe: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


def random_username() -> str:
    """Generate a random username."""
    username = "".join([random.choice(ascii_lowercase) for i in range(5)])
    return username


@users_router.get("/transaction_celery/")
async def transaction_celery(session: AsyncSession = Depends(get_db_session)) -> Dict[str, str]:
    """Create a new user and send a welcome email."""
    username = random_username()
    user = User(
        username=f"{username}",
        email=f"{username}@test.com",
    )
    async with session.begin():
        session.add(user)

    await session.refresh(user)  # Refresh to get the new user.id
    logger.info("user %s %s is persistent now", user.id, user.username)
    task_send_welcome_email.delay(user.id)
    return {"message": "done"}
