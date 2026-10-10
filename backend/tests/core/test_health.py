from unittest.mock import MagicMock, patch


def test_health_returns_ok(client):
    with patch("app.deps.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
