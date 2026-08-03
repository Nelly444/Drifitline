import uuid

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        self.active.setdefault(user_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        sockets = self.active.get(user_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if not sockets:
            del self.active[user_id]

    async def broadcast_to_user(self, user_id: uuid.UUID, message: dict) -> None:
        for websocket in list(self.active.get(user_id, ())):
            try:
                await websocket.send_json(message)
            except Exception:
                self.active[user_id].discard(websocket)


manager = ConnectionManager()
