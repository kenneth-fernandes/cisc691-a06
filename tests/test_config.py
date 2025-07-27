"""Tests for configuration management"""
import os
import pytest
from src.utils.config import Config

@pytest.fixture
def mock_env(monkeypatch):
    """Setup mock environment variables"""
    env_vars = {
        "DOCKER_MODE": "True",
        "DATABASE_TYPE": "postgresql",
        "POSTGRES_HOST": "test-db",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_pass",
        "REDIS_HOST": "test-redis",
        "REDIS_PORT": "6380",
        "REDIS_PASSWORD": "test_redis_pass",
        "MONGO_HOST": "test-mongodb",
        "MONGO_PORT": "27017",
        "MONGO_DB": "test_db",
        "MONGO_USER": "test_user",
        "MONGO_PASSWORD": "test_pass"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

def test_config_loads_database_settings(mock_env):
    """Test database configuration loading"""
    config = Config()
    assert config.DATABASE_TYPE == "postgresql"
    assert config.POSTGRES_HOST == "test-db"
    assert config.POSTGRES_PORT == 5432
    assert config.POSTGRES_DB == "test_db"
    assert config.POSTGRES_USER == "test_user"
    assert config.POSTGRES_PASSWORD == "test_pass"

def test_config_loads_redis_settings(mock_env):
    """Test Redis configuration loading"""
    config = Config()
    assert config.REDIS_HOST == "test-redis"
    assert config.REDIS_PORT == 6380
    assert config.REDIS_PASSWORD == "test_redis_pass"

def test_config_loads_mongodb_settings(mock_env):
    """Test MongoDB configuration loading"""
    config = Config()
    assert config.MONGO_HOST == "test-mongodb"
    assert config.MONGO_PORT == 27017
    assert config.MONGO_DB == "test_db"
    assert config.MONGO_USER == "test_user"
    assert config.MONGO_PASSWORD == "test_pass"

def test_docker_mode_configuration(mock_env):
    """Test Docker-only configuration (no DOCKER_MODE attribute needed)"""
    config = Config()
    # Docker mode is the default and only mode now
    assert config.DATABASE_TYPE == "postgresql"
    assert config.POSTGRES_HOST == "test-db"
    assert config.API_BASE_URL  # Should have API base URL

def test_llm_provider_settings(monkeypatch):
    """Test LLM provider configuration"""
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_MODEL", "gemini-1.5-flash")
    config = Config()
    assert config.LLM_PROVIDER == "google"
    assert config.GOOGLE_API_KEY == "test-key"
    assert config.GOOGLE_MODEL == "gemini-1.5-flash"