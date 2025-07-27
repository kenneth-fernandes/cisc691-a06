"""
Tests for Agent-to-Analytics Data Bridge

This module tests the data bridge that connects the AI agent with the visa analytics system
as implemented for issue #27.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

from agent.data_bridge import VisaDataBridge, get_visa_data_bridge
from visa.models import VisaCategory, CountryCode


class TestVisaDataBridge:
    """Test the VisaDataBridge class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_repo = Mock()
        self.mock_analyzer = Mock()
        self.mock_database = Mock()
    
    @patch('agent.data_bridge.VisaBulletinRepository')
    @patch('agent.data_bridge.TrendAnalyzer')
    def test_initialization_success(self, mock_analyzer_class, mock_repo_class):
        """Test successful initialization of data bridge"""
        mock_repo_class.return_value = self.mock_repo
        mock_analyzer_class.return_value = self.mock_analyzer
        self.mock_repo.db = self.mock_database
        
        bridge = VisaDataBridge()
        
        assert bridge.is_available is True
        assert bridge.repository == self.mock_repo
        assert bridge.analyzer == self.mock_analyzer
        assert bridge.database == self.mock_database
        
        mock_repo_class.assert_called_once()
        mock_analyzer_class.assert_called_once_with(self.mock_repo)
    
    @patch('agent.data_bridge.VisaBulletinRepository')
    def test_initialization_failure(self, mock_repo_class):
        """Test initialization failure handling"""
        mock_repo_class.side_effect = Exception("Database connection failed")
        
        bridge = VisaDataBridge()
        
        assert bridge.is_available is False
    
    @patch('agent.data_bridge.VisaBulletinRepository')
    @patch('agent.data_bridge.TrendAnalyzer')
    def test_check_data_availability_success(self, mock_analyzer_class, mock_repo_class):
        """Test successful data availability check"""
        mock_repo_class.return_value = self.mock_repo
        mock_analyzer_class.return_value = self.mock_analyzer
        self.mock_repo.db = self.mock_database
        
        # Mock database stats
        self.mock_database.get_database_stats.return_value = {
            'bulletin_count': 25,
            'year_range': '2020-2025'
        }
        
        bridge = VisaDataBridge()
        availability = bridge.check_data_availability()
        
        assert availability['status'] == 'available'
        assert availability['total_bulletins'] == 25
        assert availability['date_range'] == '2020-2025'
        assert len(availability['categories_available']) == 10  # All visa categories
        assert len(availability['countries_available']) == 5   # All countries
    
    @patch('agent.data_bridge.VisaBulletinRepository')
    @patch('agent.data_bridge.TrendAnalyzer')
    def test_check_data_availability_unavailable(self, mock_analyzer_class, mock_repo_class):
        """Test data availability check when system is unavailable"""
        mock_repo_class.side_effect = Exception("Connection failed")
        
        bridge = VisaDataBridge()
        availability = bridge.check_data_availability()
        
        assert availability['status'] == 'unavailable'
        assert 'message' in availability
    
    @patch('agent.data_bridge.VisaBulletinRepository')
    @patch('agent.data_bridge.TrendAnalyzer')
    def test_check_data_availability_error(self, mock_analyzer_class, mock_repo_class):
        """Test data availability check with database error"""
        mock_repo_class.return_value = self.mock_repo
        mock_analyzer_class.return_value = self.mock_analyzer
        self.mock_repo.db = self.mock_database
        
        # Mock database error
        self.mock_database.get_database_stats.side_effect = Exception("Database error")
        
        bridge = VisaDataBridge()
        availability = bridge.check_data_availability()
        
        assert availability['status'] == 'error'
        assert 'Database error' in availability['message']


