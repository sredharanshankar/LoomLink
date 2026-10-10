"""WebSocket broadcast receives published domain events."""
import json
import pytest
from unittest.mock import AsyncMock
from app.api.v1.ws import _ws_broadcast


@pytest.mark.asyncio
async def test_broadcast_skips_buyer_role():
    from app.api.v1.ws import _connections
    buyer_ws = AsyncMock()
    _connections["buyer"] = {buyer_ws}
    await _ws_broadcast("stock.updated", {"qty": 100})
    buyer_ws.send_text.assert_not_called()
    _connections.pop("buyer", None)


@pytest.mark.asyncio
async def test_broadcast_sends_to_non_buyer_role():
    from app.api.v1.ws import _connections
    owner_ws = AsyncMock()
    _connections["owner"] = {owner_ws}
    await _ws_broadcast("stock.updated", {"qty": 50})
    owner_ws.send_text.assert_called_once()
    msg = json.loads(owner_ws.send_text.call_args[0][0])
    assert msg["type"] == "stock.updated"
    assert msg["payload"]["qty"] == 50
    _connections.pop("owner", None)


@pytest.mark.asyncio
async def test_broadcast_removes_dead_socket():
    from app.api.v1.ws import _connections
    dead_ws = AsyncMock()
    dead_ws.send_text.side_effect = Exception("connection closed")
    _connections["manager"] = {dead_ws}
    await _ws_broadcast("test.event", {})
    assert dead_ws not in _connections.get("manager", set())
    _connections.pop("manager", None)
