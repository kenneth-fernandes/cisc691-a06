"""
Tests for LangChain Visa Analytics Tools

This module tests the LangChain tools that provide visa analytics data access
as implemented for issue #25.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

from agent.visa_tools import (
    VisaTrendAnalysisTool,
    VisaCategoryComparisonTool, 
    VisaMovementPredictionTool,
    VisaSummaryReportTool,
    get_visa_analytics_tools,
    TrendAnalysisInput,
    CategoryComparisonInput,
    MovementPredictionInput,
    SummaryReportInput
)
from visa.models import VisaCategory, CountryCode


class TestTrendAnalysisInput:
    """Test the input schema for trend analysis tool"""
    
    def test_valid_input(self):
        """Test valid input creation"""
        input_data = TrendAnalysisInput(
            category="EB-2",
            country="INDIA", 
            years_back=3
        )
        assert input_data.category == "EB-2"
        assert input_data.country == "INDIA"
        assert input_data.years_back == 3
    
    def test_default_years_back(self):
        """Test default years_back value"""
        input_data = TrendAnalysisInput(
            category="EB-1",
            country="CHINA"
        )
        assert input_data.years_back == 3


class TestCategoryComparisonInput:
    """Test the input schema for category comparison tool"""
    
    def test_valid_input_with_categories(self):
        """Test valid input with specific categories"""
        input_data = CategoryComparisonInput(
            country="INDIA",
            categories=["EB-1", "EB-2", "EB-3"],
            years_back=2
        )
        assert input_data.country == "INDIA"
        assert input_data.categories == ["EB-1", "EB-2", "EB-3"]
        assert input_data.years_back == 2
    
    def test_default_values(self):
        """Test default values"""
        input_data = CategoryComparisonInput(country="CHINA")
        assert input_data.country == "CHINA"
        assert input_data.categories is None
        assert input_data.years_back == 2


class TestMovementPredictionInput:
    """Test the input schema for movement prediction tool"""
    
    def test_valid_input(self):
        """Test valid input creation"""
        input_data = MovementPredictionInput(
            category="EB-2",
            country="INDIA",
            months_ahead=6
        )
        assert input_data.category == "EB-2"
        assert input_data.country == "INDIA"
        assert input_data.months_ahead == 6
    
    def test_default_months_ahead(self):
        """Test default months_ahead value"""
        input_data = MovementPredictionInput(
            category="F1",
            country="WORLDWIDE"
        )
        assert input_data.months_ahead == 3


class TestSummaryReportInput:
    """Test the input schema for summary report tool"""
    
    def test_valid_input_with_filters(self):
        """Test valid input with category and country filters"""
        input_data = SummaryReportInput(
            categories=["EB-1", "EB-2"],
            countries=["INDIA", "CHINA"]
        )
        assert input_data.categories == ["EB-1", "EB-2"]
        assert input_data.countries == ["INDIA", "CHINA"]
    
    def test_default_values(self):
        """Test default values (None for both)"""
        input_data = SummaryReportInput()
        assert input_data.categories is None
        assert input_data.countries is None


class TestVisaTrendAnalysisTool:
    """Test the Visa Trend Analysis Tool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = VisaTrendAnalysisTool()
    
    def test_tool_metadata(self):
        """Test tool name and description"""
        assert self.tool.name == "visa_trend_analysis"
        assert "trend" in self.tool.description.lower()
        assert "historical" in self.tool.description.lower()
        assert self.tool.args_schema == TrendAnalysisInput
    
    def test_normalize_category_valid(self):
        """Test category normalization with valid inputs"""
        assert self.tool._normalize_category("EB-1") == VisaCategory.EB1
        assert self.tool._normalize_category("EB-2") == VisaCategory.EB2
        assert self.tool._normalize_category("eb-3") == VisaCategory.EB3
        assert self.tool._normalize_category("F1") == VisaCategory.F1
        assert self.tool._normalize_category("f2a") == VisaCategory.F2A
    
    def test_normalize_category_invalid(self):
        """Test category normalization with invalid inputs"""
        with pytest.raises(ValueError, match="Unknown category"):
            self.tool._normalize_category("INVALID")
    
    def test_normalize_country_valid(self):
        """Test country normalization with valid inputs"""
        assert self.tool._normalize_country("INDIA") == CountryCode.INDIA
        assert self.tool._normalize_country("india") == CountryCode.INDIA
        assert self.tool._normalize_country("IN") == CountryCode.INDIA
        assert self.tool._normalize_country("CHINA") == CountryCode.CHINA
        assert self.tool._normalize_country("WORLDWIDE") == CountryCode.WORLDWIDE
        assert self.tool._normalize_country("ROW") == CountryCode.WORLDWIDE
    
    def test_normalize_country_invalid(self):
        """Test country normalization with invalid inputs"""
        with pytest.raises(ValueError, match="Unknown country"):
            self.tool._normalize_country("INVALID_COUNTRY")
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    def test_run_successful_analysis(self, mock_analyzer_class, mock_repo_class):
        """Test successful trend analysis execution"""
        # Mock repository and analyzer
        mock_repo = Mock()
        mock_analyzer = Mock()
        mock_repo_class.return_value = mock_repo
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock successful analysis result
        mock_result = {
            'status': 'success',
            'category': 'EB-2',
            'country': 'INDIA',
            'average_advancement_days': 15.5,
            'trend_direction': 'advancing',
            'volatility': 'moderate',
            'data_points': 24,
            'interpretation': 'EB-2 for INDIA is advancing steadily.',
            'total_advancement_days': 372,
            'positive_months': 18,
            'negative_months': 4,
            'stagnant_months': 2,
            'consistency_score': 75.2,
            'momentum': {'status': 'sufficient_data', 'direction': 'stable'},
            'prediction_confidence': {'confidence': 'moderate', 'score': 68.5},
            'seasonal_pattern': {'status': 'insufficient_data'},
            'percentiles': {'25th': 5.0, '50th': 15.0, '75th': 25.0}
        }
        mock_analyzer.calculate_advancement_trends.return_value = mock_result
        
        # Execute tool
        result = self.tool._run("EB-2", "INDIA", 3)
        
        # Verify calls
        mock_repo_class.assert_called_once()
        mock_analyzer_class.assert_called_once_with(mock_repo)
        mock_analyzer.calculate_advancement_trends.assert_called_once_with(
            VisaCategory.EB2, CountryCode.INDIA, 3
        )
        
        # Verify result format
        assert "Trend Analysis for EB-2 - INDIA" in result
        assert "15.5 days" in result  # Match the mock data
        assert "advancing" in result.lower()
        assert "moderate" in result.lower()
        assert "24 bulletins" in result
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    def test_run_insufficient_data(self, mock_analyzer_class, mock_repo_class):
        """Test handling of insufficient data scenario"""
        mock_repo = Mock()
        mock_analyzer = Mock()
        mock_repo_class.return_value = mock_repo
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock insufficient data result
        mock_result = {
            'status': 'insufficient_data',
            'data_points': 2,
            'message': 'Need at least 3 data points for trend analysis'
        }
        mock_analyzer.calculate_advancement_trends.return_value = mock_result
        
        result = self.tool._run("EB-1", "CHINA", 2)
        
        assert "Analysis failed" in result
        assert "Need at least 3 data points" in result
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    def test_run_exception_handling(self, mock_analyzer_class, mock_repo_class):
        """Test exception handling during analysis"""
        mock_repo_class.side_effect = Exception("Database connection failed")
        
        result = self.tool._run("EB-2", "INDIA", 3)
        
        assert "Error analyzing trends for EB-2-INDIA" in result
        assert "Database connection failed" in result


