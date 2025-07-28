"""
Tests for requirements changes and WebSocket dependencies
"""
import pytest


class TestWebSocketDependencies:
    """Test WebSocket related dependencies are available"""
    
    def test_websockets_library_available(self):
        """Test that websockets library is available"""
        try:
            import websockets
            assert websockets.__version__ is not None
        except ImportError:
            pytest.skip("websockets library not available - install with 'pip install websockets'")
    
    def test_uvicorn_standard_available(self):
        """Test that uvicorn with standard dependencies is available"""
        try:
            import uvicorn
            # Check if uvicorn has WebSocket support
            assert hasattr(uvicorn, 'run')
            # Try to import WebSocket related modules that come with uvicorn[standard]
            import websockets  # Should be available with uvicorn[standard]
            assert websockets is not None
        except ImportError:
            pytest.skip("uvicorn[standard] not properly installed - install with 'pip install uvicorn[standard]'")
    
    def test_fastapi_websocket_support(self):
        """Test that FastAPI WebSocket support is available"""
        try:
            from fastapi import WebSocket
            from fastapi.websockets import WebSocketState
            assert WebSocket is not None
            assert WebSocketState is not None
        except ImportError:
            pytest.fail("FastAPI WebSocket support not available")


class TestRedisClientDependencies:
    """Test Redis client dependencies"""
    
    def test_redis_library_available(self):
        """Test that Redis library is available"""
        try:
            import redis
            assert redis.__version__ is not None
        except ImportError:
            pytest.fail("redis library not available - required for caching")
    
    def test_redis_connection_creation(self):
        """Test Redis connection can be created (without connecting)"""
        try:
            import redis
            # Just test that we can create a Redis instance
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            assert r is not None
        except Exception as e:
            pytest.fail(f"Cannot create Redis connection object: {e}")


class TestDatabaseDependencies:
    """Test database client dependencies"""
    
    def test_postgresql_client_available(self):
        """Test PostgreSQL client is available"""
        try:
            import psycopg2
            assert psycopg2.__version__ is not None
        except ImportError:
            pytest.fail("psycopg2-binary not available - required for PostgreSQL")


class TestAPIFrameworkDependencies:
    """Test API framework dependencies"""
    
    def test_fastapi_available(self):
        """Test FastAPI is available with correct version"""
        try:
            import fastapi
            # Check version is >= 0.100.0 as specified in requirements
            version_parts = fastapi.__version__.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            assert major > 0 or (major == 0 and minor >= 100)
        except ImportError:
            pytest.fail("FastAPI not available")
    
    def test_pydantic_v2_available(self):
        """Test Pydantic v2 is available"""
        try:
            import pydantic
            # Check it's Pydantic v2
            version_parts = pydantic.__version__.split('.')
            major = int(version_parts[0])
            assert major >= 2
        except ImportError:
            pytest.fail("Pydantic v2 not available")


class TestStreamlitDependencies:
    """Test Streamlit frontend dependencies"""
    
    def test_streamlit_available(self):
        """Test Streamlit is available"""
        try:
            import streamlit
            assert streamlit.__version__ is not None
        except ImportError:
            pytest.fail("Streamlit not available - required for frontend")


class TestTestingDependencies:
    """Test testing framework dependencies"""
    
    def test_pytest_asyncio_available(self):
        """Test pytest-asyncio is available for async testing"""
        try:
            import pytest_asyncio
            assert pytest_asyncio is not None
        except ImportError:
            pytest.fail("pytest-asyncio not available - required for WebSocket testing")
    
    def test_httpx_available(self):
        """Test httpx is available for HTTP testing"""
        try:
            import httpx
            assert httpx.__version__ is not None
        except ImportError:
            pytest.fail("httpx not available - required for API testing")


class TestOptionalDependencies:
    """Test optional dependencies that enhance functionality"""
    
    def test_langchain_dependencies_available(self):
        """Test LangChain dependencies are available"""
        try:
            import langchain
            import langchain_openai
            import langchain_anthropic
            import langchain_google_genai
            import langchain_ollama
            assert langchain is not None
        except ImportError as e:
            pytest.skip(f"Optional LangChain dependencies not fully available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])