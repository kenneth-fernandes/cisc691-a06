"""
Tests for Streamlit API client and frontend integration
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
import json

from ui.utils.api_client import APIClient


class TestAPIClient:
    """Test the APIClient used by Streamlit frontend"""
    
    @patch('ui.utils.api_client.get_config')
    def test_api_client_initialization(self, mock_config):
        """Test API client initialization"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        client = APIClient()
        assert client.base_url == "http://test:8000"
        assert client.timeout == 30
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.get')
    def test_make_request_success(self, mock_get, mock_config):
        """Test successful API request"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response
        
        client = APIClient()
        result = client._make_request("GET", "/test")
        
        assert result == {"status": "success"}
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.get')
    def test_make_request_timeout(self, mock_get, mock_config):
        """Test API request timeout handling"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_get.side_effect = requests.exceptions.Timeout()
        
        client = APIClient()
        result = client._make_request("GET", "/test")
        
        assert "error" in result
        assert "timeout" in result["error"].lower()
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.get')
    def test_make_request_connection_error(self, mock_get, mock_config):
        """Test API request connection error handling"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        client = APIClient()
        result = client._make_request("GET", "/test")
        
        assert "error" in result
        assert "Connection failed" in result["error"]


class TestAgentClientMethods:
    """Test agent-specific API client methods"""
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.post')
    def test_chat_with_agent_basic(self, mock_post, mock_config):
        """Test basic chat with agent"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Hello! How can I help?",
            "session_id": "test-session",
            "conversation_history": []
        }
        mock_post.return_value = mock_response
        
        client = APIClient()
        result = client.chat_with_agent("Hello", "test-session")
        
        assert result["response"] == "Hello! How can I help?"
        assert result["session_id"] == "test-session"
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.post')
    def test_chat_with_agent_config(self, mock_post, mock_config):
        """Test chat with agent including config"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Response with config",
            "session_id": "test-session",
            "conversation_history": []
        }
        mock_post.return_value = mock_response
        
        client = APIClient()
        config = {"provider": "google", "temperature": 0.7}
        result = client.chat_with_agent("Test message", "test-session", config)
        
        assert "response" in result
        mock_post.assert_called_once()


class TestAnalyticsClientMethods:
    """Test analytics-specific API client methods"""
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.get')
    def test_get_categories(self, mock_get, mock_config):
        """Test getting visa categories"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "employment_based": ["EB-1", "EB-2", "EB-3"],
            "family_based": ["F1", "F2A", "F2B"]
        }
        mock_get.return_value = mock_response
        
        client = APIClient()
        result = client.get_visa_categories()
        
        assert "employment_based" in result
        assert "family_based" in result
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.get')
    def test_get_countries(self, mock_get, mock_config):
        """Test getting supported countries"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "countries": ["India", "China", "Mexico", "Philippines", "Worldwide"]
        }
        mock_get.return_value = mock_response
        
        client = APIClient()
        result = client.get_visa_countries()
        
        assert "countries" in result
        assert "India" in result["countries"]
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.get')
    def test_get_historical_data(self, mock_get, mock_config):
        """Test getting historical visa data"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "category": "EB-2",
            "country": "India",
            "data_points": 10,
            "historical_data": []
        }
        mock_get.return_value = mock_response
        
        client = APIClient()
        result = client.get_historical_data("EB-2", "India")
        
        assert result["category"] == "EB-2"
        assert result["country"] == "India"
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.post')
    def test_analyze_trends(self, mock_post, mock_config):
        """Test trend analysis"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "category": "EB-2",
            "country": "India",
            "analysis": {
                "trend": "advancing",
                "average_advancement": 15.2
            }
        }
        mock_post.return_value = mock_response
        
        client = APIClient()
        result = client.analyze_visa_trends("EB-2", "India", 3)
        
        assert result["category"] == "EB-2"
        assert "analysis" in result


class TestStreamlitIntegration:
    """Test integration scenarios specific to Streamlit usage"""
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.post')
    def test_streamlit_session_management(self, mock_post, mock_config):
        """Test API client session management for Streamlit"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Session response",
            "session_id": "streamlit-session",
            "conversation_history": []
        }
        mock_post.return_value = mock_response
        
        client = APIClient()
        session_id = "streamlit-session"
        
        # Multiple requests with same session
        result1 = client.chat_with_agent("First message", session_id)
        result2 = client.chat_with_agent("Second message", session_id)
        
        assert result1["session_id"] == session_id
        assert result2["session_id"] == session_id
        assert mock_post.call_count == 2
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.post')
    def test_streamlit_error_display(self, mock_post, mock_config):
        """Test error handling for Streamlit display"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service temporarily unavailable"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response
        
        client = APIClient()
        result = client.chat_with_agent("Hello", "error-session")
        
        # Should return error in format suitable for Streamlit display
        assert "error" in result


class TestAPIClientConfiguration:
    """Test API client configuration scenarios"""
    
    @patch('ui.utils.api_client.get_config')
    def test_different_base_urls(self, mock_config):
        """Test API client with different base URL configurations"""
        # Test with different configurations
        test_urls = [
            "http://localhost:8000",  # Local development
            "http://api:8000",        # Docker internal
            "https://api.example.com" # Production
        ]
        
        for url in test_urls:
            mock_config_obj = MagicMock()
            mock_config_obj.API_BASE_URL = url
            mock_config.return_value = mock_config_obj
            
            client = APIClient()
            assert client.base_url == url


class TestHealthCheck:
    """Test health check functionality"""
    
    @patch('ui.utils.api_client.get_config')
    @patch('requests.get')
    def test_health_check(self, mock_get, mock_config):
        """Test API health check"""
        mock_config_obj = MagicMock()
        mock_config_obj.API_BASE_URL = "http://test:8000"
        mock_config.return_value = mock_config_obj
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response
        
        client = APIClient()
        result = client.health_check()
        
        assert result["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])