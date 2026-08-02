from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.auth import UserManager, get_jwt_strategy, get_user_manager
from app.ws.manager import manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/alerts")
async def alerts_socket(
    websocket: WebSocket,
    token: str | None = None,
    user_manager: UserManager = Depends(get_user_manager),
) -> None:
    strategy = get_jwt_strategy()
    user = await strategy.read_token(token, user_manager) if token else None
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
