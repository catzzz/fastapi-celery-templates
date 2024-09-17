"""Websocket broadcast service."""

from contextlib import asynccontextmanager  # type: ignore

from apis.config import settings
from broadcaster import Broadcast
from fastapi import FastAPI

broadcast = Broadcast(settings.WS_MESSAGE_QUEUE)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument
    """Connect and disconnect to the broadcast service."""
    await broadcast.connect()
    yield
    await broadcast.disconnect()
