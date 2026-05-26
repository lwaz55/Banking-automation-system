import asyncio
import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from typing import Optional

router = APIRouter()

# Connected client queues
clients: list = []

# Reference to the main asyncio event loop — set on startup
_main_event_loop: Optional[asyncio.AbstractEventLoop] = None


def set_event_loop(loop: asyncio.AbstractEventLoop):
    global _main_event_loop
    _main_event_loop = loop


def get_event_loop() -> Optional[asyncio.AbstractEventLoop]:
    return _main_event_loop


async def broadcast_event(event_type: str, data: dict):
    """Broadcast an event to all connected SSE clients (async version)."""
    message = json.dumps({"type": event_type, "data": data})
    for client_queue in list(clients):
        try:
            await client_queue.put(message)
        except Exception:
            pass


def broadcast_event_sync(event_type: str, data: dict):
    """
    Broadcast an event from a synchronous context (background thread).
    Uses run_coroutine_threadsafe to post into the main event loop.
    """
    loop = _main_event_loop
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_event(event_type, data), loop)


@router.get("/events")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time frontend updates."""
    client_queue: asyncio.Queue = asyncio.Queue()
    clients.append(client_queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    # Wait up to 15s then send heartbeat to keep connection alive
                    message = await asyncio.wait_for(client_queue.get(), timeout=15.0)
                    yield {
                        "event": "message",
                        "id": "msg",
                        "retry": 10000,
                        "data": message,
                    }
                except asyncio.TimeoutError:
                    # Heartbeat
                    yield {
                        "event": "heartbeat",
                        "data": "ping",
                    }
        except asyncio.CancelledError:
            pass
        finally:
            if client_queue in clients:
                clients.remove(client_queue)

    return EventSourceResponse(event_generator())