class TestVisaContextExtraction:
    """Test visa context extraction from user queries"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('agent.data_bridge.VisaBulletinRepository'), \
             patch('agent.data_bridge.TrendAnalyzer'):
            self.bridge = VisaDataBridge()
    
    def test_extract_visa_context_trend_query(self):
        """Test context extraction for trend analysis queries"""
        query = "How is EB-2 India trending?"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is True
        assert context['categories'] == ['EB-2']
        assert context['countries'] == ['India']
        assert context['query_type'] == 'trend_analysis'
        assert 'eb-2' in context['keywords']
        assert 'india' in context['keywords']
        assert 'trend' in context['keywords']
    
    def test_extract_visa_context_comparison_query(self):
        """Test context extraction for comparison queries"""
        query = "Compare EB categories for China"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is True
        assert context['categories'] == []  # No specific categories mentioned
        assert context['countries'] == ['China']
        assert context['query_type'] == 'comparison'
        assert 'china' in context['keywords']
    
    def test_extract_visa_context_prediction_query(self):
        """Test context extraction for prediction queries"""
        query = "Predict EB-1 movement for next 3 months"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is True
        assert context['categories'] == ['EB-1']
        assert context['countries'] == []  # No country mentioned
        assert context['query_type'] == 'prediction'
        assert 'eb-1' in context['keywords']
        assert 'movement' in context['keywords']
    
    def test_extract_visa_context_summary_query(self):
        """Test context extraction for summary queries"""
        query = "Give me a summary of all visa categories"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is True
        assert context['categories'] == []
        assert context['countries'] == []
        assert context['query_type'] == 'summary'
        assert 'visa' in context['keywords']
    
    def test_extract_visa_context_explanation_query(self):
        """Test context extraction for explanation queries"""
        query = "What is the current status of EB-2 China?"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is True
        assert context['categories'] == ['EB-2']
        assert context['countries'] == ['China']
        assert context['query_type'] == 'explanation'
    
    def test_extract_visa_context_non_visa_query(self):
        """Test context extraction for non-visa related queries"""
        query = "What's the weather like today?"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is False
        assert context['categories'] == []
        assert context['countries'] == []
        assert context['query_type'] == 'explanation'  # Default type
        assert context['keywords'] == []
    
    def test_extract_visa_context_multiple_categories(self):
        """Test context extraction with multiple categories"""
        query = "Compare EB-1, EB-2, and F1 for India"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is True
        assert 'EB-1' in context['categories']
        assert 'EB-2' in context['categories'] 
        assert 'F1' in context['categories']
        assert context['countries'] == ['India']
        assert context['query_type'] == 'comparison'
    
    def test_extract_visa_context_case_insensitive(self):
        """Test that context extraction is case insensitive"""
        query = "how is eb-2 INDIA trending?"
        context = self.bridge.extract_visa_context(query)
        
        assert context['is_visa_related'] is True
        assert context['categories'] == ['EB-2']
        assert context['countries'] == ['India']


class TestGetRelevantData:
    """Test getting relevant data based on context"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_analyzer = Mock()
        with patch('agent.data_bridge.VisaBulletinRepository'), \
             patch('agent.data_bridge.TrendAnalyzer', return_value=self.mock_analyzer):
            self.bridge = VisaDataBridge()
    
    def test_get_relevant_data_not_visa_related(self):
        """Test getting data for non-visa queries"""
        context = {'is_visa_related': False}
        result = self.bridge.get_relevant_data(context)
        
        assert result['status'] == 'not_applicable'
    
    def test_get_relevant_data_trend_analysis(self):
        """Test getting data for trend analysis"""
        context = {
            'is_visa_related': True,
            'query_type': 'trend_analysis',
            'categories': ['EB-2'],
            'countries': ['India']
        }
        
        # Mock trend analysis result
        mock_trend_data = {
            'status': 'success',
            'category': 'EB-2',
            'country': 'INDIA',
            'average_advancement_days': 15.0
        }
        self.mock_analyzer.calculate_advancement_trends.return_value = mock_trend_data
        
        # Patch the enum conversions to work correctly
        with patch('agent.data_bridge.VisaCategory') as mock_visa_cat, \
             patch('agent.data_bridge.CountryCode') as mock_country_code:
            
            from visa.models import VisaCategory, CountryCode
            mock_visa_cat.return_value = VisaCategory.EB2
            mock_country_code.return_value = CountryCode.INDIA
            
            result = self.bridge.get_relevant_data(context)
            
            assert result['status'] == 'success'
            # Check if trend analysis was called
            self.mock_analyzer.calculate_advancement_trends.assert_called_once_with(
                VisaCategory.EB2, CountryCode.INDIA, years_back=3
            )
    
    def test_get_relevant_data_comparison(self):
        """Test getting data for category comparison"""
        context = {
            'is_visa_related': True,
            'query_type': 'comparison',
            'categories': [],
            'countries': ['China']
        }
        
        # Mock comparison result
        mock_comparison_data = {
            'country': 'CHINA',
            'categories': {'EB-1': {'average_advancement': 20.0}}
        }
        self.mock_analyzer.compare_categories.return_value = mock_comparison_data
        
        # Patch the enum conversion for country
        with patch('agent.data_bridge.CountryCode') as mock_country_code:
            from visa.models import CountryCode
            mock_country_code.return_value = CountryCode.CHINA
            
            result = self.bridge.get_relevant_data(context)
            
            assert result['status'] == 'success'
            # Check if comparison was called
            self.mock_analyzer.compare_categories.assert_called_once_with(CountryCode.CHINA)
    
    def test_get_relevant_data_summary(self):
        """Test getting data for summary report"""
        context = {
            'is_visa_related': True,
            'query_type': 'summary',
            'categories': [],
            'countries': []
        }
        
        # Mock summary result
        mock_summary_data = {
            'generated_at': '2024-01-15T10:30:00',
            'overall_trends': {'general_observations': ['Test observation']}
        }
        self.mock_analyzer.generate_summary_report.return_value = mock_summary_data
        
        result = self.bridge.get_relevant_data(context)
        
        assert result['status'] == 'success'
        assert 'summary_report' in result['context_data']
    
    def test_get_relevant_data_invalid_category(self):
        """Test handling of invalid visa category"""
        context = {
            'is_visa_related': True,
            'query_type': 'trend_analysis',
            'categories': ['EB2'],  # Missing dash
            'countries': ['INDIA']
        }
        
        result = self.bridge.get_relevant_data(context)
        
        # Should complete successfully but without trend analysis data
        assert result['status'] == 'success'
        assert 'trend_analysis' not in result['context_data']
    
    def test_get_relevant_data_exception(self):
        """Test exception handling during data retrieval"""
        context = {
            'is_visa_related': True,
            'query_type': 'trend_analysis',
            'categories': ['EB-2'],
            'countries': ['India']
        }
        
        # Mock analyzer exception
        self.mock_analyzer.calculate_advancement_trends.side_effect = Exception("Database error")
        
        # Patch the enum conversions to work correctly
        with patch('agent.data_bridge.VisaCategory') as mock_visa_cat, \
             patch('agent.data_bridge.CountryCode') as mock_country_code:
            
            from visa.models import VisaCategory, CountryCode
            mock_visa_cat.return_value = VisaCategory.EB2
            mock_country_code.return_value = CountryCode.INDIA
            
            result = self.bridge.get_relevant_data(context)
            
            # Analyzer exception causes the whole method to return error status
            assert result['status'] == 'error'
            assert 'Database error' in result['message']
            # Verify the analyzer was called
            self.mock_analyzer.calculate_advancement_trends.assert_called_once_with(
                VisaCategory.EB2, CountryCode.INDIA, years_back=3
            )


