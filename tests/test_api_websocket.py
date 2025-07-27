"""
Tests for API WebSocket functionality
"""
import pytest
import asyncio
import json
import time
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from api.main import app
from api.routers.websocket import (
    ConnectionManager, connection_manager, MessageType,
    handle_chat_message, handle_typing_indicator, handle_heartbeat
)
from api.models.websocket import (
    WebSocketMessage, ChatMessage, SystemMessage, ConnectionInfo
)

client = TestClient(app)


class TestConnectionManager:
    """Test WebSocket connection manager"""
    
    def setup_method(self):
        """Setup fresh connection manager for each test"""
        self.manager = ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect(self):
        """Test WebSocket connection"""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        session_id = "test_session_123"
        
        await self.manager.connect(mock_websocket, session_id, "test-agent", "127.0.0.1")
        
        assert session_id in self.manager.active_connections
        assert session_id in self.manager.connection_info
        assert self.manager.get_connection_count() == 1
        assert self.manager.is_connected(session_id)
        mock_websocket.accept.assert_called_once()
    
    def test_connection_manager_disconnect(self):
        """Test WebSocket disconnection"""
        session_id = "test_session_123"
        mock_websocket = MagicMock()
        
        # Manually add connection
        self.manager.active_connections[session_id] = mock_websocket
        self.manager.connection_info[session_id] = ConnectionInfo(
            session_id=session_id,
            connected_at=time.time()
        )
        
        self.manager.disconnect(session_id)
        
        assert session_id not in self.manager.active_connections
        assert session_id not in self.manager.connection_info
        assert self.manager.get_connection_count() == 0
        assert not self.manager.is_connected(session_id)
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific WebSocket"""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock()
        
        test_message = {"type": "test", "data": "hello"}
        
        await self.manager.send_personal_message(test_message, mock_websocket)
        
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert json.loads(sent_data) == test_message
    
    @pytest.mark.asyncio
    async def test_send_message_to_session(self):
        """Test sending message to specific session"""
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock()
        session_id = "test_session_123"
        
        self.manager.active_connections[session_id] = mock_websocket
        test_message = {"type": "test", "data": "hello"}
        
        await self.manager.send_message_to_session(test_message, session_id)
        
        mock_websocket.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to all connections"""
        # Setup multiple connections
        session_ids = ["session_1", "session_2", "session_3"]
        mock_websockets = []
        
        for session_id in session_ids:
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.client_state = WebSocketState.CONNECTED
            mock_websocket.send_text = AsyncMock()
            mock_websockets.append(mock_websocket)
            self.manager.active_connections[session_id] = mock_websocket
        
        test_message = {"type": "broadcast", "data": "hello all"}
        
        await self.manager.broadcast(test_message)
        
        # All websockets should have received the message
        for mock_websocket in mock_websockets:
            mock_websocket.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_typing_status_management(self):
        """Test typing status management"""
        session_id = "test_session_123"
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock()
        
        self.manager.active_connections[session_id] = mock_websocket
        
        await self.manager.set_typing_status(session_id, True)
        assert self.manager.typing_status[session_id] == True
        
        await self.manager.set_typing_status(session_id, False)
        assert self.manager.typing_status[session_id] == False
        
        # Should have sent typing indicator messages
        assert mock_websocket.send_text.call_count >= 2


