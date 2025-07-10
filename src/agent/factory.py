"""
Agent factory for creating different types of AI agents
"""
from .core import AIAgent
from ..utils.config import get_config

def create_agent(agent_type: str = "default", provider: str = None) -> AIAgent:
    """Factory function to create different types of agents"""
    config = get_config()
    
    # Use provider from config if not specified
    if provider is None:
        provider = config.LLM_PROVIDER
    
    # Get model name based on provider
    model_name = config.get_model_for_provider(provider)
    
    if agent_type == "default":
        return AIAgent(
            provider=provider,
            model_name=model_name,
            temperature=0.7
        )
    elif agent_type == "creative":
        return AIAgent(
            provider=provider,
            model_name=model_name,
            temperature=0.9
        )
    elif agent_type == "analytical":
        return AIAgent(
            provider=provider,
            model_name=model_name,
            temperature=0.3
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

def get_available_agent_types() -> list:
    """Return list of available agent types"""
    return ["default", "creative", "analytical"]