"""
Agent factory for creating different types of AI agents
"""
from src.agent.core import AIAgent
from src.utils.config import get_config
from typing import Dict, Any

# Agent type configurations
AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "default": {"temperature": 0.7},
    "creative": {"temperature": 0.9},
    "analytical": {"temperature": 0.3}
}

def create_agent(agent_type: str = "default", provider: str = None, mode: str = "general") -> AIAgent:
    """Factory function to create different types of agents"""
    if agent_type not in AGENT_CONFIGS:
        raise ValueError(f"Unknown agent type: {agent_type}")
        
    config = get_config()
    provider = provider or config.LLM_PROVIDER
    model_name = config.get_model_for_provider(provider)
    
    return AIAgent(
        provider=provider,
        model_name=model_name,
        temperature=AGENT_CONFIGS[agent_type]["temperature"],
        mode=mode
    )

def get_available_agent_types() -> list:
    """Return list of available agent types"""
    return ["default", "creative", "analytical"]

def get_available_modes() -> list:
    """Return list of available agent modes"""
    return ["general", "visa_expert"]