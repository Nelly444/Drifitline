import asyncio
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.auth import UserManager, get_jwt_strategy, get_user_manager
from app.config import get_settings
from app.ws.manager import manager

router = APIRouter(tags=["ws"])

AUTH_TIMEOUT_SECONDS = 5


@router.websocket("/ws/alerts")
async def alerts_socket(
    websocket: WebSocket,
    user_manager: UserManager = Depends(get_user_manager),
) -> None:
    origin = websocket.headers.get("origin")
    if origin is not None and origin != get_settings().FRONTEND_ORIGIN:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=AUTH_TIMEOUT_SECONDS)
        token = json.loads(raw)["token"]
    except (TimeoutError, WebSocketDisconnect, ValueError, KeyError, TypeError):
        await websocket.close(code=1008)
        return

    strategy = get_jwt_strategy()
    user = await strategy.read_token(token, user_manager)
    if user is None or not user.is_active:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user.id)
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
