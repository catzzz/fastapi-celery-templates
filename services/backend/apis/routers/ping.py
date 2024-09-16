"""Ping router for health check endpoint."""
from fastapi import APIRouter

ping_router = APIRouter(
    prefix="/ping",
)


@ping_router.get("")
async def root():
    """Health check endpoint."""
    return {"message": "pong"}
