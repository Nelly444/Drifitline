from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await websocket.send_json({"type": "connected"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
