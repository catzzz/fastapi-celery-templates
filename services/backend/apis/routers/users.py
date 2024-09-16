"""User router."""

from apis.schemas.users import UserBody
from apis.tasks.users import sample_task
from celery.result import AsyncResult
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

# Sim


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
    task = AsyncResult(task_id)
    state = task.state

    if state == "FAILURE":
        error = str(task.result)
        response = {
            "state": state,
            "error": error,
        }
    else:
        response = {
            "state": state,
        }
    return JSONResponse(response)