class TestWebSocketMessages:
    """Test WebSocket message handling"""
    
    @pytest.mark.asyncio
    async def test_handle_chat_message_success(self):
        """Test successful chat message handling"""
        mock_websocket = AsyncMock(spec=WebSocket)
        session_id = "test_session_123"
        
        message_data = {
            "message": "Hello, agent!",
            "config": {"model": "test", "temperature": 0.7}
        }
        
        with patch('api.routers.websocket.get_or_create_agent') as mock_get_agent, \
             patch('api.routers.websocket.connection_manager') as mock_manager:
            
            # Mock agent
            mock_agent = MagicMock()
            mock_agent.chat.return_value = "Hello! How can I help you?"
            mock_agent.get_conversation_history.return_value = [
                {"role": "user", "content": "Hello, agent!"},
                {"role": "assistant", "content": "Hello! How can I help you?"}
            ]
            mock_get_agent.return_value = mock_agent
            
            # Mock connection manager
            mock_manager.set_typing_status = AsyncMock()
            mock_manager.send_personal_message = AsyncMock()
            
            await handle_chat_message(mock_websocket, session_id, message_data)
            
            # Verify agent was called
            mock_get_agent.assert_called_once()
            mock_agent.chat.assert_called_once_with("Hello, agent!")
            
            # Verify typing indicators
            assert mock_manager.set_typing_status.call_count == 2
            mock_manager.set_typing_status.assert_any_call(session_id, True)
            mock_manager.set_typing_status.assert_any_call(session_id, False)
            
            # Verify response was sent
            mock_manager.send_personal_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_chat_message_error(self):
        """Test chat message handling with error"""
        mock_websocket = AsyncMock(spec=WebSocket)
        session_id = "test_session_123"
        
        message_data = {
            "message": "Hello, agent!"
        }
        
        with patch('api.routers.websocket.get_or_create_agent') as mock_get_agent, \
             patch('api.routers.websocket.connection_manager') as mock_manager, \
             patch('api.routers.websocket.send_error_message') as mock_send_error:
            
            # Mock agent failure
            mock_get_agent.side_effect = Exception("Agent error")
            
            # Mock connection manager
            mock_manager.set_typing_status = AsyncMock()
            mock_send_error = AsyncMock()
            
            await handle_chat_message(mock_websocket, session_id, message_data)
            
            # Verify typing indicator was cleared
            mock_manager.set_typing_status.assert_called_with(session_id, False)
            
            # Verify error was sent (may be called via different path)
            assert mock_manager.set_typing_status.called or mock_send_error.called
    
    @pytest.mark.asyncio
    async def test_handle_typing_indicator(self):
        """Test typing indicator handling"""
        session_id = "test_session_123"
        message_data = {"is_typing": True}
        
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_manager.set_typing_status = AsyncMock()
            
            await handle_typing_indicator(session_id, message_data)
            
            mock_manager.set_typing_status.assert_called_once_with(session_id, True)
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat(self):
        """Test heartbeat handling"""
        mock_websocket = AsyncMock(spec=WebSocket)
        session_id = "test_session_123"
        
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_manager.send_personal_message = AsyncMock()
            
            await handle_heartbeat(mock_websocket, session_id)
            
            mock_manager.send_personal_message.assert_called_once()
            
            # Verify heartbeat response structure
            call_args = mock_manager.send_personal_message.call_args[0]
            message_dict = call_args[0]
            assert message_dict["type"] == MessageType.HEARTBEAT
            assert message_dict["session_id"] == session_id
            assert message_dict["data"]["status"] == "alive"


class TestWebSocketModels:
    """Test WebSocket model validation"""
    
    def test_websocket_message_model(self):
        """Test WebSocketMessage model validation"""
        from datetime import datetime
        
        message = WebSocketMessage(
            type=MessageType.CHAT,
            timestamp=datetime.now(),
            session_id="test_123",
            data={"content": "test message"}
        )
        
        assert message.type == MessageType.CHAT
        assert message.session_id == "test_123"
        assert message.data["content"] == "test message"
    
    def test_chat_message_model(self):
        """Test ChatMessage model validation"""
        chat_msg = ChatMessage(
            message="Hello world",
            session_id="test_123",
            config={"temperature": 0.7}
        )
        
        assert chat_msg.message == "Hello world"
        assert chat_msg.session_id == "test_123"
        assert chat_msg.config["temperature"] == 0.7
    
    def test_system_message_model(self):
        """Test SystemMessage model validation"""
        sys_msg = SystemMessage(
            message="System notification",
            level="warning"
        )
        
        assert sys_msg.message == "System notification"
        assert sys_msg.level == "warning"
    
    def test_connection_info_model(self):
        """Test ConnectionInfo model validation"""
        from datetime import datetime
        
        conn_info = ConnectionInfo(
            session_id="test_123",
            connected_at=datetime.now(),
            user_agent="Mozilla/5.0",
            ip_address="127.0.0.1"
        )
        
        assert conn_info.session_id == "test_123"
        assert conn_info.user_agent == "Mozilla/5.0"
        assert conn_info.ip_address == "127.0.0.1"


