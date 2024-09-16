"""Initializes the FastAPI app and includes the routers."""

from apis.broadcast import lifespan
from apis.celery_utils import create_celery
from apis.logging import configure_logging
from apis.routers.socketio import register_socketio_app
from apis.routers.users import users_router
from apis.routers.wesocket import ws_router
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(lifespan=lifespan)

    # configure logging
    configure_logging()
    # do this before loading routes
    app.celery_app = create_celery()

    # include users router
    app.include_router(users_router)
    # include websocket router
    app.include_router(ws_router)

    # include socketio
    register_socketio_app(app)

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    return app
