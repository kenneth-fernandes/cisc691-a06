"""
WebSocket models for real-time communication
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class MessageType(str, Enum):
    """WebSocket message types"""
    CHAT = "chat"
    SYSTEM = "system"
    ERROR = "error"
    TYPING = "typing"
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    AGENT_RESPONSE = "agent_response"


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: MessageType
    timestamp: datetime
    session_id: str
    data: Dict[str, Any]


class ChatMessage(BaseModel):
    """Chat message for WebSocket"""
    message: str
    session_id: str
    config: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class ChatResponse(BaseModel):
    """Chat response for WebSocket"""
    response: str
    session_id: str
    conversation_history: Optional[List[Dict[str, Any]]] = None
    response_time: Optional[float] = None
    timestamp: Optional[datetime] = None


class SystemMessage(BaseModel):
    """System message for WebSocket"""
    message: str
    level: str = "info"  # info, warning, error
    timestamp: Optional[datetime] = None


class TypingIndicator(BaseModel):
    """Typing indicator for WebSocket"""
    session_id: str
    is_typing: bool
    timestamp: Optional[datetime] = None


class ConnectionInfo(BaseModel):
    """WebSocket connection information"""
    session_id: str
    connected_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class HeartbeatMessage(BaseModel):
    """Heartbeat message for connection monitoring"""
    timestamp: datetime
    session_id: str


class ErrorMessage(BaseModel):
    """Error message for WebSocket"""
    error: str
    error_code: Optional[str] = None
    session_id: str
    timestamp: Optional[datetime] = None