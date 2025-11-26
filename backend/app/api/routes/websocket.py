"""WebSocket routes for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

from app.infrastructure.observability.events import event_bus
from app.infrastructure.observability.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_connections=len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", total_connections=len(self.active_connections))
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_error", error=str(e))
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)


connection_manager = ConnectionManager()


# Subscribe to events
async def event_handler(data: dict):
    """Handle events from event bus"""
    await connection_manager.broadcast(data)


# Subscribe to job events
event_bus.subscribe("job_submitted", event_handler)
event_bus.subscribe("job_started", event_handler)
event_bus.subscribe("job_completed", event_handler)
event_bus.subscribe("job_failed", event_handler)
event_bus.subscribe("job_retry", event_handler)
event_bus.subscribe("job_dlq", event_handler)
event_bus.subscribe("metrics_updated", event_handler)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            # Echo back or handle client messages
            await websocket.send_json({"type": "pong", "message": "connected"})
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        connection_manager.disconnect(websocket)

