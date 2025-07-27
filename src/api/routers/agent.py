"""
AI Agent API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from api.models.agent import (
    ChatRequest, ChatResponse, AgentConfig, ConversationHistory,
    AgentConfigRequest, ProviderListResponse
)
from agent.factory import create_agent
from agent.core import AIAgent

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session storage (in production, use Redis or database)
agent_sessions = {}

def get_or_create_agent(session_id: str, config: Optional[AgentConfig] = None) -> AIAgent:
    """Get existing agent or create new one for session"""
    if session_id not in agent_sessions or config:
        if config:
            agent = create_agent(
                agent_type=config.agent_type,
                provider=config.provider,
                mode=config.mode
            )
        else:
            agent = create_agent("default")
        agent_sessions[session_id] = agent
        logger.info(f"Created new agent for session {session_id}")
    
    return agent_sessions[session_id]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Chat with the AI agent"""
    try:
        agent = get_or_create_agent(request.session_id, request.config)
        
        # Get response from agent
        response_text = agent.chat(request.message)
        
        # Get conversation history
        history = agent.get_conversation_history()
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            conversation_history=history[-10:]  # Last 10 messages
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/conversation/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = agent_sessions[session_id]
    history = agent.get_conversation_history()
    
    return ConversationHistory(
        session_id=session_id,
        messages=history
    )

@router.delete("/conversation/{session_id}")
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = agent_sessions[session_id]
    agent.clear_history()
    
    return {"message": f"Conversation history cleared for session {session_id}"}

@router.post("/configure")
async def configure_agent(request: AgentConfigRequest):
    """Configure agent for a session"""
    try:
        agent = create_agent(
            agent_type=request.config.agent_type,
            provider=request.config.provider,
            mode=request.config.mode
        )
        agent_sessions[request.session_id] = agent
        
        return {"message": f"Agent configured for session {request.session_id}"}
        
    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent configuration failed: {str(e)}")

@router.get("/providers", response_model=ProviderListResponse)
async def get_supported_providers():
    """Get list of supported LLM providers"""
    return ProviderListResponse(
        providers=AIAgent.get_supported_providers()
    )

@router.get("/status/{session_id}")
async def get_agent_status(session_id: str):
    """Get agent status for a session"""
    if session_id not in agent_sessions:
        return {"session_exists": False, "message": "Session not found"}
    
    agent = agent_sessions[session_id]
    history_count = len(agent.get_conversation_history())
    
    return {
        "session_exists": True,
        "provider": agent.provider,
        "model": agent.model_name,
        "mode": agent.mode,
        "message_count": history_count
    }