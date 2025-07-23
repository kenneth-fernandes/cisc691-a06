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

def test_docker_mode_setting(mock_env):
    """Test Docker mode configuration"""
    config = Config()
    assert config.DOCKER_MODE is True

def test_local_mode_settings(monkeypatch):
    """Test local mode configuration"""
    monkeypatch.setenv("DOCKER_MODE", "False")
    monkeypatch.setenv("DATABASE_TYPE", "sqlite")
    config = Config()
    assert config.DOCKER_MODE is False
    assert config.DATABASE_TYPE == "sqlite"