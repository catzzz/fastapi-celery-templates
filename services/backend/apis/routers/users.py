"""User router."""

from apis.celery_utils import get_task_info
from apis.schemas.users import UserBody
from apis.tasks.users import (
    sample_task,
    task_process_notification,
)
from fastapi import (
    APIRouter,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

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
