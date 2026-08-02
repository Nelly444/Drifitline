from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_connect_receives_connected_message():
    with client.websocket_connect("/ws/alerts") as websocket:
        data = websocket.receive_json()
        assert data == {"type": "connected"}


def test_multiple_connections_coexist():
    with client.websocket_connect("/ws/alerts") as first, client.websocket_connect("/ws/alerts") as second:
        assert first.receive_json() == {"type": "connected"}
        assert second.receive_json() == {"type": "connected"}