class TestVisaCategoryComparisonTool:
    """Test the Visa Category Comparison Tool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = VisaCategoryComparisonTool()
    
    def test_tool_metadata(self):
        """Test tool name and description"""
        assert self.tool.name == "visa_category_comparison"
        assert "compare" in self.tool.description.lower()
        assert "categories" in self.tool.description.lower()
        assert self.tool.args_schema == CategoryComparisonInput
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    @patch('agent.visa_tools.VisaTrendAnalysisTool')
    def test_run_successful_comparison(self, mock_trend_tool_class, mock_analyzer_class, mock_repo_class):
        """Test successful category comparison"""
        # Mock dependencies
        mock_repo = Mock()
        mock_analyzer = Mock()
        mock_trend_tool = Mock()
        mock_repo_class.return_value = mock_repo
        mock_analyzer_class.return_value = mock_analyzer
        mock_trend_tool_class.return_value = mock_trend_tool
        
        # Mock trend tool normalization methods
        mock_trend_tool._normalize_country.return_value = CountryCode.INDIA
        mock_trend_tool._normalize_category.side_effect = [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3]
        
        # Mock comparison result
        mock_result = {
            'country': 'INDIA',
            'categories': {
                'EB-1': {
                    'average_advancement': 25.0,
                    'trend_direction': 'advancing',
                    'volatility': 'low',
                    'consistency_score': 85.0,
                    'data_points': 24
                },
                'EB-2': {
                    'average_advancement': 10.0,
                    'trend_direction': 'stable',
                    'volatility': 'moderate', 
                    'consistency_score': 70.0,
                    'data_points': 24
                }
            },
            'rankings': {
                'fastest_advancing': [
                    {'category': 'EB-1', 'advancement': 25.0, 'consistency': 85.0},
                    {'category': 'EB-2', 'advancement': 10.0, 'consistency': 70.0}
                ],
                'most_stable': [
                    {'category': 'EB-1', 'consistency': 85.0},
                    {'category': 'EB-2', 'consistency': 70.0}
                ],
                'most_volatile': [
                    {'category': 'EB-2', 'volatility_numeric': 15.0},
                    {'category': 'EB-1', 'volatility_numeric': 8.0}
                ]
            }
        }
        mock_analyzer.compare_categories.return_value = mock_result
        
        result = self.tool._run("INDIA", ["EB-1", "EB-2", "EB-3"], 2)
        
        # Verify result format
        assert "Category Comparison for INDIA" in result
        assert "EB-1" in result
        assert "25.0 days/month" in result
        assert "Fastest Advancing Categories" in result
        assert "Most Consistent Categories" in result
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    @patch('agent.visa_tools.VisaTrendAnalysisTool')
    def test_run_no_data_available(self, mock_trend_tool_class, mock_analyzer_class, mock_repo_class):
        """Test handling when no data is available"""
        mock_repo = Mock()
        mock_analyzer = Mock()
        mock_trend_tool = Mock()
        mock_repo_class.return_value = mock_repo
        mock_analyzer_class.return_value = mock_analyzer
        mock_trend_tool_class.return_value = mock_trend_tool
        
        mock_trend_tool._normalize_country.return_value = CountryCode.CHINA
        
        # Mock empty result
        mock_result = {
            'country': 'CHINA',
            'categories': {},
            'rankings': {'fastest_advancing': [], 'most_stable': [], 'most_volatile': []}
        }
        mock_analyzer.compare_categories.return_value = mock_result
        
        result = self.tool._run("CHINA")
        
        assert "No data available for category comparison in CHINA" in result


class TestVisaMovementPredictionTool:
    """Test the Visa Movement Prediction Tool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = VisaMovementPredictionTool()
    
    def test_tool_metadata(self):
        """Test tool name and description"""
        assert self.tool.name == "visa_movement_prediction"
        assert "predict" in self.tool.description.lower()
        assert "movement" in self.tool.description.lower()
        assert self.tool.args_schema == MovementPredictionInput
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    @patch('agent.visa_tools.VisaTrendAnalysisTool')
    def test_run_successful_prediction(self, mock_trend_tool_class, mock_analyzer_class, mock_repo_class):
        """Test successful movement prediction"""
        # Mock dependencies
        mock_repo = Mock()
        mock_analyzer = Mock()
        mock_trend_tool = Mock()
        mock_repo_class.return_value = mock_repo
        mock_analyzer_class.return_value = mock_analyzer
        mock_trend_tool_class.return_value = mock_trend_tool
        
        mock_trend_tool._normalize_category.return_value = VisaCategory.EB2
        mock_trend_tool._normalize_country.return_value = CountryCode.INDIA
        
        # Mock prediction result
        mock_result = {
            'status': 'success',
            'category': 'EB-2',
            'country': 'INDIA',
            'predictions': [
                {
                    'month': 1,
                    'predicted_advancement': 15,
                    'range_low': 5,
                    'range_high': 25,
                    'confidence': 'moderate'
                },
                {
                    'month': 2,
                    'predicted_advancement': 12,
                    'range_low': 2,
                    'range_high': 22,
                    'confidence': 'moderate'
                }
            ],
            'methodology': 'trend_analysis',
            'confidence': {'confidence': 'moderate', 'score': 75.0},
            'disclaimer': 'Predictions are based on historical trends.'
        }
        mock_analyzer.predict_next_movement.return_value = mock_result
        
        result = self.tool._run("EB-2", "INDIA", 2)
        
        # Verify result format
        assert "Movement Prediction for EB-2 - INDIA" in result
        assert "Prediction Confidence**: Moderate (75%)" in result  # Match the actual format with **
        assert "Month 1: Expected to advance by 15 days" in result
        assert "Month 2: Expected to advance by 12 days" in result
        assert "Disclaimer" in result
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    @patch('agent.visa_tools.VisaTrendAnalysisTool')
    def test_run_prediction_failed(self, mock_trend_tool_class, mock_analyzer_class, mock_repo_class):
        """Test handling of failed prediction"""
        mock_repo = Mock()
        mock_analyzer = Mock()
        mock_trend_tool = Mock()
        mock_repo_class.return_value = mock_repo
        mock_analyzer_class.return_value = mock_analyzer
        mock_trend_tool_class.return_value = mock_trend_tool
        
        mock_trend_tool._normalize_category.return_value = VisaCategory.F1
        mock_trend_tool._normalize_country.return_value = CountryCode.WORLDWIDE
        
        # Mock failed prediction
        mock_result = {
            'status': 'prediction_failed',
            'reason': 'Insufficient data for prediction'
        }
        mock_analyzer.predict_next_movement.return_value = mock_result
        
        result = self.tool._run("F1", "WORLDWIDE", 3)
        
        assert "Prediction failed: Insufficient data for prediction" in result


