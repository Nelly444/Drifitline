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
    # Browsers don't send an Origin header on same-origin requests they
    # control, but a cross-site page opening this socket would - reject those
    # outright. Non-browser clients (tests, curl, other tools) send no Origin
    # at all, so absence is allowed through to auth itself.
    origin = websocket.headers.get("origin")
    if origin is not None and origin != get_settings().FRONTEND_ORIGIN:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    # Browsers can't set an Authorization header on a WS handshake, and a
    # `?token=` query param would leak into server/proxy access logs - so the
    # token travels as the client's first message after the connection opens.
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
