"""Initializes the FastAPI app and includes the routers."""

from apis.broadcast import lifespan
from apis.celery_utils import create_celery
from apis.routers.users import users_router
from apis.routers.wesocket import ws_router
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(lifespan=lifespan)

    # do this before loading routes
    app.celery_app = create_celery()

    app.include_router(users_router)

    app.include_router(ws_router)

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    return app
