# project/app/main.py
"""FastAPI app."""

from config import (
    Settings,
    get_settings,
)
from fastapi import (
    Depends,
    FastAPI,
)

app = FastAPI()


@app.get("/ping")
async def pong(settings: Settings = Depends(get_settings)):
    """Health check endpoint."""
    return {"ping": "pong!", "environment": settings.environment, "testing": settings.testing}
