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

    with patch("app.core.events._dispatch_queue") as mock_q:
        publish(mock_session, "stock.updated", {"item": "yarn"}, actor_id=None)

    assert mock_session.execute.called
    # The INSERT INTO domain_events call happened
    call_args = mock_session.execute.call_args_list[0]
    assert "domain_events" in str(call_args)