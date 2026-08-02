from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        # Iterate a copy and prune failing sockets individually so one dead
        # connection doesn't stop the broadcast from reaching everyone else.
        for websocket in list(self.active):
            try:
                await websocket.send_json(message)
            except Exception:
                self.active.discard(websocket)


manager = ConnectionManager()
