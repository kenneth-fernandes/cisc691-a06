"""
Tests for Docker Configuration Changes

This module tests the Docker mode detection and configuration changes
made to utils/config.py as part of issues #25 and #27.
"""

import pytest
from unittest.mock import Mock, patch
import os

from utils.config import Config, get_config


class TestConfigDockerMode:
    """Test Docker mode detection and configuration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Store original environment variables
        self.original_env = {}
        docker_related_vars = [
            'DOCKER_MODE', 'DATABASE_PATH', 'HOST', 'PORT', 'API_BASE_URL',
            'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
            'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD',
            'MONGO_HOST', 'MONGO_PORT', 'MONGO_DB', 'MONGO_USER', 'MONGO_PASSWORD',
            'OLLAMA_BASE_URL'
        ]
        
        for var in docker_related_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def teardown_method(self):
        """Clean up after tests"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    def test_docker_mode_disabled_by_default(self):
        """Test that Docker mode is disabled by default"""
        config = Config()
        assert config.DOCKER_MODE is False
    
    def test_docker_mode_enabled_explicitly(self):
        """Test enabling Docker mode explicitly"""
        os.environ['DOCKER_MODE'] = 'true'
        config = Config()
        assert config.DOCKER_MODE is True
    
    def test_docker_mode_case_insensitive(self):
        """Test that Docker mode setting is case insensitive"""
        test_cases = ['true', 'TRUE', 'True', 'tRuE']
        for case in test_cases:
            os.environ['DOCKER_MODE'] = case
            config = Config()
            assert config.DOCKER_MODE is True
            del os.environ['DOCKER_MODE']
        
        false_cases = ['false', 'FALSE', 'False', 'fAlSe', '0', 'no', '']
        for case in false_cases:
            os.environ['DOCKER_MODE'] = case
            config = Config()
            assert config.DOCKER_MODE is False
            del os.environ['DOCKER_MODE']
    
    def test_database_path_configuration(self):
        """Test database path configuration for Docker"""
        # Test default fallback path
        config = Config()
        assert config.DATABASE_PATH == "data/app.db"
        
        # Test custom database path
        os.environ['DATABASE_PATH'] = '/app/data/custom.db'
        config = Config()
        assert config.DATABASE_PATH == '/app/data/custom.db'


class TestDockerServiceConfiguration:
    """Test Docker service configuration settings"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Clear relevant environment variables
        self.env_vars_to_clear = [
            'HOST', 'PORT', 'API_BASE_URL',
            'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
            'REDIS_HOST', 'REDIS_PORT', 'REDIS_PASSWORD',
            'MONGO_HOST', 'MONGO_PORT', 'MONGO_DB', 'MONGO_USER', 'MONGO_PASSWORD',
            'OLLAMA_BASE_URL'
        ]
        
        self.original_env = {}
        for var in self.env_vars_to_clear:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def teardown_method(self):
        """Clean up after tests"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    def test_server_configuration_defaults(self):
        """Test server configuration defaults for Docker"""
        config = Config()
        assert config.HOST == "0.0.0.0"  # Docker-friendly default
        assert config.PORT == 8000
        assert config.API_BASE_URL == "http://api:8000"  # Docker service communication
    
    def test_server_configuration_custom(self):
        """Test custom server configuration"""
        os.environ['HOST'] = '127.0.0.1'
        os.environ['PORT'] = '9000'
        os.environ['API_BASE_URL'] = 'http://custom-api:9000'
        
        config = Config()
        assert config.HOST == "127.0.0.1"
        assert config.PORT == 9000
        assert config.API_BASE_URL == "http://custom-api:9000"
    
    def test_postgresql_configuration_defaults(self):
        """Test PostgreSQL configuration defaults for Docker"""
        config = Config()
        assert config.DATABASE_TYPE == "postgresql"
        assert config.POSTGRES_HOST == "db"  # Docker service name
        assert config.POSTGRES_PORT == 5432
        assert config.POSTGRES_DB == "app_db"
        assert config.POSTGRES_USER == "admin"
        assert config.POSTGRES_PASSWORD == "password"
    
    def test_postgresql_configuration_custom(self):
        """Test custom PostgreSQL configuration"""
        os.environ['POSTGRES_HOST'] = 'custom-db'
        os.environ['POSTGRES_PORT'] = '5433'
        os.environ['POSTGRES_DB'] = 'visa_data'
        os.environ['POSTGRES_USER'] = 'visa_user'
        os.environ['POSTGRES_PASSWORD'] = 'secure_password'
        
        config = Config()
        assert config.POSTGRES_HOST == "custom-db"
        assert config.POSTGRES_PORT == 5433
        assert config.POSTGRES_DB == "visa_data"
        assert config.POSTGRES_USER == "visa_user"
        assert config.POSTGRES_PASSWORD == "secure_password"
    
    def test_redis_configuration_defaults(self):
        """Test Redis configuration defaults for Docker"""
        config = Config()
        assert config.REDIS_HOST == "redis"  # Docker service name
        assert config.REDIS_PORT == 6379
        assert config.REDIS_PASSWORD == "redis_password"
    
    def test_redis_configuration_custom(self):
        """Test custom Redis configuration"""
        os.environ['REDIS_HOST'] = 'custom-redis'
        os.environ['REDIS_PORT'] = '6380'
        os.environ['REDIS_PASSWORD'] = 'custom_redis_pass'
        
        config = Config()
        assert config.REDIS_HOST == "custom-redis"
        assert config.REDIS_PORT == 6380
        assert config.REDIS_PASSWORD == "custom_redis_pass"
    
    def test_mongodb_configuration_defaults(self):
        """Test MongoDB configuration defaults for Docker"""
        config = Config()
        assert config.MONGO_HOST == "mongodb"  # Docker service name
        assert config.MONGO_PORT == 27017
        assert config.MONGO_DB == "app_db"
        assert config.MONGO_USER == "admin"
        assert config.MONGO_PASSWORD == "password"
    
    def test_mongodb_configuration_custom(self):
        """Test custom MongoDB configuration"""
        os.environ['MONGO_HOST'] = 'custom-mongo'
        os.environ['MONGO_PORT'] = '27018'
        os.environ['MONGO_DB'] = 'visa_analytics'
        os.environ['MONGO_USER'] = 'mongo_user'
        os.environ['MONGO_PASSWORD'] = 'mongo_secure_pass'
        
        config = Config()
        assert config.MONGO_HOST == "custom-mongo"
        assert config.MONGO_PORT == 27018
        assert config.MONGO_DB == "visa_analytics"
        assert config.MONGO_USER == "mongo_user"
        assert config.MONGO_PASSWORD == "mongo_secure_pass"
    
    def test_ollama_configuration_docker_default(self):
        """Test Ollama configuration default for Docker"""
        config = Config()
        assert config.OLLAMA_BASE_URL == "http://host.docker.internal:11434"  # Docker host access
    
    def test_ollama_configuration_custom(self):
        """Test custom Ollama configuration"""
        os.environ['OLLAMA_BASE_URL'] = 'http://ollama-service:11434'
        
        config = Config()
        assert config.OLLAMA_BASE_URL == "http://ollama-service:11434"


