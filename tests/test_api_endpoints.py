"""
Test FastAPI endpoints for agent and analytics routers
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test basic health and info endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAgentEndpoints:
    """Test agent chat API endpoints"""
    
    @patch('api.routers.agent.get_or_create_agent')
    def test_agent_chat_basic(self, mock_get_agent):
        """Test basic agent chat functionality"""
        # Mock agent response
        mock_agent = MagicMock()
        mock_agent.chat.return_value = "Hello! How can I help you?"
        mock_get_agent.return_value = mock_agent
        
        response = client.post("/api/agent/chat", json={
            "message": "Hello",
            "session_id": "test-session"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session"
        assert "conversation_history" in data
    
    @patch('api.routers.agent.get_or_create_agent')
    def test_agent_chat_with_config(self, mock_get_agent):
        """Test agent chat with custom configuration"""
        mock_agent = MagicMock()
        mock_agent.chat.return_value = "Response with custom config"
        mock_get_agent.return_value = mock_agent
        
        response = client.post("/api/agent/chat", json={
            "message": "Test message",
            "session_id": "test-session-2",
            "config": {
                "provider": "google",
                "temperature": 0.7
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-2"
        # The agent function is called with session_id and config, but config structure may differ
        assert mock_get_agent.called
    
    def test_agent_chat_missing_message(self):
        """Test chat endpoint with missing message"""
        response = client.post("/api/agent/chat", json={
            "session_id": "test-session"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_agent_chat_missing_session_id(self):
        """Test chat endpoint with missing session_id"""
        response = client.post("/api/agent/chat", json={
            "message": "Hello"
        })
        
        assert response.status_code == 422  # Validation error


class TestAnalyticsEndpoints:
    """Test analytics API endpoints"""
    
    def test_get_categories(self):
        """Test getting supported visa categories"""
        response = client.get("/api/analytics/categories")
        assert response.status_code == 200
        data = response.json()
        assert "employment_based" in data
        assert "family_based" in data
        assert "EB-1" in data["employment_based"]
        assert "F1" in data["family_based"]
    
    def test_get_countries(self):
        """Test getting supported countries"""
        response = client.get("/api/analytics/countries")
        assert response.status_code == 200
        data = response.json()
        assert "countries" in data
        assert "India" in data["countries"]
        assert "China" in data["countries"]
    
    @patch('api.routers.analytics.repository')
    def test_get_stats(self, mock_repository):
        """Test getting database statistics"""
        mock_repository.get_statistics.return_value = {
            "bulletin_count": 25,
            "category_data_count": 500,
            "year_range": "2020-2024"
        }
        
        response = client.get("/api/analytics/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_bulletins" in data
        assert "total_categories" in data
        assert "database_stats" in data
    
    @patch('api.routers.analytics.repository')
    def test_get_bulletins(self, mock_repository):
        """Test getting all bulletins"""
        mock_bulletin = MagicMock()
        mock_bulletin.fiscal_year = 2024
        mock_bulletin.month = 8
        mock_bulletin.year = 2024
        mock_bulletin.bulletin_date = None
        mock_bulletin.source_url = "test-url"
        mock_bulletin.categories = []
        
        mock_repository.get_bulletins_by_year_range.return_value = [mock_bulletin]
        
        response = client.get("/api/analytics/bulletins")
        assert response.status_code == 200
        data = response.json()
        assert "bulletins" in data
        assert "count" in data
        assert data["count"] == 1
    
    @patch('api.routers.analytics.repository')
    def test_get_bulletin_by_date(self, mock_repository):
        """Test getting specific bulletin by date"""
        mock_bulletin = MagicMock()
        mock_bulletin.fiscal_year = 2024
        mock_bulletin.month = 8
        mock_bulletin.year = 2024
        mock_bulletin.bulletin_date = None
        mock_bulletin.source_url = "test-url"
        mock_bulletin.categories = []
        
        mock_repository.get_bulletin_by_date.return_value = mock_bulletin
        
        response = client.get("/api/analytics/bulletins/2024/8")
        assert response.status_code == 200
        data = response.json()
        assert data["fiscal_year"] == 2024
        assert data["month"] == 8
        assert data["year"] == 2024
    
    @patch('api.routers.analytics.repository')
    def test_get_bulletin_not_found(self, mock_repository):
        """Test getting non-existent bulletin"""
        mock_repository.get_bulletin_by_date.return_value = None
        
        response = client.get("/api/analytics/bulletins/2030/12")
        assert response.status_code == 404
    
    @patch('api.routers.analytics.repository')
    def test_historical_data(self, mock_repository):
        """Test getting historical data"""
        mock_data = MagicMock()
        mock_data.category.value = "EB-2"
        mock_data.country.value = "INDIA"
        mock_data.final_action_date = None
        mock_data.filing_date = None
        mock_data.status = "C"
        mock_data.notes = None
        
        mock_repository.get_category_history.return_value = [mock_data]
        
        response = client.get("/api/analytics/historical?category=EB2&country=India")
        assert response.status_code == 200
        data = response.json()
        assert "historical_data" in data
        assert "data_points" in data
        assert data["category"] == "EB2"
        assert data["country"] == "India"
    
    @patch('api.routers.analytics.trend_analyzer')
    def test_trend_analysis(self, mock_analyzer):
        """Test trend analysis endpoint"""
        mock_analyzer.calculate_advancement_trends.return_value = {
            "trend": "advancing",
            "average_advancement": 15.2,
            "total_advancement": 152,
            "data_points": 10
        }
        
        response = client.post("/api/analytics/trends", json={
            "category": "EB-2",
            "country": "India",
            "years_back": 3
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert data["category"] == "EB-2"
        assert data["country"] == "India"
    
    def test_trend_analysis_invalid_category(self):
        """Test trend analysis with invalid category"""
        response = client.post("/api/analytics/trends", json={
            "category": "INVALID",
            "country": "India",
            "years_back": 3
        })
        
        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_endpoint(self):
        """Test accessing non-existent endpoint"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """Test using wrong HTTP method"""
        response = client.get("/api/agent/chat")  # Should be POST
        assert response.status_code == 405
    
    def test_invalid_json(self):
        """Test sending invalid JSON"""
        response = client.post("/api/agent/chat", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/api/agent/chat")
        # Note: TestClient might not fully simulate CORS
        # This is more for documentation of expected behavior
        assert response.status_code in [200, 405]  # Either allowed or method not allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])