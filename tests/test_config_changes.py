"""
Tests for configuration changes made during API-first architecture implementation
"""
import pytest
import os
from unittest.mock import patch
from utils.config import Config


class TestRedisConfiguration:
    """Test Redis configuration changes"""
    
    def test_redis_default_port_configuration(self):
        """Test that Redis default port is now 6379"""
        config = Config()
        assert config.REDIS_PORT == 6379
        assert config.REDIS_HOST == "redis"
        assert config.REDIS_PASSWORD == "redis_password"
    
    @patch.dict(os.environ, {
        'REDIS_HOST': 'test-redis',
        'REDIS_PORT': '6380',
        'REDIS_PASSWORD': 'test-password'
    })
    def test_redis_environment_override(self):
        """Test Redis configuration from environment variables"""
        config = Config()
        assert config.REDIS_HOST == "test-redis"
        assert config.REDIS_PORT == 6380
        assert config.REDIS_PASSWORD == "test-password"
    
    def test_redis_configuration_types(self):
        """Test Redis configuration data types"""
        config = Config()
        assert isinstance(config.REDIS_PORT, int)
        assert isinstance(config.REDIS_HOST, str)
        assert isinstance(config.REDIS_PASSWORD, str)



class TestPostgreSQLConfiguration:
    """Test PostgreSQL configuration"""
    
    def test_postgresql_default_configuration(self):
        """Test PostgreSQL default configuration"""
        config = Config()
        assert config.POSTGRES_HOST == "db"
        assert config.POSTGRES_PORT == 5432
        assert config.POSTGRES_DB == "app_db"
        assert config.POSTGRES_USER == "admin"
        assert config.POSTGRES_PASSWORD == "password"
    
    def test_database_type_setting(self):
        """Test database type is set to postgresql"""
        config = Config()
        assert config.DATABASE_TYPE == "postgresql"


class TestAPIConfiguration:
    """Test API configuration changes"""
    
    def test_api_base_url_configuration(self):
        """Test API base URL for Docker service communication"""
        config = Config()
        assert config.API_BASE_URL == "http://api:8000"
    
    @patch.dict(os.environ, {'API_BASE_URL': 'http://custom-api:9000'})
    def test_api_base_url_override(self):
        """Test API base URL override"""
        config = Config()
        assert config.API_BASE_URL == "http://custom-api:9000"
    
    def test_server_configuration(self):
        """Test server host and port configuration"""
        config = Config()
        assert config.HOST == "0.0.0.0"
        assert config.PORT == 8000


class TestLLMProviderConfiguration:
    """Test LLM provider configuration"""
    
    def test_default_llm_provider(self):
        """Test default LLM provider is Google"""
        config = Config()
        assert config.LLM_PROVIDER == "google"
    
    def test_google_model_configuration(self):
        """Test Google model configuration"""
        config = Config()
        assert config.GOOGLE_MODEL == "gemini-1.5-flash"
    
    def test_ollama_configuration(self):
        """Test Ollama configuration for Docker"""
        config = Config()
        assert config.OLLAMA_BASE_URL == "http://host.docker.internal:11434"
        assert config.OLLAMA_MODEL == "llama3.2"
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'openai'})
    def test_llm_provider_override(self):
        """Test LLM provider override"""
        config = Config()
        assert config.LLM_PROVIDER == "openai"


class TestApplicationConfiguration:
    """Test application configuration"""
    
    def test_app_defaults(self):
        """Test application default settings"""
        config = Config()
        assert config.APP_NAME == "AgentVisa"
        assert config.APP_VERSION == "1.0.0"
        assert config.DEBUG == False
        assert config.LOG_LEVEL == "INFO"
    
    @patch.dict(os.environ, {'DEBUG': 'true', 'LOG_LEVEL': 'DEBUG'})
    def test_debug_configuration(self):
        """Test debug configuration"""
        config = Config()
        assert config.DEBUG == True
        assert config.LOG_LEVEL == "DEBUG"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])