class TestConfigValidation:
    """Test configuration validation with Docker settings"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Clear API key environment variables
        self.api_key_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'LLM_PROVIDER']
        self.original_env = {}
        
        for var in self.api_key_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def teardown_method(self):
        """Clean up after tests"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    def test_validate_config_openai_success(self):
        """Test successful OpenAI configuration validation"""
        os.environ['OPENAI_API_KEY'] = 'test-api-key'
        config = Config()
        assert config.validate_config('openai') is True
    
    def test_validate_config_openai_missing_key(self):
        """Test OpenAI configuration validation with missing API key"""
        config = Config()
        with pytest.raises(ValueError, match="OPENAI_API_KEY is required but not set"):
            config.validate_config('openai')
    
    def test_validate_config_anthropic_success(self):
        """Test successful Anthropic configuration validation"""
        os.environ['ANTHROPIC_API_KEY'] = 'test-api-key'
        config = Config()
        assert config.validate_config('anthropic') is True
    
    def test_validate_config_anthropic_missing_key(self):
        """Test Anthropic configuration validation with missing API key"""
        config = Config()
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required but not set"):
            config.validate_config('anthropic')
    
    def test_validate_config_google_success(self):
        """Test successful Google configuration validation"""
        os.environ['GOOGLE_API_KEY'] = 'test-api-key'
        config = Config()
        assert config.validate_config('google') is True
    
    def test_validate_config_google_missing_key(self):
        """Test Google configuration validation with missing API key"""
        config = Config()
        with pytest.raises(ValueError, match="GOOGLE_API_KEY is required but not set"):
            config.validate_config('google')
    
    def test_validate_config_ollama_no_key_required(self):
        """Test Ollama configuration validation (no API key required)"""
        config = Config()
        # Ollama should not require an API key
        assert config.validate_config('ollama') is True


