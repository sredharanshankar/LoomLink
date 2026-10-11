import pytest
from unittest.mock import MagicMock, patch
from app.core.events import subscribe, publish, _handlers


def test_subscribe_stores_handler():
    received = []
    subscribe("test.event", lambda s, e: received.append(e))
    assert "test.event" in _handlers
    assert len(_handlers["test.event"]) >= 1


def test_subscribe_prefix_stored():
    subscribe("stock.", lambda s, e: None)
    assert "stock." in _handlers


def test_publish_inserts_to_db():
    mock_session = MagicMock()
    mock_scalar = MagicMock(return_value=42)
    mock_session.execute.return_value.scalar = mock_scalar

    with patch("app.core.events._dispatch_queue"), \
         patch("sqlalchemy.event.listens_for", return_value=lambda f: f):
        publish(mock_session, "stock.updated", {"item": "yarn"}, actor_id=None)

    assert mock_session.execute.called
    # First execute call is the INSERT INTO domain_events; verify via params
    first_call = mock_session.execute.call_args_list[0]
    params = first_call[0][1] if len(first_call[0]) > 1 else first_call.kwargs.get("params", {})
    assert "etype" in params
    assert params["etype"] == "stock.updated"