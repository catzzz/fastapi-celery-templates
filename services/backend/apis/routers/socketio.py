"""SocketIO."""
import socketio
from apis.celery_utils import get_task_info
from apis.config import settings
from fastapi import FastAPI
from socketio.asyncio_namespace import AsyncNamespace


# -----------------------
# SocketIO
# -----------------------
class TaskStatusNameSpace(AsyncNamespace):
    """SocketIO namespace for task status updates."""

    async def on_join(self, sid, data):
        """Join the room."""
        self.enter_room(sid=sid, room=data["task_id"])
        # just in case the task already finish
        await self.emit("status", get_task_info(data["task_id"]), room=data["task_id"])


def register_socketio_app(app: FastAPI):
    """Register the SocketIO app."""
    mgr = socketio.AsyncRedisManager(settings.WS_MESSAGE_QUEUE)
    # https://python-socketio.readthedocs.io/en/latest/server.html#uvicorn-daphne-and-other-asgi-servers
    # https://github.com/tiangolo/fastapi/issues/129#issuecomment-714636723
    sio = socketio.AsyncServer(async_mode="asgi", client_manager=mgr, logger=True, engineio_logger=True)
    sio.register_namespace(TaskStatusNameSpace("/task_status"))
    asgi = socketio.ASGIApp(
        socketio_server=sio,
    )
    app.mount("/ws", asgi)


def update_celery_task_status_socketio(task_id):
    """
    Update Celery task status via Socket.IO.

    This function is called in the Celery worker to emit task status updates
    to connected clients using Socket.IO.

    For more information on emitting events from external processes, see:
    https://python-socketio.readthedocs.io/en/latest/server.html#emitting-from-external-processes

    Args:
    ----
    task_id : str
        The ID of the Celery task to update.

    """
    # connect to the redis queue as an external process
    external_sio = socketio.RedisManager(settings.WS_MESSAGE_QUEUE, write_only=True)
    # emit an event
    external_sio.emit("status", get_task_info(task_id), room=task_id, namespace="/task_status")
