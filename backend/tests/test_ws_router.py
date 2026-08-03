import asyncio
import uuid

import pytest
from fastapi_users import exceptions
from starlette.websockets import WebSocketDisconnect

from app.auth import get_jwt_strategy, get_user_manager
from app.main import app

from fastapi.testclient import TestClient

client = TestClient(app)


class FakeUser:
    def __init__(self, id, is_active=True):
        self.id = id
        self.is_active = is_active


class FakeUserManager:
    def __init__(self, users_by_id):
        self.users_by_id = users_by_id

    def parse_id(self, value):
        return uuid.UUID(str(value))

    async def get(self, user_id):
        user = self.users_by_id.get(user_id)
        if user is None:
            raise exceptions.UserNotExists()
        return user


def _token_for(user) -> str:
    strategy = get_jwt_strategy()
    return asyncio.run(strategy.write_token(user))


@pytest.fixture
def user_a():
    return FakeUser(id=uuid.uuid4())


@pytest.fixture
def user_b():
    return FakeUser(id=uuid.uuid4())


@pytest.fixture(autouse=True)
def override_user_manager(user_a, user_b):
    fake_manager = FakeUserManager({user_a.id: user_a, user_b.id: user_b})
    app.dependency_overrides[get_user_manager] = lambda: fake_manager
    yield
    app.dependency_overrides.pop(get_user_manager, None)


def test_connect_without_sending_a_token_is_rejected():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/alerts") as websocket:
            websocket.receive_json()


def test_connect_with_non_json_first_message_is_rejected():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/alerts") as websocket:
            websocket.send_text("not-json")
            websocket.receive_json()


def test_connect_with_garbage_token_is_rejected():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/alerts") as websocket:
            websocket.send_json({"token": "not-a-real-jwt"})
            websocket.receive_json()


def test_connect_with_valid_token_receives_connected_message(user_a):
    token = _token_for(user_a)
    with client.websocket_connect("/ws/alerts") as websocket:
        websocket.send_json({"token": token})
        data = websocket.receive_json()
        assert data == {"type": "connected"}


def test_two_different_users_can_connect_simultaneously(user_a, user_b):
    token_a = _token_for(user_a)
    token_b = _token_for(user_b)
    with (
        client.websocket_connect("/ws/alerts") as first,
        client.websocket_connect("/ws/alerts") as second,
    ):
        first.send_json({"token": token_a})
        second.send_json({"token": token_b})
        assert first.receive_json() == {"type": "connected"}
        assert second.receive_json() == {"type": "connected"}


def test_connect_with_mismatched_origin_is_rejected(user_a):
    token = _token_for(user_a)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws/alerts", headers={"origin": "http://evil.example.com"}
        ) as websocket:
            websocket.send_json({"token": token})
            websocket.receive_json()
