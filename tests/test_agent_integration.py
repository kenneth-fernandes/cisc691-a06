"""
Tests for Agent Integration with Visa Analytics

This module tests the changes made to the AIAgent class to integrate
visa analytics tools and data bridge functionality for issues #25 and #27.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from agent.core import AIAgent


class TestAIAgentInitialization:
    """Test AIAgent initialization with visa analytics integration"""
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_agent_init_general_mode(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test agent initialization in general mode"""
        # Mock dependencies
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        
        mock_bridge = Mock()
        mock_bridge.get_data_summary_for_context.return_value = "Test summary"
        mock_get_bridge.return_value = mock_bridge
        
        mock_get_tools.return_value = []
        
        # Set environment variable for Ollama
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="general")
            
            # Verify initialization
            assert agent.mode == "general"
            assert agent.data_bridge == mock_bridge
            assert len(agent.visa_tools) == 0  # No tools in general mode
            assert agent.agent_executor is None
            
            # Verify data bridge was called
            mock_get_bridge.assert_called_once()
            mock_get_tools.assert_not_called()  # Should not get tools in general mode
            
        finally:
            # Clean up environment
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_agent_init_visa_expert_mode(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test agent initialization in visa expert mode"""
        # Mock dependencies
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        
        mock_bridge = Mock()
        mock_bridge.get_data_summary_for_context.return_value = "I have access to 25 visa bulletins."
        mock_get_bridge.return_value = mock_bridge
        
        # Mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "visa_trend_analysis"
        mock_tool2 = Mock()
        mock_tool2.name = "visa_category_comparison"
        mock_get_tools.return_value = [mock_tool1, mock_tool2]
        
        # Set environment variable for Ollama
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            # Verify initialization
            assert agent.mode == "visa_expert"
            assert agent.data_bridge == mock_bridge
            assert len(agent.visa_tools) == 2
            assert agent.visa_tools[0] == mock_tool1
            assert agent.visa_tools[1] == mock_tool2
            
            # Verify calls
            mock_get_bridge.assert_called_once()
            mock_get_tools.assert_called_once()
            mock_bridge.get_data_summary_for_context.assert_called_once()
            
        finally:
            # Clean up environment
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_agent_init_system_prompt_enhancement(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test that system prompt is enhanced with data summary in visa expert mode"""
        # Mock dependencies
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        
        mock_bridge = Mock()
        data_summary = "I have access to 50 visa bulletins spanning from 2020-2025."
        mock_bridge.get_data_summary_for_context.return_value = data_summary
        mock_get_bridge.return_value = mock_bridge
        
        mock_get_tools.return_value = []
        
        # Set environment variable
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            # Verify system prompt contains data summary
            assert data_summary in agent.system_prompt
            assert "DATA ACCESS CAPABILITIES" in agent.system_prompt
            assert "visa_trend_analysis" in agent.system_prompt
            assert "visa_category_comparison" in agent.system_prompt
            
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)


