"""Websocket router for task status updates."""
import json

from apis.broadcast import broadcast
from apis.celery_utils import get_task_info
from fastapi import (
    APIRouter,
    WebSocket,
)

ws_router = APIRouter()


@ws_router.websocket("/ws/task_status/{task_id}")
async def ws_task_status(websocket: WebSocket):
    """Websocket endpoint to get task status."""
    await websocket.accept()

    task_id = websocket.scope["path_params"]["task_id"]

    async with broadcast.subscribe(channel=task_id) as subscriber:
        # just in case the task already finish
        data = get_task_info(task_id)
        await websocket.send_json(data)

        async for event in subscriber:
            await websocket.send_json(json.loads(event.message))


async def update_celery_task_status(task_id: str):
    """Update the task status."""
    await broadcast.connect()
    await broadcast.publish(
        channel=task_id, message=json.dumps(get_task_info(task_id))  # RedisProtocol.publish expect str
    )
    await broadcast.disconnect()
