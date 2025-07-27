"""
Integration tests for WebSocket functionality with corrected endpoints
"""
import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from api.main import app

client = TestClient(app)


class TestWebSocketEndpointCorrections:
    """Test WebSocket endpoints with corrected paths"""
    
    def test_websocket_stats_endpoint_corrected_path(self):
        """Test WebSocket stats endpoint with correct path"""
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_manager.get_connection_count.return_value = 1
            mock_manager.connection_info = {}
            mock_manager.typing_status = {}
            
            # Test the corrected path (without double /websocket)
            response = client.get("/api/websocket/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert "active_connections" in data
            assert "connection_info" in data
            assert "typing_status" in data
    
    def test_broadcast_endpoint_corrected_path(self):
        """Test broadcast endpoint with correct path"""
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()
            mock_manager.get_connection_count.return_value = 2
            
            message_data = {
                "message": "Test broadcast message",
                "level": "info"
            }
            
            # Test the corrected path
            response = client.post("/api/websocket/broadcast", json=message_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "recipients" in data
    
    def test_disconnect_endpoint_corrected_path(self):
        """Test disconnect endpoint with correct path"""
        session_id = "test_session_456"
        
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_websocket = AsyncMock()
            mock_manager.is_connected.return_value = True
            mock_manager.active_connections = {session_id: mock_websocket}
            mock_manager.disconnect = MagicMock()
            
            # Test the corrected path
            response = client.delete(f"/api/websocket/disconnect/{session_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
    
    def test_old_double_websocket_paths_return_404(self):
        """Test that old double /websocket paths return 404"""
        # These should all return 404 now
        old_paths = [
            "/api/websocket/websocket/stats",
            "/api/websocket/websocket/broadcast", 
            "/api/websocket/websocket/disconnect/test"
        ]
        
        for path in old_paths:
            if "broadcast" in path:
                response = client.post(path, json={"message": "test"})
            elif "disconnect" in path:
                response = client.delete(path)
            else:
                response = client.get(path)
            
            assert response.status_code == 404, f"Path {path} should return 404"


class TestWebSocketChatEndpoint:
    """Test the main WebSocket chat endpoint"""
    
    def test_websocket_chat_endpoint_path(self):
        """Test WebSocket chat endpoint is correctly configured"""
        # This tests that the WebSocket endpoint is properly registered
        # We can't easily test WebSocket connections in TestClient, but we can verify
        # the endpoint exists by checking the OpenAPI spec
        
        # Check if WebSocket endpoint paths exist in the app
        # WebSocket endpoints don't appear in OpenAPI spec, but we can check the router
        from api.routers import websocket
        
        # Verify the router has the websocket decorator
        assert hasattr(websocket, 'router')
        assert websocket.router is not None
    
    def test_websocket_auth_dependency(self):
        """Test WebSocket authentication dependency"""
        from api.routers.websocket import verify_websocket_auth
        import pytest
        from fastapi import HTTPException
        
        # Test with missing session_id
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.close = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_websocket_auth(mock_websocket, None))
        
        assert exc_info.value.status_code == 401
    
    def test_websocket_message_types_validation(self):
        """Test WebSocket message type validation"""
        from api.models.websocket import MessageType, WebSocketMessage
        from datetime import datetime
        
        # Test valid message types
        valid_types = ["chat", "system", "error", "typing", "heartbeat", "agent_response"]
        
        for msg_type in valid_types:
            message = WebSocketMessage(
                type=msg_type,
                timestamp=datetime.now(),
                session_id="test",
                data={"test": "data"}
            )
            assert message.type == msg_type


class TestWebSocketConnectionManager:
    """Test WebSocket connection manager functionality"""
    
    def test_connection_manager_initialization(self):
        """Test connection manager initializes correctly"""
        from api.routers.websocket import ConnectionManager
        
        manager = ConnectionManager()
        assert manager.active_connections == {}
        assert manager.connection_info == {}
        assert manager.typing_status == {}
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect_flow(self):
        """Test connection manager connect flow"""
        from api.routers.websocket import ConnectionManager
        
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock()
        session_id = "test_session_789"
        
        await manager.connect(mock_websocket, session_id, "test-agent", "127.0.0.1")
        
        assert manager.is_connected(session_id)
        assert manager.get_connection_count() == 1
        assert session_id in manager.connection_info
        mock_websocket.accept.assert_called_once()
        mock_websocket.send_text.assert_called_once()  # Welcome message


class TestWebSocketModelValidation:
    """Test WebSocket model validation and serialization"""
    
    def test_chat_message_model(self):
        """Test ChatMessage model validation"""
        from api.models.websocket import ChatMessage
        from datetime import datetime
        
        chat_msg = ChatMessage(
            message="Test message",
            session_id="test_123",
            config={"provider": "google"},
            timestamp=datetime.now()
        )
        
        assert chat_msg.message == "Test message"
        assert chat_msg.session_id == "test_123"
        assert chat_msg.config["provider"] == "google"
    
    def test_system_message_model(self):
        """Test SystemMessage model validation"""
        from api.models.websocket import SystemMessage
        
        sys_msg = SystemMessage(
            message="System notification",
            level="warning"
        )
        
        assert sys_msg.message == "System notification"
        assert sys_msg.level == "warning"
    
    def test_connection_info_model(self):
        """Test ConnectionInfo model validation"""
        from api.models.websocket import ConnectionInfo
        from datetime import datetime
        
        conn_info = ConnectionInfo(
            session_id="test_456",
            connected_at=datetime.now(),
            user_agent="Mozilla/5.0",
            ip_address="127.0.0.1"
        )
        
        assert conn_info.session_id == "test_456"
        assert conn_info.user_agent == "Mozilla/5.0"
        assert conn_info.ip_address == "127.0.0.1"


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect_cleanup(self):
        """Test WebSocket disconnect cleanup"""
        from api.routers.websocket import ConnectionManager
        
        manager = ConnectionManager()
        session_id = "cleanup_test_session"
        
        # Simulate connection
        mock_websocket = AsyncMock()
        manager.active_connections[session_id] = mock_websocket
        manager.connection_info[session_id] = MagicMock()
        manager.typing_status[session_id] = False
        
        # Test disconnect cleanup
        manager.disconnect(session_id)
        
        assert not manager.is_connected(session_id)
        assert session_id not in manager.connection_info
        assert session_id not in manager.typing_status
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio 
    async def test_websocket_send_error_handling(self):
        """Test WebSocket send error handling"""
        from api.routers.websocket import ConnectionManager
        
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        
        # Should not raise exception
        await manager.send_personal_message({"test": "message"}, mock_websocket)
        
        # Verify send_text was called despite the exception
        mock_websocket.send_text.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])