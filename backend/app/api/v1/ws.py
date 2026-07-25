import asyncio
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger("astrax.ws")
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"Client {client_id} connected via WebSocket")

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_text(message)

    async def broadcast(self, message: str):
        for client_id, connections in self.active_connections.items():
            for connection in connections:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Simple echo or process incoming commands
            await manager.send_personal_message(f"Message text was: {data}", client_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected")
