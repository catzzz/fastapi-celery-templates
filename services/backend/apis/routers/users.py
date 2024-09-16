"""User router."""

import logging
import random
from string import ascii_lowercase

from apis.celery_utils import get_task_info
from apis.database import get_db_session
from apis.models.users import User
from apis.schemas.users import UserBody
from apis.tasks.users import (
    sample_task,
    task_process_notification,
    task_send_welcome_email,
)
from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

users_router = APIRouter(
    prefix="/users",
)

templates = Jinja2Templates(directory="apis/templates/users")


# --------------------------------------------
# Emulate a user router, for webhooks and async tasks
# --------------------------------------------


@users_router.get("/form/")
async def form_example_get(request: Request):
    """Get a form."""
    return templates.TemplateResponse("form.html", {"request": request})


@users_router.post("/form/")
async def form_example_post(user_body: UserBody):
    """Post a user."""
    task = sample_task.delay(user_body.email)
    return JSONResponse({"task_id": task.task_id})


@users_router.get("/task_status/")
async def task_status(task_id: str):
    """Get the status of a task."""
    response = get_task_info(task_id)
    return JSONResponse(response)


@users_router.post("/webhook_test_async/")
async def webhook_test_async():
    """Test async task notification."""
    task_process_notification.delay()

    return "pong"


# ---------------------
# WebSockets
# ---------------------
@users_router.get("/form_ws/")
def form_ws_example(request: Request):
    """Get a form with websocket."""
    return templates.TemplateResponse("form_ws.html", {"request": request})


# -----------------------
# SocketIO
# -----------------------
@users_router.get("/form_socketio/")
def form_socketio_example(request: Request):
    """Get a form with socketio."""
    return templates.TemplateResponse("form_socketio.html", {"request": request})


# -----------------------
# Database transaction
# -----------------------


def random_username():
    """Generate a random username."""
    username = "".join([random.choice(ascii_lowercase) for i in range(5)])
    return username


@users_router.get("/transaction_celery/")
async def transaction_celery(session: AsyncSession = Depends(get_db_session)):
    """Create a new user and send a welcome email."""
    username = random_username()
    user = User(
        username=f"{username}",
        email=f"{username}@test.com",
    )
    async with session.begin():
        session.add(user)

    await session.refresh(user)  # Refresh to get the new user.id
    logger.info("user %s %s is persistent now", user.id, user.username)  # Fixed logging
    task_send_welcome_email.delay(user.id)
    return {"message": "done"}