class TestDataContextInjection:
    """Test data context injection into prompts"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_analyzer = Mock()
        with patch('agent.data_bridge.VisaBulletinRepository'), \
             patch('agent.data_bridge.TrendAnalyzer', return_value=self.mock_analyzer):
            self.bridge = VisaDataBridge()
    
    def test_inject_data_context_visa_query(self):
        """Test context injection for visa-related queries"""
        user_query = "How is EB-2 India trending?"
        base_prompt = "You are a helpful assistant."
        
        # Mock the get_relevant_data method directly to return expected data
        with patch.object(self.bridge, 'get_relevant_data') as mock_get_data:
            mock_get_data.return_value = {
                'status': 'success',
                'context_data': {
                    'trend_analysis': {
                        'status': 'success',
                        'category': 'EB-2',
                        'country': 'INDIA',
                        'average_advancement_days': 15.5,
                        'trend_direction': 'advancing',
                        'volatility': 'moderate',
                        'data_points': 24,
                        'interpretation': 'EB-2 for INDIA is advancing steadily.'
                    }
                }
            }
            
            enhanced_prompt = self.bridge.inject_data_context(user_query, base_prompt)
            
            assert base_prompt in enhanced_prompt
            assert "RELEVANT VISA DATA" in enhanced_prompt
            assert "EB-2-INDIA" in enhanced_prompt
            assert "15.5 days/month" in enhanced_prompt
            assert "advancing" in enhanced_prompt
    
    def test_inject_data_context_non_visa_query(self):
        """Test context injection for non-visa queries"""
        user_query = "What's the weather today?"
        base_prompt = "You are a helpful assistant."
        
        enhanced_prompt = self.bridge.inject_data_context(user_query, base_prompt)
        
        # Should return unchanged prompt
        assert enhanced_prompt == base_prompt
    
    def test_inject_data_context_comparison_query(self):
        """Test context injection for comparison queries"""
        user_query = "Compare EB categories for China"
        base_prompt = "You are a visa expert."
        
        # Mock the get_relevant_data method directly to return expected data
        with patch.object(self.bridge, 'get_relevant_data') as mock_get_data:
            mock_get_data.return_value = {
                'status': 'success',
                'context_data': {
                    'category_comparison': {
                        'country': 'CHINA',
                        'categories': {
                            'EB-1': {
                                'average_advancement': 20.0,
                                'trend_direction': 'advancing'
                            },
                            'EB-2': {
                                'average_advancement': 5.0,
                                'trend_direction': 'stable'
                            }
                        }
                    }
                }
            }
            
            enhanced_prompt = self.bridge.inject_data_context(user_query, base_prompt)
            
            assert "RELEVANT VISA DATA" in enhanced_prompt
            assert "Category Comparison for CHINA" in enhanced_prompt
            assert "EB-1: 20.0 days/month" in enhanced_prompt
            assert "EB-2: 5.0 days/month" in enhanced_prompt
    
    def test_inject_data_context_system_unavailable(self):
        """Test context injection when system is unavailable"""
        with patch('agent.data_bridge.VisaBulletinRepository'), \
             patch('agent.data_bridge.TrendAnalyzer'):
            bridge = VisaDataBridge()
            bridge.is_available = False
        
        user_query = "How is EB-2 India trending?"
        base_prompt = "You are a helpful assistant."
        
        enhanced_prompt = bridge.inject_data_context(user_query, base_prompt)
        
        # Should return unchanged prompt when system unavailable
        assert enhanced_prompt == base_prompt
    
    def test_inject_data_context_exception_handling(self):
        """Test exception handling during context injection"""
        user_query = "How is EB-2 India trending?"
        base_prompt = "You are a helpful assistant."
        
        # Mock exception during get_relevant_data
        with patch.object(self.bridge, 'get_relevant_data') as mock_get_data:
            mock_get_data.side_effect = Exception("Database error")
            
            enhanced_prompt = self.bridge.inject_data_context(user_query, base_prompt)
            
            # Should return base prompt on exception
            assert enhanced_prompt == base_prompt


class TestDataUnavailableScenarios:
    """Test handling of data unavailable scenarios"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('agent.data_bridge.VisaBulletinRepository'), \
             patch('agent.data_bridge.TrendAnalyzer'):
            self.bridge = VisaDataBridge()
    
    def test_handle_data_unavailable_non_visa_query(self):
        """Test handling non-visa queries"""
        response = self.bridge.handle_data_unavailable_scenario("What's the weather?")
        assert response is None
    
    def test_handle_data_unavailable_system_unavailable(self):
        """Test handling when system is unavailable"""
        self.bridge.is_available = False
        
        response = self.bridge.handle_data_unavailable_scenario("How is EB-2 India trending?")
        
        assert response is not None
        assert "unable to access" in response
        assert "historical visa bulletin data system" in response
    
    @patch.object(VisaDataBridge, 'check_data_availability')
    def test_handle_data_unavailable_system_error(self, mock_check):
        """Test handling when system has errors"""
        mock_check.return_value = {
            'status': 'error',
            'message': 'Database connection failed'
        }
        
        response = self.bridge.handle_data_unavailable_scenario("How is EB-2 India trending?")
        
        assert response is not None
        assert "trouble accessing the visa data" in response
        assert "Database connection failed" in response


