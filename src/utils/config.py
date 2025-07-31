"""
Configuration management for the AI Agent
"""
import os
from typing import Optional
from dotenv import load_dotenv

class Config:
    """Configuration class for managing application settings"""
    
    def __init__(self):
        """Initialize config for Docker-only deployment"""
        # LLM Provider Configuration
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google").strip().split('#')[0].strip()
        
        # OpenAI Configuration
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # Anthropic Configuration
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        # Google Configuration (Default)
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        self.GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
        
        # Ollama Configuration
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        
        # Application Configuration
        self.APP_NAME = os.getenv("APP_NAME", "AgentVisa")
        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DOCKER_MODE = os.getenv("DOCKER_MODE", "false").lower() == "true"
        
        # Server Configuration (Docker internal)
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
        
        # API Configuration (Docker service communication)
        self.API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
        
        # Database Configuration (PostgreSQL only in Docker)
        self.DATABASE_TYPE = "postgresql"
        self.DATABASE_PATH = os.getenv("DATABASE_PATH", "data/app.db")  # Fallback for local development
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
        
        # Handle POSTGRES_PORT which might be a service URL in Kubernetes
        postgres_port_env = os.getenv("POSTGRES_PORT", "5432")
        if postgres_port_env.startswith("tcp://"):
            # Extract port from service URL format: tcp://ip:port
            self.POSTGRES_PORT = int(postgres_port_env.split(":")[-1])
        else:
            self.POSTGRES_PORT = int(postgres_port_env)
            
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "visa_app")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
        
        # Redis Configuration
        self.REDIS_HOST = os.getenv("REDIS_HOST", "redis")
        
        # Handle REDIS_PORT which might be a service URL in Kubernetes
        redis_port_env = os.getenv("REDIS_PORT", "6379")
        if redis_port_env.startswith("tcp://"):
            # Extract port from service URL format: tcp://ip:port
            self.REDIS_PORT = int(redis_port_env.split(":")[-1])
        else:
            self.REDIS_PORT = int(redis_port_env)
            
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis_password")
        
        # Build DATABASE_URL from components
        self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    
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
    """Get configuration instance for Docker deployment"""
    # Load environment variables from .env file
    load_dotenv(override=force_reload)
    config = Config()
    config.validate_config(config.LLM_PROVIDER)
    return config