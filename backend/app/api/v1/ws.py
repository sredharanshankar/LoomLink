from __future__ import annotations
import asyncio
import json
import logging
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token
from app.core.errors import AppError
from app.core.rbac import PERMISSIONS

logger = logging.getLogger(__name__)
router = APIRouter()

# {role: set of websocket connections}
_connections: dict[str, set[WebSocket]] = {}
_lock = asyncio.Lock()


async def _ws_broadcast(event_type: str, payload: dict) -> None:
    """Called by the event dispatcher to send events to connected clients."""
    message = json.dumps({"type": event_type, "payload": payload})
    async with _lock:
        dead: list[tuple[str, WebSocket]] = []
        for role, sockets in _connections.items():
            if role == "buyer":
                continue
            for ws in list(sockets):
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append((role, ws))
        for role, ws in dead:
            _connections.get(role, set()).discard(ws)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    try:
        payload = decode_access_token(token)
    except Exception:
        await websocket.close(code=4001)
        return

    role = payload.get("role", "")
    if role == "buyer":
        await websocket.close(code=4003)
        return

    await websocket.accept()

    async with _lock:
        _connections.setdefault(role, set()).add(websocket)

    from app.core.events import set_ws_broadcast
    set_ws_broadcast(_ws_broadcast)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            _connections.get(role, set()).discard(websocket)