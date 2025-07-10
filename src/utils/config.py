"""
Configuration management for the AI Agent
"""
import os
from typing import Optional
from dotenv import load_dotenv

class Config:
    """Configuration class for managing application settings"""
    
    def __init__(self):
        """Initialize config after loading environment variables"""
        # LLM Provider Configuration
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().split('#')[0].strip()
        
        # OpenAI Configuration (PAID - you have Plus)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # Latest model
        
        # Anthropic Configuration (PAID - you have Pro)
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")  # Latest model
        
        # Google Configuration (FREE TIER)
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")  # Free tier model
        
        # Ollama Configuration (LOCAL - FREE)
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # Local model
        
        # Application Configuration
        self.APP_NAME = os.getenv("APP_NAME", "AI Agent")
        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Server Configuration
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
    
    def validate_config(self, provider: str = None) -> bool:
        """Validate that required configuration is present"""
        provider = provider or self.LLM_PROVIDER
        
        if provider == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required but not set")
        elif provider == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required but not set")
        elif provider == "google" and not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required but not set")
        
        return True
    
    def get_model_for_provider(self, provider: str) -> str:
        """Get default model for specified provider"""
        if provider == "openai":
            return self.OPENAI_MODEL
        elif provider == "anthropic":
            return self.ANTHROPIC_MODEL
        elif provider == "google":
            return self.GOOGLE_MODEL
        elif provider == "ollama":
            return self.OLLAMA_MODEL
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @staticmethod
    def get_supported_providers() -> list:
        """Get list of supported providers"""
        return ["openai", "anthropic", "google", "ollama"]

def get_config(force_reload: bool = True) -> Config:
    """Get configuration instance"""
    # Load environment variables from .env file (always override by default)
    load_dotenv(override=force_reload)
    config = Config()
    config.validate_config(config.LLM_PROVIDER)
    return config