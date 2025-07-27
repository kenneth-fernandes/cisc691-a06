"""
WebSocket client for real-time agent communication
"""
import asyncio
import json
import threading
import time
from typing import Callable, Optional, Dict, Any
import websockets
import streamlit as st
import logging
from datetime import datetime

from utils.config import get_config

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for real-time communication with agent"""
    
    def __init__(self, session_id: str):
        self.config = get_config()
        self.session_id = session_id
        self.websocket = None
        self.is_connected = False
        self.is_connecting = False
        self.message_callbacks = []
        self.error_callbacks = []
        self.connection_callbacks = []
        self.loop = None
        self.thread = None
        
        # Generate WebSocket URL
        base_url = self.config.API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
        self.websocket_url = f"{base_url}/api/websocket/chat/{session_id}"
    
    def add_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for incoming messages"""
        self.message_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Add callback for errors"""
        self.error_callbacks.append(callback)
    
    def add_connection_callback(self, callback: Callable[[bool], None]):
        """Add callback for connection status changes"""
        self.connection_callbacks.append(callback)
    
    def connect(self):
        """Connect to WebSocket (non-blocking)"""
        if self.is_connected or self.is_connecting:
            return
        
        self.is_connecting = True
        
        # Start WebSocket in separate thread
        self.thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.thread.start()
        
        logger.info(f"WebSocket connection initiated for session: {self.session_id}")
    
    def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket and self.is_connected:
            asyncio.run_coroutine_threadsafe(
                self.websocket.close(),
                self.loop
            ).result(timeout=5)
        
        self.is_connected = False
        self.is_connecting = False
        logger.info(f"WebSocket disconnected for session: {self.session_id}")
    
    def send_message(self, message: str, config: Optional[Dict[str, Any]] = None):
        """Send chat message via WebSocket"""
        if not self.is_connected:
            self._trigger_error_callbacks("WebSocket not connected")
            return False
        
        message_data = {
            "type": "chat",
            "message": message,
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if self.loop and self.websocket:
                future = asyncio.run_coroutine_threadsafe(
                    self.websocket.send(json.dumps(message_data)),
                    self.loop
                )
                future.result(timeout=5)
                return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self._trigger_error_callbacks(f"Failed to send message: {str(e)}")
            return False
    
    def send_typing_indicator(self, is_typing: bool):
        """Send typing indicator"""
        if not self.is_connected:
            return
        
        typing_data = {
            "type": "typing",
            "is_typing": is_typing,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if self.loop and self.websocket:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(json.dumps(typing_data)),
                    self.loop
                )
        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")
    
    def _run_websocket(self):
        """Run WebSocket connection in event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._websocket_handler())
        except Exception as e:
            logger.error(f"WebSocket thread error: {e}")
            self._trigger_error_callbacks(f"Connection error: {str(e)}")
        finally:
            self.is_connected = False
            self.is_connecting = False
            self._trigger_connection_callbacks(False)
    
    async def _websocket_handler(self):
        """Handle WebSocket connection and messages"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Attempting WebSocket connection to: {self.websocket_url}")
                
                async with websockets.connect(
                    self.websocket_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.is_connected = True
                    self.is_connecting = False
                    retry_count = 0  # Reset retry count on successful connection
                    
                    logger.info(f"WebSocket connected successfully for session: {self.session_id}")
                    self._trigger_connection_callbacks(True)
                    
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    
                    try:
                        async for message in websocket:
                            await self._handle_message(message)
                    
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket connection closed")
                    except Exception as e:
                        logger.error(f"WebSocket message handling error: {e}")
                        self._trigger_error_callbacks(f"Message handling error: {str(e)}")
                    
                    finally:
                        heartbeat_task.cancel()
                        try:
                            await heartbeat_task
                        except asyncio.CancelledError:
                            pass
            
            except Exception as e:
                retry_count += 1
                logger.error(f"WebSocket connection failed (attempt {retry_count}): {e}")
                
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                else:
                    self._trigger_error_callbacks(f"Failed to connect after {max_retries} attempts: {str(e)}")
                    break
        
        self.is_connected = False
        self.is_connecting = False
        self._trigger_connection_callbacks(False)
    
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            self._trigger_message_callbacks(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            self._trigger_error_callbacks(f"Invalid message format: {str(e)}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        try:
            while self.is_connected:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
                if self.websocket and self.is_connected:
                    heartbeat_data = {
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.websocket.send(json.dumps(heartbeat_data))
        
        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
    
    def _trigger_message_callbacks(self, data: Dict[str, Any]):
        """Trigger all message callbacks"""
        for callback in self.message_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Message callback error: {e}")
    
    def _trigger_error_callbacks(self, error: str):
        """Trigger all error callbacks"""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error callback error: {e}")
    
    def _trigger_connection_callbacks(self, is_connected: bool):
        """Trigger all connection callbacks"""
        for callback in self.connection_callbacks:
            try:
                callback(is_connected)
            except Exception as e:
                logger.error(f"Connection callback error: {e}")
    
    @property
    def connection_status(self) -> str:
        """Get current connection status"""
        if self.is_connected:
            return "connected"
        elif self.is_connecting:
            return "connecting"
        else:
            return "disconnected"


@st.cache_resource
def get_websocket_client(session_id: str) -> WebSocketClient:
    """Get cached WebSocket client for session"""
    return WebSocketClient(session_id)