class TestAIAgentToolIntegration:
    """Test AIAgent integration with visa analytics tools"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_bridge = Mock()
        self.mock_tool = Mock()
        self.mock_tool.name = "visa_trend_analysis"
        
        # Mock data bridge methods
        self.mock_bridge.get_data_summary_for_context.return_value = "Test summary"
        self.mock_bridge.handle_data_unavailable_scenario.return_value = None
        self.mock_bridge.extract_visa_context.return_value = {
            'is_visa_related': True,
            'categories': ['EB-2'],
            'countries': ['INDIA'],
            'query_type': 'trend_analysis'
        }
        self.mock_bridge.inject_data_context.return_value = "Enhanced prompt"
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    @patch('agent.core.create_tool_calling_agent', None)  # Disable agent executor
    def test_manual_tool_integration_trend_analysis(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test manual tool integration for trend analysis"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = [self.mock_tool]
        
        # Set environment variable
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            # Mock tool execution
            with patch('agent.visa_tools.VisaTrendAnalysisTool') as mock_tool_class:
                mock_tool_instance = Mock()
                mock_tool_instance._run.return_value = "Trend analysis result"
                mock_tool_class.return_value = mock_tool_instance
                
                # Test manual tool integration
                result = agent._manual_tool_integration("How is EB-2 India trending?")
                
                # Verify tool was called
                mock_tool_class.assert_called_once()
                mock_tool_instance._run.assert_called_once_with('EB-2', 'INDIA')
                assert result == "Trend analysis result"
                
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    @patch('agent.core.create_tool_calling_agent', None)
    def test_manual_tool_integration_comparison(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test manual tool integration for category comparison"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = [self.mock_tool]
        
        # Mock comparison context
        self.mock_bridge.extract_visa_context.return_value = {
            'is_visa_related': True,
            'categories': ['EB-1', 'EB-2'],
            'countries': ['CHINA'],
            'query_type': 'comparison'
        }
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            # Mock tool execution
            with patch('agent.visa_tools.VisaCategoryComparisonTool') as mock_tool_class:
                mock_tool_instance = Mock()
                mock_tool_instance._run.return_value = "Comparison result"
                mock_tool_class.return_value = mock_tool_instance
                
                result = agent._manual_tool_integration("Compare EB categories for China")
                
                # Verify tool was called with correct parameters
                mock_tool_instance._run.assert_called_once_with('CHINA', ['EB-1', 'EB-2'])
                assert result == "Comparison result"
                
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    @patch('agent.core.create_tool_calling_agent', None)
    def test_manual_tool_integration_prediction(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test manual tool integration for movement prediction"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = [self.mock_tool]
        
        # Mock prediction context
        self.mock_bridge.extract_visa_context.return_value = {
            'is_visa_related': True,
            'categories': ['EB-1'],
            'countries': ['INDIA'],
            'query_type': 'prediction'
        }
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            with patch('agent.visa_tools.VisaMovementPredictionTool') as mock_tool_class:
                mock_tool_instance = Mock()
                mock_tool_instance._run.return_value = "Prediction result"
                mock_tool_class.return_value = mock_tool_instance
                
                result = agent._manual_tool_integration("Predict EB-1 India movement")
                
                mock_tool_instance._run.assert_called_once_with('EB-1', 'INDIA')
                assert result == "Prediction result"
                
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    @patch('agent.core.create_tool_calling_agent', None)
    def test_manual_tool_integration_summary(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test manual tool integration for summary report"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = [self.mock_tool]
        
        # Mock summary context
        self.mock_bridge.extract_visa_context.return_value = {
            'is_visa_related': True,
            'categories': [],
            'countries': [],
            'query_type': 'summary'
        }
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            with patch('agent.visa_tools.VisaSummaryReportTool') as mock_tool_class:
                mock_tool_instance = Mock()
                mock_tool_instance._run.return_value = "Summary result"
                mock_tool_class.return_value = mock_tool_instance
                
                result = agent._manual_tool_integration("Generate summary report")
                
                mock_tool_instance._run.assert_called_once_with(None, None)
                assert result == "Summary result"
                
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_manual_tool_integration_non_visa_query(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test manual tool integration with non-visa query"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = [self.mock_tool]
        
        # Mock non-visa context
        self.mock_bridge.extract_visa_context.return_value = {
            'is_visa_related': False,
            'categories': [],
            'countries': [],
            'query_type': 'general'
        }
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            result = agent._manual_tool_integration("What's the weather like?")
            
            # Should return None for non-visa queries
            assert result is None
            
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)


class TestAIAgentChatIntegration:
    """Test chat functionality with visa analytics integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_bridge = Mock()
        self.mock_bridge.get_data_summary_for_context.return_value = "Test summary"
        self.mock_bridge.handle_data_unavailable_scenario.return_value = None
        self.mock_bridge.inject_data_context.return_value = "Enhanced prompt with data"
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    @patch('agent.core.create_tool_calling_agent', None)  # Disable agent executor
    def test_chat_with_data_context_injection(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test chat with data context injection"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = []
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            # Mock LLM response
            with patch.object(agent, 'llm') as mock_llm:
                mock_response = Mock()
                mock_response.content = "Visa analysis response"
                mock_llm.invoke.return_value = mock_response
                
                response = agent.chat("How is EB-2 India trending?")
                
                # Verify data context injection was called
                self.mock_bridge.inject_data_context.assert_called_once()
                
                # Verify LLM was called
                mock_llm.invoke.assert_called_once()
                
                assert response == "Visa analysis response"
                
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_chat_with_data_unavailable_scenario(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test chat when data is unavailable"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = []
        
        # Mock data unavailable scenario
        unavailable_message = "Sorry, visa data system is currently unavailable."
        self.mock_bridge.handle_data_unavailable_scenario.return_value = unavailable_message
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            response = agent.chat("How is EB-2 India trending?")
            
            # Should return the unavailable message directly
            assert response == unavailable_message
            
            # Verify message was saved to memory
            history = agent.get_conversation_history()
            assert len(history) == 2  # User message + assistant response
            assert history[0]['role'] == 'user'
            assert history[1]['role'] == 'assistant'
            assert history[1]['content'] == unavailable_message
            
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    @patch('agent.core.create_tool_calling_agent', None)
    def test_chat_with_manual_tool_integration(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test chat with manual tool integration fallback"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        
        mock_tool = Mock()
        mock_tool.name = "visa_trend_analysis"
        mock_get_tools.return_value = [mock_tool]
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            # Mock manual tool integration
            with patch.object(agent, '_manual_tool_integration') as mock_manual_tool:
                mock_manual_tool.return_value = "Tool integration response"
                
                response = agent.chat("How is EB-2 India trending?")
                
                # Should use manual tool integration
                mock_manual_tool.assert_called_once_with("How is EB-2 India trending?")
                assert response == "Tool integration response"
                
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_chat_general_mode_no_visa_integration(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test chat in general mode without visa integration"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        mock_get_bridge.return_value = self.mock_bridge
        mock_get_tools.return_value = []
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="general")
            
            # Mock LLM response
            with patch.object(agent, 'llm') as mock_llm:
                mock_response = Mock()
                mock_response.content = "General response"
                mock_llm.invoke.return_value = mock_response
                
                response = agent.chat("Hello, how are you?")
                
                # Should not call visa-specific methods
                self.mock_bridge.handle_data_unavailable_scenario.assert_not_called()
                self.mock_bridge.inject_data_context.assert_not_called()
                
                assert response == "General response"
                
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)


class TestAIAgentErrorHandling:
    """Test error handling in agent integration"""
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_agent_init_with_bridge_failure(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test agent initialization when data bridge fails"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        
        # Mock bridge failure during data summary call
        mock_bridge = Mock()
        mock_bridge.get_data_summary_for_context.side_effect = Exception("Bridge failed")
        mock_get_bridge.return_value = mock_bridge
        mock_get_tools.return_value = []
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            # Should raise the exception since it's not currently handled in AIAgent init
            with pytest.raises(Exception, match="Bridge failed"):
                AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)
    
    @patch('agent.core.get_visa_data_bridge')
    @patch('agent.core.get_visa_analytics_tools')
    @patch('agent.core.get_config')
    def test_manual_tool_integration_error_handling(self, mock_get_config, mock_get_tools, mock_get_bridge):
        """Test error handling in manual tool integration"""
        # Setup mocks
        mock_config = Mock()
        mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_get_config.return_value = mock_config
        
        mock_bridge = Mock()
        mock_bridge.get_data_summary_for_context.return_value = "Test summary"
        mock_bridge.extract_visa_context.side_effect = Exception("Context extraction failed")
        mock_get_bridge.return_value = mock_bridge
        mock_get_tools.return_value = []
        
        os.environ['OLLAMA_API_KEY'] = 'test'
        
        try:
            agent = AIAgent(provider="ollama", model_name="llama3.2", mode="visa_expert")
            
            # Should handle exception gracefully
            result = agent._manual_tool_integration("How is EB-2 India trending?")
            
            # Should return None on error
            assert result is None
            
        finally:
            os.environ.pop('OLLAMA_API_KEY', None)