"""
WebSocket endpoints for real-time agent communication
"""
import asyncio
import json
import time
import uuid
from typing import Dict, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, HTTPException
from fastapi.websockets import WebSocketState
import logging

from api.models.websocket import (
    MessageType, WebSocketMessage, ChatMessage, ChatResponse,
    SystemMessage, TypingIndicator, ConnectionInfo, HeartbeatMessage, ErrorMessage
)
from api.routers.agent import get_or_create_agent
from api.models.agent import AgentConfig

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        # Active connections: session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Connection info: session_id -> ConnectionInfo
        self.connection_info: Dict[str, ConnectionInfo] = {}
        # Typing indicators: session_id -> bool
        self.typing_status: Dict[str, bool] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_agent: str = None, ip_address: str = None):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        # Store connection
        self.active_connections[session_id] = websocket
        self.connection_info[session_id] = ConnectionInfo(
            session_id=session_id,
            connected_at=datetime.now(),
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        logger.info(f"WebSocket connected: {session_id}")
        
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type=MessageType.SYSTEM,
            timestamp=datetime.now(),
            session_id=session_id,
            data={
                "message": "Connected to AI Agent WebSocket",
                "level": "info"
            }
        )
        await self.send_personal_message(welcome_msg.dict(), websocket)
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.connection_info:
            del self.connection_info[session_id]
        if session_id in self.typing_status:
            del self.typing_status[session_id]
        
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def send_message_to_session(self, message: dict, session_id: str):
        """Send message to specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await self.send_personal_message(message, websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            try:
                await self.send_personal_message(message, websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to {session_id}: {e}")
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            self.disconnect(session_id)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self, session_id: str) -> ConnectionInfo:
        """Get connection info for session"""
        return self.connection_info.get(session_id)
    
    def is_connected(self, session_id: str) -> bool:
        """Check if session is connected"""
        return session_id in self.active_connections
    
    async def set_typing_status(self, session_id: str, is_typing: bool):
        """Set typing status for session"""
        self.typing_status[session_id] = is_typing
        
        # Send typing indicator
        typing_msg = WebSocketMessage(
            type=MessageType.TYPING,
            timestamp=datetime.now(),
            session_id=session_id,
            data={
                "is_typing": is_typing
            }
        )
        await self.send_message_to_session(typing_msg.dict(), session_id)


# Global connection manager
connection_manager = ConnectionManager()


async def verify_websocket_auth(websocket: WebSocket, session_id: str = None):
    """Verify WebSocket authentication"""
    # For now, just verify session_id is provided
    if not session_id:
        await websocket.close(code=4001, reason="Session ID required")
        raise HTTPException(status_code=401, detail="Session ID required")
    
    return session_id


@router.websocket("/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str = Depends(verify_websocket_auth)
):
    """WebSocket endpoint for real-time agent chat"""
    try:
        # Get client info
        user_agent = websocket.headers.get("user-agent")
        ip_address = websocket.client.host if websocket.client else None
        
        # Connect to WebSocket
        await connection_manager.connect(websocket, session_id, user_agent, ip_address)
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat_loop(websocket, session_id))
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process different message types
                message_type = message_data.get("type")
                
                if message_type == MessageType.CHAT:
                    await handle_chat_message(websocket, session_id, message_data)
                elif message_type == MessageType.TYPING:
                    await handle_typing_indicator(session_id, message_data)
                elif message_type == MessageType.HEARTBEAT:
                    await handle_heartbeat(websocket, session_id)
                else:
                    await send_error_message(websocket, session_id, f"Unknown message type: {message_type}")
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket client {session_id} disconnected normally")
        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {e}")
            await send_error_message(websocket, session_id, f"Internal error: {str(e)}")
        
        finally:
            # Cancel heartbeat task
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
    
    finally:
        # Clean up connection
        connection_manager.disconnect(session_id)


async def handle_chat_message(websocket: WebSocket, session_id: str, message_data: dict):
    """Handle chat message from WebSocket"""
    try:
        # Parse chat message
        chat_msg = ChatMessage(
            message=message_data.get("message"),
            session_id=session_id,
            config=message_data.get("config"),
            timestamp=datetime.now()
        )
        
        # Set typing indicator for agent
        await connection_manager.set_typing_status(session_id, True)
        
        # Get agent and process message
        start_time = time.time()
        
        agent_config = None
        if chat_msg.config:
            agent_config = AgentConfig(**chat_msg.config)
        
        agent = get_or_create_agent(session_id, agent_config)
        response_text = agent.chat(chat_msg.message)
        conversation_history = agent.get_conversation_history()
        
        response_time = time.time() - start_time
        
        # Clear typing indicator
        await connection_manager.set_typing_status(session_id, False)
        
        # Send response
        response_msg = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            timestamp=datetime.now(),
            session_id=session_id,
            data={
                "response": response_text,
                "response_time": response_time,
                "conversation_history": conversation_history[-10:] if conversation_history else []
            }
        )
        
        await connection_manager.send_personal_message(response_msg.dict(), websocket)
        
        logger.info(f"WebSocket chat processed for {session_id} in {response_time:.2f}s")
    
    except Exception as e:
        await connection_manager.set_typing_status(session_id, False)
        await send_error_message(websocket, session_id, f"Chat processing error: {str(e)}")


async def handle_typing_indicator(session_id: str, message_data: dict):
    """Handle typing indicator from client"""
    is_typing = message_data.get("is_typing", False)
    await connection_manager.set_typing_status(session_id, is_typing)


async def handle_heartbeat(websocket: WebSocket, session_id: str):
    """Handle heartbeat message"""
    heartbeat_response = WebSocketMessage(
        type=MessageType.HEARTBEAT,
        timestamp=datetime.now(),
        session_id=session_id,
        data={"status": "alive"}
    )
    await connection_manager.send_personal_message(heartbeat_response.dict(), websocket)


async def send_error_message(websocket: WebSocket, session_id: str, error: str):
    """Send error message to WebSocket"""
    error_msg = WebSocketMessage(
        type=MessageType.ERROR,
        timestamp=datetime.now(),
        session_id=session_id,
        data={
            "error": error,
            "error_code": "WEBSOCKET_ERROR"
        }
    )
    await connection_manager.send_personal_message(error_msg.dict(), websocket)


async def heartbeat_loop(websocket: WebSocket, session_id: str, interval: int = 30):
    """Send periodic heartbeat to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(interval)
            if connection_manager.is_connected(session_id):
                await handle_heartbeat(websocket, session_id)
            else:
                break
    except asyncio.CancelledError:
        logger.info(f"Heartbeat loop cancelled for {session_id}")
    except Exception as e:
        logger.error(f"Heartbeat error for {session_id}: {e}")


# WebSocket management endpoints
@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "active_connections": connection_manager.get_connection_count(),
        "connection_info": {
            session_id: {
                "connected_at": info.connected_at,
                "user_agent": info.user_agent,
                "ip_address": info.ip_address
            }
            for session_id, info in connection_manager.connection_info.items()
        },
        "typing_status": connection_manager.typing_status
    }


@router.post("/broadcast")
async def broadcast_message(message: SystemMessage):
    """Broadcast system message to all WebSocket connections"""
    broadcast_msg = WebSocketMessage(
        type=MessageType.SYSTEM,
        timestamp=datetime.now(),
        session_id="system",
        data=message.dict()
    )
    
    await connection_manager.broadcast(broadcast_msg.dict())
    
    return {
        "message": "Message broadcasted",
        "recipients": connection_manager.get_connection_count()
    }


@router.delete("/disconnect/{session_id}")
async def force_disconnect_session(session_id: str):
    """Force disconnect a WebSocket session"""
    if connection_manager.is_connected(session_id):
        websocket = connection_manager.active_connections[session_id]
        await websocket.close(code=4000, reason="Force disconnect")
        connection_manager.disconnect(session_id)
        return {"message": f"Session {session_id} disconnected"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")