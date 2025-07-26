"""
Pydantic models for agent API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AgentConfig(BaseModel):
    """Agent configuration"""
    agent_type: str = Field(default="default", description="Agent type: default, creative, analytical")
    provider: str = Field(default="google", description="LLM provider: openai, anthropic, google, ollama")
    mode: str = Field(default="general", description="Agent mode: general, visa_expert")

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session ID for conversation tracking")
    config: Optional[AgentConfig] = Field(None, description="Optional agent configuration")

class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str = Field(..., description="Message role (user, assistant)")
    content: str = Field(..., description="Message content")

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    conversation_history: List[ConversationMessage] = Field(default_factory=list, description="Recent conversation history")

class ConversationHistory(BaseModel):
    """Conversation history model"""
    session_id: str = Field(..., description="Session ID")
    messages: List[ConversationMessage] = Field(default_factory=list, description="Conversation messages")

class AgentConfigRequest(BaseModel):
    """Agent configuration request"""
    session_id: str = Field(..., description="Session ID")
    config: AgentConfig = Field(..., description="Agent configuration")

class ProviderListResponse(BaseModel):
    """Supported providers response"""
    providers: List[str] = Field(..., description="List of supported LLM providers")