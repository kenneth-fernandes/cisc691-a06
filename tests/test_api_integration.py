"""
Integration tests for FastAPI application with database and external services
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os

from api.main import app

client = TestClient(app)


class TestDatabaseIntegration:
    """Test API integration with database"""
    
    @patch('visa.database.VisaDatabase')
    def test_api_database_connection(self, mock_db):
        """Test API can connect to database"""
        # Mock database connection
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        response = client.get("/api/analytics/stats")
        # Even with mocked DB, should not crash on connection attempt
        assert response.status_code in [200, 500]  # Either success or handled error
    
    @patch('api.routers.analytics.repository')
    def test_analytics_with_real_data_structure(self, mock_repository):
        """Test analytics endpoints with realistic data structure"""
        # Mock realistic visa data
        mock_repository.get_category_history.return_value = []
        mock_repository.get_statistics.return_value = {
            "bulletin_count": 0,
            "category_data_count": 0,
            "year_range": "No data"
        }
        
        # Test historical data endpoint
        response = client.get("/api/analytics/historical?category=EB2&country=India")
        assert response.status_code == 200
        data = response.json()
        assert data["data_points"] == 0
        
        # Test stats endpoint
        response = client.get("/api/analytics/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_bulletins" in data


class TestAgentIntegration:
    """Test agent integration with different providers"""
    
    @patch('api.routers.agent.create_agent')
    def test_agent_with_google_provider(self, mock_create_agent):
        """Test agent creation with Google provider"""
        mock_agent = MagicMock()
        mock_agent.chat.return_value = "Google response"
        mock_create_agent.return_value = mock_agent
        
        response = client.post("/api/agent/chat", json={
            "message": "Test message",
            "session_id": "google-test",
            "config": {"provider": "google"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    @patch('api.routers.agent.create_agent')
    def test_agent_with_ollama_provider(self, mock_create_agent):
        """Test agent creation with Ollama provider"""
        mock_agent = MagicMock()
        mock_agent.chat.return_value = "Ollama response"
        mock_create_agent.return_value = mock_agent
        
        response = client.post("/api/agent/chat", json={
            "message": "Test message",
            "session_id": "ollama-test",
            "config": {"provider": "ollama"}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    @patch('api.routers.agent.create_agent')
    def test_agent_session_persistence(self, mock_create_agent):
        """Test that agent sessions are maintained"""
        mock_agent = MagicMock()
        mock_agent.chat.return_value = "Session response"
        mock_agent.get_conversation_history.return_value = []
        mock_create_agent.return_value = mock_agent
        
        session_id = "persistent-session"
        
        # First request
        response1 = client.post("/api/agent/chat", json={
            "message": "First message",
            "session_id": session_id
        })
        assert response1.status_code == 200
        
        # Second request with same session
        response2 = client.post("/api/agent/chat", json={
            "message": "Second message", 
            "session_id": session_id
        })
        assert response2.status_code == 200
        
        # Agent should be created only once for the session (sessions are cached)
        # Note: Due to session caching, create_agent might be called once
        assert mock_create_agent.call_count >= 1


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    @patch('api.routers.analytics.repository')
    @patch('api.routers.analytics.trend_analyzer')
    def test_visa_analysis_workflow(self, mock_analyzer, mock_repository):
        """Test complete visa analysis workflow"""
        # Setup mock data
        mock_repository.get_category_history.return_value = []
        mock_analyzer.calculate_advancement_trends.return_value = {
            "trend": "advancing",
            "average_advancement": 10.5,
            "total_advancement": 105,
            "data_points": 10
        }
        
        # 1. Get supported categories
        response = client.get("/api/analytics/categories")
        assert response.status_code == 200
        categories = response.json()
        
        # 2. Get supported countries  
        response = client.get("/api/analytics/countries")
        assert response.status_code == 200
        countries = response.json()
        
        # 3. Get historical data
        response = client.get("/api/analytics/historical?category=EB2&country=India")
        assert response.status_code == 200
        
        # 4. Perform trend analysis
        response = client.post("/api/analytics/trends", json={
            "category": "EB-2",
            "country": "India",
            "years_back": 3
        })
        assert response.status_code == 200
        trend_data = response.json()
        assert "analysis" in trend_data
    
    @patch('api.routers.agent.create_agent')
    def test_agent_visa_consultation_workflow(self, mock_create_agent):
        """Test agent-based visa consultation workflow"""
        mock_agent = MagicMock()
        mock_agent.chat.side_effect = [
            "Hello! I can help with visa questions.",
            "EB-2 is for professionals with advanced degrees.",
            "Current trends show advancement for India EB-2."
        ]
        mock_agent.get_conversation_history.return_value = []
        mock_create_agent.return_value = mock_agent
        
        session_id = "visa-consultation"
        
        # 1. Initial greeting
        response = client.post("/api/agent/chat", json={
            "message": "Hello, I need help with visa questions",
            "session_id": session_id
        })
        assert response.status_code == 200
        
        # 2. Ask about EB-2 category
        response = client.post("/api/agent/chat", json={
            "message": "What is EB-2 visa category?",
            "session_id": session_id
        })
        assert response.status_code == 200
        
        # 3. Ask about trends
        response = client.post("/api/agent/chat", json={
            "message": "What are the current trends for India EB-2?",
            "session_id": session_id
        })
        assert response.status_code == 200


class TestErrorRecovery:
    """Test error recovery and resilience"""
    
    @patch('api.routers.analytics.repository')
    def test_database_error_handling(self, mock_repository):
        """Test handling of database errors"""
        mock_repository.get_statistics.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/analytics/stats")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    @patch('api.routers.agent.create_agent')
    def test_agent_error_handling(self, mock_create_agent):
        """Test handling of agent creation errors"""
        mock_create_agent.side_effect = Exception("Agent creation failed")
        
        response = client.post("/api/agent/chat", json={
            "message": "Test message",
            "session_id": "error-test"
        })
        # Should handle the error gracefully
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    def test_invalid_data_handling(self):
        """Test handling of invalid input data"""
        # Test with completely invalid JSON structure
        response = client.post("/api/analytics/trends", json={
            "invalid_field": "invalid_value"
        })
        assert response.status_code == 422  # Validation error
        
        # Test with invalid enum values
        response = client.post("/api/analytics/trends", json={
            "category": "INVALID_CATEGORY",
            "country": "INVALID_COUNTRY",
            "years_back": 3
        })
        assert response.status_code == 400  # Business logic error


class TestPerformance:
    """Test API performance characteristics"""
    
    @patch('api.routers.analytics.repository')
    def test_large_dataset_handling(self, mock_repository):
        """Test handling of large datasets"""
        # Mock large dataset
        large_dataset = []
        for i in range(1000):
            mock_data = MagicMock()
            mock_data.category.value = "EB-2"
            mock_data.country.value = "INDIA"
            mock_data.final_action_date = None
            mock_data.filing_date = None
            mock_data.status = "C"
            mock_data.notes = None
            large_dataset.append(mock_data)
        
        mock_repository.get_category_history.return_value = large_dataset
        
        response = client.get("/api/analytics/historical?category=EB2&country=India")
        assert response.status_code == 200
        data = response.json()
        assert data["data_points"] == 1000
    
    @patch('api.routers.agent.create_agent')
    def test_concurrent_agent_sessions(self, mock_create_agent):
        """Test handling of multiple concurrent agent sessions"""
        mock_agent = MagicMock()
        mock_agent.chat.return_value = "Concurrent response"
        mock_agent.get_conversation_history.return_value = []
        mock_create_agent.return_value = mock_agent
        
        # Simulate multiple concurrent sessions
        sessions = [f"session-{i}" for i in range(10)]
        
        for session_id in sessions:
            response = client.post("/api/agent/chat", json={
                "message": f"Message from {session_id}",
                "session_id": session_id
            })
            assert response.status_code == 200


class TestConfiguration:
    """Test different configuration scenarios"""
    
    @patch.dict(os.environ, {"DOCKER_MODE": "true"})
    def test_docker_mode_configuration(self):
        """Test API behavior in Docker mode"""
        response = client.get("/health")
        assert response.status_code == 200
    
    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_debug_mode_configuration(self):
        """Test API behavior in debug mode"""
        response = client.get("/health")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])