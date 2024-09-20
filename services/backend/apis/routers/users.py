"""User router."""

import logging
import random
from string import ascii_lowercase

from apis.celery_utils import get_task_info
from apis.tasks.users import (
    sample_task,
    task_add_subscribe,
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
from shared.database import get_db_session
from shared.models.users import User
from shared.schemas.users import UserBody
from sqlalchemy.orm import Session

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


@users_router.post("/user_subscribe/")
def user_subscribe(user_body: UserBody, session: Session = Depends(get_db_session)):
    """Subscribe a user."""
    with session.begin():
        user = session.query(User).filter_by(username=user_body.username).first()
        if not user:
            user = User(
                username=user_body.username,
                email=user_body.email,
            )
            session.add(user)
    task_add_subscribe.delay(user.id)
    return {"message": "send task to Celery successfully"}


def random_username() -> str:
    """Generate a random username."""
    username = "".join([random.choice(ascii_lowercase) for i in range(5)])
    return username


@users_router.get("/transaction_celery/")
async def transaction_celery(session: Session = Depends(get_db_session)):
    """Test transaction with Celery."""
    username = random_username()
    user = User(
        username=f"{username}",
        email=f"{username}@test.com",
    )
    with session.begin():
        session.add(user)

    task_send_welcome_email.delay(user.id)
    return {"message": "done"}