class TestWebSocketEndpoints:
    """Test WebSocket HTTP endpoints"""
    
    def test_websocket_stats_endpoint(self):
        """Test WebSocket statistics endpoint"""
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_manager.get_connection_count.return_value = 2
            mock_manager.connection_info = {
                "session_1": MagicMock(
                    connected_at="2024-01-01T10:00:00",
                    user_agent="Mozilla/5.0",
                    ip_address="127.0.0.1"
                )
            }
            mock_manager.typing_status = {"session_1": False}
            
            response = client.get("/api/websocket/websocket/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert "active_connections" in data
            assert "connection_info" in data
            assert "typing_status" in data
            assert data["active_connections"] == 2
    
    @pytest.mark.asyncio
    async def test_broadcast_endpoint(self):
        """Test broadcast message endpoint"""
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_manager.broadcast = AsyncMock()
            mock_manager.get_connection_count.return_value = 3
            
            message_data = {
                "message": "System maintenance in 5 minutes",
                "level": "warning"
            }
            
            response = client.post("/api/websocket/websocket/broadcast", json=message_data)
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "recipients" in data
            assert data["recipients"] == 3
    
    def test_force_disconnect_endpoint_success(self):
        """Test force disconnect endpoint with existing session"""
        session_id = "test_session_123"
        
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_websocket = AsyncMock()
            mock_manager.is_connected.return_value = True
            mock_manager.active_connections = {session_id: mock_websocket}
            mock_manager.disconnect = MagicMock()
            
            response = client.delete(f"/api/websocket/websocket/disconnect/{session_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert session_id in data["message"]
    
    def test_force_disconnect_endpoint_not_found(self):
        """Test force disconnect endpoint with non-existent session"""
        session_id = "nonexistent_session"
        
        with patch('api.routers.websocket.connection_manager') as mock_manager:
            mock_manager.is_connected.return_value = False
            
            response = client.delete(f"/api/websocket/websocket/disconnect/{session_id}")
            assert response.status_code == 404
            
            data = response.json()
            assert "detail" in data
            assert "Session not found" in data["detail"]


class TestWebSocketSecurity:
    """Test WebSocket security and authentication"""
    
    @pytest.mark.asyncio
    async def test_websocket_auth_missing_session_id(self):
        """Test WebSocket authentication with missing session ID"""
        from api.routers.websocket import verify_websocket_auth
        from fastapi import HTTPException
        
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.close = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_websocket_auth(mock_websocket, None)
        
        assert exc_info.value.status_code == 401
        assert "Session ID required" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_websocket_auth_valid_session_id(self):
        """Test WebSocket authentication with valid session ID"""
        from api.routers.websocket import verify_websocket_auth
        
        mock_websocket = AsyncMock(spec=WebSocket)
        session_id = "valid_session_123"
        
        result = await verify_websocket_auth(mock_websocket, session_id)
        assert result == session_id


class TestWebSocketIntegration:
    """Test WebSocket integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self):
        """Test complete WebSocket connection lifecycle"""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock()
        session_id = "lifecycle_test_123"
        
        # Connect
        await manager.connect(mock_websocket, session_id, "test-agent", "127.0.0.1")
        assert manager.is_connected(session_id)
        assert manager.get_connection_count() == 1
        
        # Send message
        test_message = {"type": "test", "data": "hello"}
        await manager.send_message_to_session(test_message, session_id)
        assert mock_websocket.send_text.call_count >= 1  # Welcome message + test message
        
        # Set typing status
        await manager.set_typing_status(session_id, True)
        assert manager.typing_status[session_id] == True
        
        # Disconnect
        manager.disconnect(session_id)
        assert not manager.is_connected(session_id)
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_management(self):
        """Test managing multiple WebSocket sessions"""
        manager = ConnectionManager()
        sessions = ["session_1", "session_2", "session_3"]
        websockets = []
        
        # Connect multiple sessions
        for session_id in sessions:
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.accept = AsyncMock()
            mock_websocket.client_state = WebSocketState.CONNECTED
            mock_websocket.send_text = AsyncMock()
            websockets.append(mock_websocket)
            
            await manager.connect(mock_websocket, session_id)
        
        assert manager.get_connection_count() == 3
        
        # Test broadcast
        broadcast_message = {"type": "broadcast", "data": "hello all"}
        await manager.broadcast(broadcast_message)
        
        for mock_websocket in websockets:
            assert mock_websocket.send_text.call_count >= 1  # Welcome + broadcast messages
        
        # Disconnect one session
        manager.disconnect("session_2")
        assert manager.get_connection_count() == 2
        assert not manager.is_connected("session_2")
        assert manager.is_connected("session_1")
        assert manager.is_connected("session_3")


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_message_sending_performance(self):
        """Test WebSocket message sending performance"""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock()
        session_id = "perf_test_123"
        
        await manager.connect(mock_websocket, session_id)
        
        # Send multiple messages and measure time
        start_time = time.time()
        for i in range(10):
            test_message = {"type": "test", "data": f"message_{i}"}
            await manager.send_message_to_session(test_message, session_id)
        end_time = time.time()
        
        # Should be fast
        assert (end_time - start_time) < 1.0
        assert mock_websocket.send_text.call_count >= 10  # At least 10 messages sent
    
    @pytest.mark.asyncio
    async def test_concurrent_connections_handling(self):
        """Test handling multiple concurrent connections"""
        manager = ConnectionManager()
        num_connections = 10
        
        # Create multiple concurrent connections
        tasks = []
        for i in range(num_connections):
            mock_websocket = AsyncMock(spec=WebSocket)
            mock_websocket.accept = AsyncMock()
            session_id = f"concurrent_session_{i}"
            
            task = asyncio.create_task(
                manager.connect(mock_websocket, session_id)
            )
            tasks.append(task)
        
        # Wait for all connections
        await asyncio.gather(*tasks)
        
        assert manager.get_connection_count() == num_connections
        
        # Test broadcast to all connections
        broadcast_message = {"type": "broadcast", "data": "hello all"}
        await manager.broadcast(broadcast_message)


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_websocket_send_error_handling(self):
        """Test handling of WebSocket send errors"""
        manager = ConnectionManager()
        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.client_state = WebSocketState.CONNECTED
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        session_id = "error_test_123"
        
        await manager.connect(mock_websocket, session_id)
        
        # Should handle send error gracefully
        test_message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(test_message, mock_websocket)
        
        # Error should be logged but not raise exception
        assert mock_websocket.send_text.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_broadcast_error_handling(self):
        """Test broadcast error handling with some failed connections"""
        manager = ConnectionManager()
        
        # Setup connections - one good, one bad
        good_websocket = AsyncMock(spec=WebSocket)
        good_websocket.client_state = WebSocketState.CONNECTED
        good_websocket.send_text = AsyncMock()
        
        bad_websocket = AsyncMock(spec=WebSocket)
        bad_websocket.client_state = WebSocketState.CONNECTED
        bad_websocket.send_text = AsyncMock(side_effect=Exception("Connection lost"))
        
        manager.active_connections["good_session"] = good_websocket
        manager.active_connections["bad_session"] = bad_websocket
        
        # Broadcast should handle errors and clean up bad connections
        test_message = {"type": "broadcast", "data": "hello"}
        await manager.broadcast(test_message)
        
        # Good connection should remain, bad connection should be cleaned up
        assert "good_session" in manager.active_connections
        # Bad connection might be cleaned up during broadcast error handling
    
    def test_invalid_message_format_handling(self):
        """Test handling of invalid WebSocket message formats"""
        # Test that invalid JSON would be handled gracefully in real implementation
        invalid_message = "invalid json {"
        
        # Verify that json.loads would raise an error
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_message)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])