class TestVisaSummaryReportTool:
    """Test the Visa Summary Report Tool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = VisaSummaryReportTool()
    
    def test_tool_metadata(self):
        """Test tool name and description"""
        assert self.tool.name == "visa_summary_report"
        assert "summary" in self.tool.description.lower()
        assert "comprehensive" in self.tool.description.lower()
        assert self.tool.args_schema == SummaryReportInput
    
    @patch('agent.visa_tools.VisaBulletinRepository')
    @patch('agent.visa_tools.TrendAnalyzer')
    @patch('agent.visa_tools.VisaTrendAnalysisTool')
    def test_run_successful_report(self, mock_trend_tool_class, mock_analyzer_class, mock_repo_class):
        """Test successful summary report generation"""
        # Mock dependencies
        mock_repo = Mock()
        mock_analyzer = Mock()
        mock_trend_tool = Mock()
        mock_repo_class.return_value = mock_repo
        mock_analyzer_class.return_value = mock_analyzer
        mock_trend_tool_class.return_value = mock_trend_tool
        
        mock_trend_tool._normalize_category.side_effect = [VisaCategory.EB1, VisaCategory.EB2]
        mock_trend_tool._normalize_country.side_effect = [CountryCode.INDIA, CountryCode.CHINA]
        
        # Mock report result
        mock_result = {
            'generated_at': '2024-01-15T10:30:00',
            'categories_analyzed': 2,
            'countries_analyzed': 2,
            'category_country_combinations': {
                'EB-1_INDIA': {
                    'category': 'EB-1',
                    'country': 'INDIA',
                    'trend_direction': 'advancing',
                    'average_advancement': 20.0,
                    'volatility': 'low',
                    'data_quality': 'good'
                },
                'EB-2_CHINA': {
                    'category': 'EB-2',
                    'country': 'CHINA',
                    'trend_direction': 'stable',
                    'average_advancement': 5.0,
                    'volatility': 'moderate',
                    'data_quality': 'limited'
                }
            },
            'overall_trends': {
                'most_active_categories': [('EB-1', 15.0), ('EB-2', 8.0)],
                'general_observations': [
                    '1 category-country combinations are advancing',
                    '1 combinations are stable',
                    '0 combinations are retrogressing'
                ]
            }
        }
        mock_analyzer.generate_summary_report.return_value = mock_result
        
        result = self.tool._run(["EB-1", "EB-2"], ["INDIA", "CHINA"])
        
        # Verify result format
        assert "Comprehensive Visa Bulletin Summary Report" in result
        assert "Generated: 2024-01-15T10:30:00" in result
        assert "Categories analyzed: 2" in result
        assert "Countries analyzed: 2" in result
        assert "Market Overview" in result
        assert "Most Active Categories" in result
        assert "Advancing Categories" in result


class TestGetVisaAnalyticsTools:
    """Test the factory function for getting all tools"""
    
    def test_get_all_tools(self):
        """Test that all tools are returned by the factory function"""
        tools = get_visa_analytics_tools()
        
        assert len(tools) == 4
        
        tool_names = [tool.name for tool in tools]
        expected_names = [
            "visa_trend_analysis",
            "visa_category_comparison", 
            "visa_movement_prediction",
            "visa_summary_report"
        ]
        
        for expected_name in expected_names:
            assert expected_name in tool_names
    
    def test_tools_are_properly_initialized(self):
        """Test that all tools are properly initialized"""
        tools = get_visa_analytics_tools()
        
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'args_schema')
            assert hasattr(tool, '_run')
            assert tool.name is not None
            assert tool.description is not None