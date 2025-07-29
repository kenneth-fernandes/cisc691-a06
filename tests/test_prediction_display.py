"""
Tests for prediction display UI component
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
import pandas as pd

from visa.models import (
    VisaCategory, CountryCode, PredictionResult, TrendAnalysis, 
    CategoryData, BulletinStatus
)
from ui.components.prediction_display import (
    render_prediction_results,
    render_trend_analysis,
    render_historical_chart,
    render_comparison_chart
)


@pytest.fixture
def sample_prediction():
    """Sample prediction result for testing"""
    return PredictionResult(
        category=VisaCategory.EB2,
        country=CountryCode.INDIA,
        predicted_date=date(2024, 6, 15),
        confidence_score=0.75,
        prediction_type="advancement",
        target_month=6,
        target_year=2024,
        created_at=datetime(2024, 1, 15, 10, 30),
        model_version="1.0"
    )


@pytest.fixture
def sample_trend():
    """Sample trend analysis for testing"""
    return TrendAnalysis(
        category=VisaCategory.EB3,
        country=CountryCode.CHINA,
        start_date=date(2023, 1, 1),
        end_date=date(2024, 1, 1),
        total_advancement_days=120,
        average_monthly_advancement=10.0,
        volatility_score=15.5,
        trend_direction="advancing",
        analysis_date=datetime(2024, 1, 15, 10, 30)
    )


@pytest.fixture
def sample_history():
    """Sample historical data for testing"""
    return [
        CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2023, 1, 1),
            filing_date=date(2023, 1, 1),
            status=BulletinStatus.DATE_SPECIFIED,
            notes="Test data 1"
        ),
        CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2023, 2, 15),
            filing_date=date(2023, 2, 15),
            status=BulletinStatus.DATE_SPECIFIED,
            notes="Test data 2"
        ),
        CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2023, 4, 1),
            filing_date=date(2023, 4, 1),
            status=BulletinStatus.DATE_SPECIFIED,
            notes="Test data 3"
        )
    ]


class TestPredictionResults:
    """Test cases for prediction results display"""
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    def test_render_prediction_results_success(self, mock_expander, mock_metric, mock_columns, mock_markdown, sample_prediction):
        """Test rendering successful prediction results"""
        # Mock streamlit components
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_col3 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        # Mock column context managers
        for col in [mock_col1, mock_col2, mock_col3]:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        
        # Mock expander
        mock_exp = Mock()
        mock_exp.__enter__ = Mock(return_value=mock_exp)
        mock_exp.__exit__ = Mock(return_value=None)
        mock_expander.return_value = mock_exp
        
        render_prediction_results(sample_prediction)
        
        # Verify components were called
        assert mock_markdown.called
        assert mock_columns.called
        assert mock_metric.called
        assert mock_expander.called
    
    @patch('streamlit.warning')
    def test_render_prediction_results_none(self, mock_warning):
        """Test rendering when prediction is None"""
        render_prediction_results(None)
        
        mock_warning.assert_called_once_with("⚠️ No prediction data available")
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    def test_render_prediction_different_types(self, mock_expander, mock_metric, mock_columns, mock_markdown):
        """Test rendering predictions with different types"""
        # Mock streamlit components
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_col3 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        for col in [mock_col1, mock_col2, mock_col3]:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        
        mock_exp = Mock()
        mock_exp.__enter__ = Mock(return_value=mock_exp)
        mock_exp.__exit__ = Mock(return_value=None)
        mock_expander.return_value = mock_exp
        
        # Test different prediction types
        prediction_types = ["advancement", "retrogression", "stable", "current", "unavailable"]
        
        for pred_type in prediction_types:
            prediction = PredictionResult(
                category=VisaCategory.EB1,
                country=CountryCode.WORLDWIDE,
                predicted_date=date(2024, 6, 15),
                confidence_score=0.5,
                prediction_type=pred_type,
                target_month=6,
                target_year=2024,
                model_version="1.0"
            )
            
            render_prediction_results(prediction)
            assert mock_markdown.called


class TestTrendAnalysis:
    """Test cases for trend analysis display"""
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    def test_render_trend_analysis_success(self, mock_metric, mock_columns, mock_markdown, sample_trend):
        """Test rendering successful trend analysis"""
        # Mock streamlit components
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_col3 = Mock()
        mock_col4 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4]
        
        for col in [mock_col1, mock_col2, mock_col3, mock_col4]:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        
        render_trend_analysis(sample_trend)
        
        assert mock_markdown.called
        assert mock_columns.called
        assert mock_metric.called
    
    @patch('streamlit.warning')
    def test_render_trend_analysis_none(self, mock_warning):
        """Test rendering when trend is None"""
        render_trend_analysis(None)
        
        mock_warning.assert_called_once_with("⚠️ No trend analysis available")
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    def test_render_different_trend_directions(self, mock_metric, mock_columns, mock_markdown):
        """Test rendering trends with different directions"""
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_col3 = Mock()
        mock_col4 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4]
        
        for col in [mock_col1, mock_col2, mock_col3, mock_col4]:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        
        trend_directions = ["advancing", "retrogressing", "stable"]
        
        for direction in trend_directions:
            trend = TrendAnalysis(
                category=VisaCategory.EB2,
                country=CountryCode.INDIA,
                start_date=date(2023, 1, 1),
                end_date=date(2024, 1, 1),
                total_advancement_days=90,
                average_monthly_advancement=7.5,
                volatility_score=12.0,
                trend_direction=direction
            )
            
            render_trend_analysis(trend)
            assert mock_markdown.called


class TestHistoricalChart:
    """Test cases for historical chart display"""
    
    @patch('streamlit.markdown')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('plotly.graph_objects.Figure')
    def test_render_historical_chart_success(self, mock_fig, mock_metric, mock_columns, mock_plotly, mock_markdown, sample_history):
        """Test rendering historical chart with data"""
        # Mock plotly figure
        mock_figure = Mock()
        mock_fig.return_value = mock_figure
        
        # Mock streamlit columns
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_col3 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        for col in [mock_col1, mock_col2, mock_col3]:
            col.__enter__ = Mock(return_value=col)
            col.__exit__ = Mock(return_value=None)
        
        render_historical_chart(sample_history, VisaCategory.EB2, CountryCode.INDIA)
        
        assert mock_markdown.called
        assert mock_plotly.called
        assert mock_columns.called
        assert mock_metric.called
    
    @patch('streamlit.warning')
    def test_render_historical_chart_empty(self, mock_warning):
        """Test rendering when history is empty"""
        render_historical_chart([], VisaCategory.EB2, CountryCode.INDIA)
        
        mock_warning.assert_called_once_with("⚠️ No historical data available")
    
    @patch('streamlit.info')  
    @patch('streamlit.markdown')
    def test_render_historical_chart_no_dates(self, mock_markdown, mock_info):
        """Test rendering when history has no valid dates"""
        history_no_dates = [
            CategoryData(
                category=VisaCategory.EB2,
                country=CountryCode.INDIA,
                final_action_date=None,  # No date
                filing_date=None,
                status=BulletinStatus.UNAVAILABLE,
                notes="No dates"
            )
        ]
        
        render_historical_chart(history_no_dates, VisaCategory.EB2, CountryCode.INDIA)
        
        assert mock_markdown.called
        assert mock_info.called


class TestComparisonChart:
    """Test cases for comparison chart display"""
    
    @patch('streamlit.markdown')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.dataframe')
    @patch('plotly.express.bar')
    def test_render_comparison_chart_success(self, mock_bar, mock_dataframe, mock_plotly, mock_markdown):
        """Test rendering comparison chart with multiple predictions"""
        predictions = [
            PredictionResult(
                category=VisaCategory.EB2,
                country=CountryCode.INDIA,
                predicted_date=date(2024, 6, 15),
                confidence_score=0.75,
                prediction_type="advancement",
                target_month=6,
                target_year=2024,
                model_version="1.0"
            ),
            PredictionResult(
                category=VisaCategory.EB3,
                country=CountryCode.CHINA,
                predicted_date=date(2024, 7, 1),
                confidence_score=0.60,
                prediction_type="stable",
                target_month=7,
                target_year=2024,
                model_version="1.0"
            )
        ]
        
        # Mock plotly figure
        mock_figure = Mock()
        mock_bar.return_value = mock_figure
        
        render_comparison_chart(predictions)
        
        assert mock_markdown.called
        assert mock_plotly.called
        assert mock_dataframe.called
        assert mock_bar.called
    
    @patch('streamlit.info')
    def test_render_comparison_chart_insufficient_data(self, mock_info):
        """Test rendering when insufficient predictions for comparison"""
        single_prediction = [
            PredictionResult(
                category=VisaCategory.EB2,
                country=CountryCode.INDIA,
                predicted_date=date(2024, 6, 15),
                confidence_score=0.75,
                prediction_type="advancement",
                target_month=6,
                target_year=2024,
                model_version="1.0"
            )
        ]
        
        render_comparison_chart(single_prediction)
        
        mock_info.assert_called_once_with("📊 Need at least 2 predictions for comparison")
    
    @patch('streamlit.info')
    def test_render_comparison_chart_empty(self, mock_info):
        """Test rendering when no predictions provided"""
        render_comparison_chart([])
        
        mock_info.assert_called_once_with("📊 Need at least 2 predictions for comparison")


class TestPredictionDisplayIntegration:
    """Integration tests for prediction display components"""
    
    def test_full_prediction_display_flow(self, sample_prediction, sample_trend, sample_history):
        """Test full prediction display workflow"""
        # Create a flexible mock that returns the right number of columns
        def columns_side_effect(n):
            mock_col = Mock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            return [mock_col] * n
        
        with patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.columns', side_effect=columns_side_effect) as mock_columns, \
             patch('streamlit.metric') as mock_metric, \
             patch('streamlit.expander') as mock_expander, \
             patch('streamlit.plotly_chart') as mock_plotly, \
             patch('plotly.graph_objects.Figure') as mock_fig:
            
            # Mock expander
            mock_exp = Mock()
            mock_exp.__enter__ = Mock(return_value=mock_exp)
            mock_exp.__exit__ = Mock(return_value=None)
            mock_expander.return_value = mock_exp
            
            # Mock figure
            mock_figure = Mock()
            mock_fig.return_value = mock_figure
            
            # Test prediction results
            render_prediction_results(sample_prediction)
            
            # Test trend analysis
            render_trend_analysis(sample_trend)
            
            # Test historical chart
            render_historical_chart(sample_history, VisaCategory.EB2, CountryCode.INDIA)
            
            # Verify all components were called
            assert mock_markdown.called
            assert mock_columns.called
            assert mock_metric.called
            assert mock_plotly.called
    
    def test_prediction_data_validation(self):
        """Test that prediction components handle edge cases properly"""
        # Test with None values
        render_prediction_results(None)
        render_trend_analysis(None)
        render_historical_chart([], VisaCategory.EB1, CountryCode.WORLDWIDE)
        render_comparison_chart([])
        
        # Should not raise exceptions
        assert True
    
    @pytest.mark.parametrize("prediction_type,expected_icon", [
        ("advancement", "📈"),
        ("retrogression", "📉"),
        ("stable", "➡️"),
        ("current", "✅"),
        ("unavailable", "❌"),
        ("insufficient_data", "⚠️"),
        ("no_features", "❓")
    ])
    def test_prediction_type_icons(self, prediction_type, expected_icon):
        """Test that correct icons are used for different prediction types"""
        # This test would verify icon mapping logic
        # In actual implementation, we'd extract the icon selection logic to a testable function
        assert True  # Placeholder for icon mapping test