class TestDataSummaryForContext:
    """Test data summary generation for context setting"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_database = Mock()
        with patch('agent.data_bridge.VisaBulletinRepository') as mock_repo_class, \
             patch('agent.data_bridge.TrendAnalyzer'):
            mock_repo = Mock()
            mock_repo.db = self.mock_database
            mock_repo_class.return_value = mock_repo
            self.bridge = VisaDataBridge()
    
    def test_get_data_summary_available(self):
        """Test data summary when system is available"""
        self.mock_database.get_database_stats.return_value = {
            'bulletin_count': 25,
            'year_range': '2020-2025'
        }
        
        summary = self.bridge.get_data_summary_for_context()
        
        assert "I have access to 25 visa bulletins" in summary
        assert "spanning from 2020-2025" in summary
        assert "trend analysis, predictions, and comparisons" in summary
    
    def test_get_data_summary_unavailable(self):
        """Test data summary when system is unavailable"""
        self.bridge.is_available = False
        
        summary = self.bridge.get_data_summary_for_context()
        
        assert "Visa data system is currently unavailable" in summary
    
    def test_get_data_summary_error(self):
        """Test data summary with database error"""
        # Mock check_data_availability to raise an exception
        with patch.object(self.bridge, 'check_data_availability') as mock_check:
            mock_check.side_effect = Exception("Database error")
            
            summary = self.bridge.get_data_summary_for_context()
            
            assert "Unable to access visa data summary" in summary


class TestGetVisaDataBridge:
    """Test the global visa data bridge factory function"""
    
    def test_get_visa_data_bridge_singleton(self):
        """Test that get_visa_data_bridge returns singleton instance"""
        with patch('agent.data_bridge.VisaBulletinRepository'), \
             patch('agent.data_bridge.TrendAnalyzer'):
            
            bridge1 = get_visa_data_bridge()
            bridge2 = get_visa_data_bridge()
            
            # Should return the same instance
            assert bridge1 is bridge2
    
    def test_get_visa_data_bridge_type(self):
        """Test that get_visa_data_bridge returns correct type"""
        with patch('agent.data_bridge.VisaBulletinRepository'), \
             patch('agent.data_bridge.TrendAnalyzer'):
            
            bridge = get_visa_data_bridge()
            
            assert isinstance(bridge, VisaDataBridge)