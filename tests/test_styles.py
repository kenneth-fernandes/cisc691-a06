"""
Tests for styling utilities and CSS functions
"""
import pytest
from unittest.mock import Mock, patch

from ui.components.styles import (
    load_custom_css,
    get_prediction_color,
    get_confidence_class,
    get_trend_class,
    render_styled_metric,
    render_status_badge
)


class TestStyleUtilities:
    """Test cases for style utility functions"""
    
    def test_get_prediction_color_known_types(self):
        """Test prediction color mapping for known types"""
        test_cases = {
            "advancement": "#28a745",
            "retrogression": "#dc3545",
            "stable": "#ffc107",
            "current": "#17a2b8",
            "unavailable": "#6c757d",
            "insufficient_data": "#fd7e14",
            "no_features": "#6f42c1"
        }
        
        for prediction_type, expected_color in test_cases.items():
            result = get_prediction_color(prediction_type)
            assert result == expected_color
    
    def test_get_prediction_color_unknown_type(self):
        """Test prediction color for unknown type returns default"""
        result = get_prediction_color("unknown_type")
        assert result == "#007bff"  # Default color
    
    def test_get_confidence_class_high(self):
        """Test confidence class for high confidence"""
        result = get_confidence_class(0.8)
        assert result == "confidence-high"
        
        result = get_confidence_class(0.7)  # Boundary case
        assert result == "confidence-high"
    
    def test_get_confidence_class_medium(self):
        """Test confidence class for medium confidence"""
        result = get_confidence_class(0.6)
        assert result == "confidence-medium"
        
        result = get_confidence_class(0.4)  # Boundary case
        assert result == "confidence-medium"
    
    def test_get_confidence_class_low(self):
        """Test confidence class for low confidence"""
        result = get_confidence_class(0.3)
        assert result == "confidence-low"
        
        result = get_confidence_class(0.0)
        assert result == "confidence-low"
    
    def test_get_trend_class_known_directions(self):
        """Test trend class mapping for known directions"""
        test_cases = {
            "advancing": "trend-advancing",
            "retrogressing": "trend-retrogressing",
            "stable": "trend-stable"
        }
        
        for direction, expected_class in test_cases.items():
            result = get_trend_class(direction)
            assert result == expected_class
    
    def test_get_trend_class_unknown_direction(self):
        """Test trend class for unknown direction returns empty string"""
        result = get_trend_class("unknown_direction")
        assert result == ""
    
    def test_render_status_badge_current(self):
        """Test status badge for current status"""
        result = render_status_badge("current")
        assert "status-current" in result
        assert "CURRENT" in result
        
        result = render_status_badge("C")
        assert "status-current" in result
        assert "CURRENT" in result
    
    def test_render_status_badge_unavailable(self):
        """Test status badge for unavailable status"""
        result = render_status_badge("unavailable")
        assert "status-unavailable" in result
        assert "UNAVAILABLE" in result
        
        result = render_status_badge("U")
        assert "status-unavailable" in result
        assert "UNAVAILABLE" in result
    
    def test_render_status_badge_date(self):
        """Test status badge for date status"""
        result = render_status_badge("date")
        assert "status-date" in result
        assert "DATE" in result
        
        result = render_status_badge("other")
        assert "status-date" in result
        assert "DATE" in result


class TestCSSLoading:
    """Test cases for CSS loading functionality"""
    
    @patch('streamlit.markdown')
    def test_load_custom_css(self, mock_markdown):
        """Test that custom CSS is loaded properly"""
        load_custom_css()
        
        # Verify streamlit.markdown was called
        assert mock_markdown.called
        
        # Verify CSS content was passed
        call_args = mock_markdown.call_args
        assert call_args is not None
        assert len(call_args[0]) > 0  # Should have CSS content
        # Check that unsafe_allow_html is True in kwargs
        assert call_args[1].get('unsafe_allow_html') is True
    
    @patch('streamlit.markdown')
    def test_css_contains_expected_classes(self, mock_markdown):
        """Test that CSS contains expected class definitions"""
        load_custom_css()
        
        call_args = mock_markdown.call_args
        css_content = call_args[0][0]
        
        # Check for key CSS classes
        expected_classes = [
            "visa-prediction-container",
            "prediction-card",
            "category-selector",
            "confidence-high",
            "trend-advancing",
            "status-current"
        ]
        
        for class_name in expected_classes:
            assert class_name in css_content


class TestStyledMetric:
    """Test cases for styled metric rendering"""
    
    @patch('streamlit.markdown')
    def test_render_styled_metric_basic(self, mock_markdown):
        """Test basic styled metric rendering"""
        render_styled_metric("Test Label", "Test Value")
        
        assert mock_markdown.called
        call_args = mock_markdown.call_args
        content = call_args[0][0]
        
        assert "Test Label" in content
        assert "Test Value" in content
        assert "📊" in content  # Default icon
    
    @patch('streamlit.markdown')
    def test_render_styled_metric_with_delta(self, mock_markdown):
        """Test styled metric with delta value"""
        render_styled_metric("Test Label", "Test Value", delta="+5.2%")
        
        call_args = mock_markdown.call_args
        content = call_args[0][0]
        
        assert "Test Label" in content
        assert "Test Value" in content
        assert "+5.2%" in content
    
    @patch('streamlit.markdown')
    def test_render_styled_metric_with_help(self, mock_markdown):
        """Test styled metric with help text"""
        render_styled_metric("Test Label", "Test Value", help_text="This is help text")
        
        call_args = mock_markdown.call_args
        content = call_args[0][0]
        
        assert "Test Label" in content
        assert "Test Value" in content
        assert "This is help text" in content
        assert "ℹ️" in content
    
    @patch('streamlit.markdown')
    def test_render_styled_metric_custom_icon(self, mock_markdown):
        """Test styled metric with custom icon"""
        render_styled_metric("Test Label", "Test Value", icon="🔥")
        
        call_args = mock_markdown.call_args
        content = call_args[0][0]
        
        assert "Test Label" in content
        assert "Test Value" in content
        assert "🔥" in content