class TestGetConfigFunction:
    """Test the get_config factory function with Docker integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Set up environment for valid config
        os.environ['GOOGLE_API_KEY'] = 'test-google-key'
        os.environ['LLM_PROVIDER'] = 'google'
    
    def teardown_method(self):
        """Clean up after tests"""
        # Clean up environment variables
        env_vars_to_clean = ['GOOGLE_API_KEY', 'LLM_PROVIDER', 'DOCKER_MODE']
        for var in env_vars_to_clean:
            if var in os.environ:
                del os.environ[var]
    
    @patch('utils.config.load_dotenv')
    def test_get_config_loads_dotenv(self, mock_load_dotenv):
        """Test that get_config loads environment variables"""
        config = get_config()
        
        # Verify dotenv was called with override
        mock_load_dotenv.assert_called_once_with(override=True)
        
        # Verify config was created and validated
        assert isinstance(config, Config)
        assert config.LLM_PROVIDER == 'google'
    
    @patch('utils.config.load_dotenv')
    def test_get_config_force_reload_false(self, mock_load_dotenv):
        """Test get_config with force_reload=False"""
        config = get_config(force_reload=False)
        
        # Verify dotenv was called without override
        mock_load_dotenv.assert_called_once_with(override=False)
        
        assert isinstance(config, Config)
    
    def test_get_config_with_docker_mode(self):
        """Test get_config with Docker mode enabled"""
        os.environ['DOCKER_MODE'] = 'true'
        
        config = get_config()
        
        assert config.DOCKER_MODE is True
        assert config.HOST == "0.0.0.0"  # Docker-friendly host
        assert config.DATABASE_TYPE == "postgresql"  # Docker uses PostgreSQL
    
    @patch('utils.config.load_dotenv')
    def test_get_config_validation_failure(self, mock_load_dotenv):
        """Test get_config with validation failure"""
        # Remove API key but keep provider set to google to cause validation failure
        del os.environ['GOOGLE_API_KEY']
        # Ensure LLM_PROVIDER is set to google
        os.environ['LLM_PROVIDER'] = 'google'
        
        with pytest.raises(ValueError, match="GOOGLE_API_KEY is required but not set"):
            get_config()


class TestConfigSupportedProviders:
    """Test configuration provider support"""
    
    def test_get_supported_providers(self):
        """Test getting list of supported providers"""
        providers = Config.get_supported_providers()
        
        expected_providers = ["openai", "anthropic", "google", "ollama"]
        assert providers == expected_providers
        assert len(providers) == 4
    
    def test_get_model_for_provider_openai(self):
        """Test getting model for OpenAI provider"""
        config = Config()
        model = config.get_model_for_provider('openai')
        assert model == config.OPENAI_MODEL
    
    def test_get_model_for_provider_anthropic(self):
        """Test getting model for Anthropic provider"""
        config = Config()
        model = config.get_model_for_provider('anthropic')
        assert model == config.ANTHROPIC_MODEL
    
    def test_get_model_for_provider_google(self):
        """Test getting model for Google provider"""
        config = Config()
        model = config.get_model_for_provider('google')
        assert model == config.GOOGLE_MODEL
    
    def test_get_model_for_provider_ollama(self):
        """Test getting model for Ollama provider"""
        config = Config()
        model = config.get_model_for_provider('ollama')
        assert model == config.OLLAMA_MODEL
    
    def test_get_model_for_provider_unknown(self):
        """Test getting model for unknown provider"""
        config = Config()
        with pytest.raises(ValueError, match="Unknown provider: unknown"):
            config.get_model_for_provider('unknown')


class TestDockerEnvironmentIntegration:
    """Test integration with actual Docker environment patterns"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Clear environment variables
        self.env_vars_to_clear = [
            'DOCKER_MODE', 'DATABASE_PATH', 'POSTGRES_HOST', 'REDIS_HOST', 'MONGO_HOST'
        ]
        
        self.original_env = {}
        for var in self.env_vars_to_clear:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def teardown_method(self):
        """Clean up after tests"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
    
    def test_docker_compose_service_names(self):
        """Test Docker Compose service name defaults"""
        config = Config()
        
        # Verify Docker Compose service names are used as defaults
        assert config.POSTGRES_HOST == "db"
        assert config.REDIS_HOST == "redis"
        assert config.MONGO_HOST == "mongodb"
    
    def test_docker_container_communication(self):
        """Test Docker container communication settings"""
        config = Config()
        
        # Verify container-friendly settings
        assert config.HOST == "0.0.0.0"  # Bind to all interfaces
        assert config.API_BASE_URL == "http://api:8000"  # Service-to-service communication
        assert config.OLLAMA_BASE_URL == "http://host.docker.internal:11434"  # Host access from container
    
    def test_docker_environment_override(self):
        """Test overriding Docker environment settings"""
        # Simulate Docker environment with custom service names
        os.environ['POSTGRES_HOST'] = 'visa-postgres'
        os.environ['REDIS_HOST'] = 'visa-redis'
        os.environ['MONGO_HOST'] = 'visa-mongodb'
        os.environ['DOCKER_MODE'] = 'true'
        
        config = Config()
        
        assert config.POSTGRES_HOST == "visa-postgres"
        assert config.REDIS_HOST == "visa-redis"
        assert config.MONGO_HOST == "visa-mongodb"
        assert config.DOCKER_MODE is True
    
    def test_local_development_fallback(self):
        """Test fallback behavior for local development"""
        config = Config()
        
        # Database path should fallback to local file for development
        assert config.DATABASE_PATH == "data/app.db"
        
        # Docker mode should be disabled by default
        assert config.DOCKER_MODE is False