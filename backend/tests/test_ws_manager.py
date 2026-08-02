import uuid

import pytest

from app.ws.manager import ConnectionManager


class FakeWebSocket:
    def __init__(self, raise_on_send: bool = False) -> None:
        self.raise_on_send = raise_on_send
        self.sent: list[dict] = []

    async def accept(self) -> None:
        pass

    async def send_json(self, message: dict) -> None:
        if self.raise_on_send:
            raise RuntimeError("connection closed")
        self.sent.append(message)


USER_A = uuid.uuid4()
USER_B = uuid.uuid4()


@pytest.mark.asyncio
async def test_broadcast_delivers_to_all_sockets_for_that_user():
    manager = ConnectionManager()
    a, b = FakeWebSocket(), FakeWebSocket()
    await manager.connect(a, USER_A)
    await manager.connect(b, USER_A)

    await manager.broadcast_to_user(USER_A, {"type": "new_alert"})

    assert a.sent == [{"type": "new_alert"}]
    assert b.sent == [{"type": "new_alert"}]


@pytest.mark.asyncio
async def test_broadcast_never_reaches_a_different_user():
    manager = ConnectionManager()
    a, b = FakeWebSocket(), FakeWebSocket()
    await manager.connect(a, USER_A)
    await manager.connect(b, USER_B)

    await manager.broadcast_to_user(USER_A, {"type": "new_alert"})

    assert a.sent == [{"type": "new_alert"}]
    assert b.sent == []


@pytest.mark.asyncio
async def test_broadcast_prunes_failing_socket_without_dropping_others():
    manager = ConnectionManager()
    dead, alive = FakeWebSocket(raise_on_send=True), FakeWebSocket()
    await manager.connect(dead, USER_A)
    await manager.connect(alive, USER_A)

    await manager.broadcast_to_user(USER_A, {"type": "new_alert"})

    assert alive.sent == [{"type": "new_alert"}]
    assert dead not in manager.active.get(USER_A, set())


@pytest.mark.asyncio
async def test_disconnect_removes_socket_and_empty_user_entry():
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.connect(ws, USER_A)

    manager.disconnect(ws, USER_A)

    assert USER_A not in manager.active
