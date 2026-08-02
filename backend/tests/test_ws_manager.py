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


@pytest.mark.asyncio
async def test_broadcast_delivers_to_all_connected_sockets():
    manager = ConnectionManager()
    a, b = FakeWebSocket(), FakeWebSocket()
    await manager.connect(a)
    await manager.connect(b)

    await manager.broadcast({"type": "new_alert"})

    assert a.sent == [{"type": "new_alert"}]
    assert b.sent == [{"type": "new_alert"}]


@pytest.mark.asyncio
async def test_broadcast_prunes_failing_socket_without_dropping_others():
    manager = ConnectionManager()
    dead, alive = FakeWebSocket(raise_on_send=True), FakeWebSocket()
    await manager.connect(dead)
    await manager.connect(alive)

    await manager.broadcast({"type": "new_alert"})

    assert alive.sent == [{"type": "new_alert"}]
    assert dead not in manager.active


@pytest.mark.asyncio
async def test_disconnect_removes_socket():
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.connect(ws)

    manager.disconnect(ws)

    assert ws not in manager.active
