"""
API client for communicating with the FastAPI backend
"""
import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from utils.config import get_config

class APIClient:
    """Client for interacting with the FastAPI backend"""
    
    def __init__(self):
        """Initialize API client with configuration"""
        self.config = get_config()
        self.base_url = self.config.API_BASE_URL
        self.timeout = 30
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request to API with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            st.error(f"🚫 Cannot connect to API server at {self.base_url}")
            st.info("💡 Make sure the API server is running: `python scripts/start_api.py`")
            return {"error": "Connection failed"}
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. The API server might be overloaded.")
            return {"error": "Request timeout"}
        except requests.exceptions.HTTPError as e:
            st.error(f"🔴 API Error: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict:
        """Check API health status"""
        return self._make_request("GET", "/health")
    
    def chat_with_agent(self, message: str, session_id: str, config: Dict = None) -> Dict:
        """Send chat message to agent"""
        data = {
            "message": message,
            "session_id": session_id
        }
        if config:
            data["config"] = config
            
        return self._make_request("POST", "/api/agent/chat", data=data)
    
    def get_conversation_history(self, session_id: str) -> Dict:
        """Get conversation history for session"""
        return self._make_request("GET", f"/api/agent/conversation/{session_id}")
    
    def update_agent_config(self, session_id: str, config: Dict) -> Dict:
        """Update agent configuration for session"""
        data = {
            "session_id": session_id,
            "config": config
        }
        return self._make_request("POST", "/api/agent/configure", data=data)
    
    def get_supported_providers(self) -> Dict:
        """Get list of supported LLM providers"""
        return self._make_request("GET", "/api/agent/providers")
    
    def get_visa_categories(self) -> Dict:
        """Get supported visa categories"""
        return self._make_request("GET", "/api/analytics/categories")
    
    def get_visa_countries(self) -> Dict:
        """Get supported countries"""
        return self._make_request("GET", "/api/analytics/countries")
    
    def analyze_visa_trends(self, category: str, country: str, years_back: int = 2) -> Dict:
        """Analyze visa bulletin trends"""
        data = {
            "category": category,
            "country": country,
            "years_back": years_back
        }
        return self._make_request("POST", "/api/analytics/trends", data=data)
    
    def predict_visa_movement(self, category: str, country: str, months_ahead: int = 3) -> Dict:
        """Predict visa bulletin movement"""
        data = {
            "category": category,
            "country": country,
            "months_ahead": months_ahead
        }
        return self._make_request("POST", "/api/analytics/predictions", data=data)
    
    def get_historical_data(self, category: str, country: str, start_year: int = None, end_year: int = None) -> Dict:
        """Get historical visa bulletin data"""
        params = {
            "category": category,
            "country": country
        }
        if start_year:
            params["start_year"] = start_year
        if end_year:
            params["end_year"] = end_year
            
        return self._make_request("GET", "/api/analytics/historical", params=params)
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        return self._make_request("GET", "/api/analytics/stats")

# Global instance
@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance"""
    return APIClient()