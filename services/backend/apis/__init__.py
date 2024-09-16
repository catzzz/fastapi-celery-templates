"""Initializes the FastAPI app and includes the routers."""
from apis.routers.users import users_router
from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI()

    app.include_router(users_router)

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    return app