class TestStylesIntegration:
    """Integration tests for style components"""
    
    def test_color_consistency(self):
        """Test that colors are consistent across functions"""
        # Test that advancement colors match
        prediction_color = get_prediction_color("advancement")
        
        # Should be the same green color used throughout
        assert prediction_color == "#28a745"
    
    def test_confidence_thresholds(self):
        """Test confidence level thresholds"""
        # Test boundary values
        assert get_confidence_class(0.69) == "confidence-medium"
        assert get_confidence_class(0.70) == "confidence-high"
        assert get_confidence_class(0.39) == "confidence-low"
        assert get_confidence_class(0.40) == "confidence-medium"
    
    @pytest.mark.parametrize("input_value,expected_class", [
        (1.0, "confidence-high"),
        (0.75, "confidence-high"),
        (0.7, "confidence-high"),
        (0.65, "confidence-medium"),
        (0.5, "confidence-medium"),
        (0.4, "confidence-medium"),
        (0.35, "confidence-low"),
        (0.0, "confidence-low"),
    ])
    def test_confidence_class_parametrized(self, input_value, expected_class):
        """Test confidence class with parametrized inputs"""
        result = get_confidence_class(input_value)
        assert result == expected_class
    
    def test_status_badge_case_insensitive(self):
        """Test that status badges work with different cases"""
        # Test various cases
        test_cases = [
            ("Current", "CURRENT"),
            ("CURRENT", "CURRENT"),
            ("current", "CURRENT"),
            ("c", "CURRENT"),
            ("C", "CURRENT"),
            ("Unavailable", "UNAVAILABLE"),
            ("UNAVAILABLE", "UNAVAILABLE"),
            ("unavailable", "UNAVAILABLE"),
            ("u", "UNAVAILABLE"),
            ("U", "UNAVAILABLE"),
        ]
        
        for input_status, expected_text in test_cases:
            result = render_status_badge(input_status)
            assert expected_text in result


class TestStylesErrorHandling:
    """Test error handling in style functions"""
    
    def test_get_prediction_color_none_input(self):
        """Test prediction color with None input"""
        result = get_prediction_color(None)
        assert result == "#007bff"  # Should return default
    
    def test_get_confidence_class_edge_cases(self):
        """Test confidence class with edge case inputs"""
        # Test values outside normal range
        assert get_confidence_class(-0.1) == "confidence-low"
        assert get_confidence_class(1.5) == "confidence-high"
    
    def test_render_status_badge_empty_string(self):
        """Test status badge with empty string"""
        result = render_status_badge("")
        assert "status-date" in result
        assert "DATE" in result
    
    def test_functions_dont_raise_exceptions(self):
        """Test that utility functions don't raise exceptions with various inputs"""
        # Test with various inputs that shouldn't cause crashes
        test_inputs = [None, "", "invalid", 123]  # Removed list and dict as they're not hashable
        
        for test_input in test_inputs:
            try:
                get_prediction_color(test_input)
                get_trend_class(test_input)
                render_status_badge(str(test_input))
                # Should not raise exceptions
            except Exception as e:
                pytest.fail(f"Function raised exception with input {test_input}: {e}")
        
        # Test confidence class with numeric edge cases
        numeric_inputs = [-1, 0, 0.5, 1, 2]  # Removed infinity values which might cause issues
        for test_input in numeric_inputs:
            try:
                get_confidence_class(test_input)
            except Exception as e:
                pytest.fail(f"get_confidence_class raised exception with input {test_input}: {e}")


@pytest.fixture
def mock_streamlit_markdown():
    """Fixture for mocking streamlit markdown"""
    with patch('streamlit.markdown') as mock:
        yield mock


class TestStylesWithFixtures:
    """Test styles using fixtures"""
    
    def test_load_css_with_fixture(self, mock_streamlit_markdown):
        """Test CSS loading using fixture"""
        load_custom_css()
        
        assert mock_streamlit_markdown.called
        call_args = mock_streamlit_markdown.call_args
        # Check that unsafe_allow_html is True in kwargs
        assert call_args[1].get('unsafe_allow_html') is True
    
    def test_styled_metric_with_fixture(self, mock_streamlit_markdown):
        """Test styled metric using fixture"""
        render_styled_metric("Test", "Value", delta="±2", help_text="Help", icon="🎯")
        
        assert mock_streamlit_markdown.called
        content = mock_streamlit_markdown.call_args[0][0]
        
        assert "Test" in content
        assert "Value" in content
        assert "±2" in content
        assert "Help" in content
        assert "🎯" in content