"""
Tests for visa selector UI component
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

from visa.models import VisaCategory, CountryCode
from ui.components.visa_selector import (
    render_visa_selector,
    render_country_filter,
    render_category_filter
)


class TestVisaSelector:
    """Test cases for visa selector component"""
    
    @patch('streamlit.selectbox')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_render_visa_selector_no_selection(self, mock_markdown, mock_columns, mock_selectbox):
        """Test visa selector with no selection made"""
        # Mock streamlit columns
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Mock selectbox to return no selection
        mock_selectbox.side_effect = ["Select Category Type...", "Select Country..."]
        
        # Mock column context managers
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        
        result = render_visa_selector()
        
        assert result == (None, None)
        assert mock_markdown.called
        assert mock_columns.called
    
    @patch('streamlit.selectbox')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_render_visa_selector_employment_selection(self, mock_markdown, mock_columns, mock_selectbox):
        """Test visa selector with employment-based selection"""
        # Mock streamlit columns
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Mock selectbox returns
        mock_selectbox.side_effect = [
            "Employment-Based",  # Category type
            "EB-2 (Advanced Degree)",  # Specific category
            "India"  # Country
        ]
        
        # Mock column context managers
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        
        result = render_visa_selector()
        
        assert result[0] == VisaCategory.EB2
        assert result[1] == CountryCode.INDIA
    
    @patch('streamlit.selectbox')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_render_visa_selector_family_selection(self, mock_markdown, mock_columns, mock_selectbox):
        """Test visa selector with family-based selection"""
        # Mock streamlit columns
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Mock selectbox returns
        mock_selectbox.side_effect = [
            "Family-Based",  # Category type
            "F1 (Unmarried Adult Children)",  # Specific category
            "China"  # Country
        ]
        
        # Mock column context managers
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        
        result = render_visa_selector()
        
        assert result[0] == VisaCategory.F1
        assert result[1] == CountryCode.CHINA
    
    @patch('streamlit.selectbox')
    @patch('streamlit.markdown')
    def test_render_country_filter(self, mock_markdown, mock_selectbox):
        """Test standalone country filter component"""
        mock_selectbox.return_value = "India"
        
        result = render_country_filter()
        
        assert result == CountryCode.INDIA
        assert mock_markdown.called
        assert mock_selectbox.called
    
    @patch('streamlit.selectbox')
    @patch('streamlit.markdown')
    def test_render_country_filter_worldwide(self, mock_markdown, mock_selectbox):
        """Test country filter with worldwide selection"""
        mock_selectbox.return_value = "All Countries"
        
        result = render_country_filter()
        
        assert result == CountryCode.WORLDWIDE
    
    @patch('streamlit.selectbox')
    @patch('streamlit.markdown')
    def test_render_category_filter(self, mock_markdown, mock_selectbox):
        """Test standalone category filter component"""
        mock_selectbox.return_value = "EB-3"
        
        result = render_category_filter()
        
        assert result == VisaCategory.EB3
        assert mock_markdown.called
        assert mock_selectbox.called
    
    @patch('streamlit.selectbox')
    @patch('streamlit.markdown')
    def test_render_category_filter_all_categories(self, mock_markdown, mock_selectbox):
        """Test category filter with all categories selection"""
        mock_selectbox.return_value = "All Categories"
        
        result = render_category_filter()
        
        assert result is None
    
    def test_category_enum_values(self):
        """Test that category enum contains expected values"""
        expected_categories = ["EB-1", "EB-2", "EB-3", "EB-4", "EB-5", "F1", "F2A", "F2B", "F3", "F4"]
        actual_categories = [cat.value for cat in VisaCategory]
        
        for expected in expected_categories:
            assert expected in actual_categories
    
    def test_country_enum_values(self):
        """Test that country enum contains expected values"""
        expected_countries = ["Worldwide", "China", "India", "Mexico", "Philippines"]
        actual_countries = [country.value for country in CountryCode]
        
        for expected in expected_countries:
            assert expected in actual_countries


class TestVisaSelectorIntegration:
    """Integration tests for visa selector with real Streamlit session state"""
    
    @patch('streamlit.selectbox')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_visa_selector_with_visual_feedback(self, mock_markdown, mock_columns, mock_selectbox):
        """Test that visual feedback is shown when both category and country are selected"""
        # Mock streamlit columns
        mock_col1 = Mock()
        mock_col2 = Mock()
        mock_columns.return_value = [mock_col1, mock_col2]
        
        # Mock selectbox returns for full selection
        mock_selectbox.side_effect = [
            "Employment-Based",
            "EB-1 (Priority Workers)",
            "Philippines"
        ]
        
        # Mock column context managers
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        
        result = render_visa_selector()
        
        # Should return proper selections
        assert result[0] == VisaCategory.EB1
        assert result[1] == CountryCode.PHILIPPINES
        
        # Should have called markdown for visual feedback
        feedback_calls = [call for call in mock_markdown.call_args_list 
                         if any("Selected:" in str(arg) for arg in call[0])]
        assert len(feedback_calls) > 0
    
    def test_invalid_category_handling(self):
        """Test handling of invalid category values"""
        with pytest.raises(ValueError):
            VisaCategory("INVALID_CATEGORY")
    
    def test_invalid_country_handling(self):
        """Test handling of invalid country values"""
        with pytest.raises(ValueError):
            CountryCode("INVALID_COUNTRY")


@pytest.fixture
def mock_streamlit_components():
    """Fixture to mock common Streamlit components"""
    with patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.selectbox') as mock_selectbox, \
         patch('streamlit.columns') as mock_columns:
        
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col, mock_col]
        
        yield {
            'markdown': mock_markdown,
            'selectbox': mock_selectbox,
            'columns': mock_columns,
            'col': mock_col
        }


class TestVisaSelectorWithFixtures:
    """Test visa selector using fixtures"""
    
    def test_render_visa_selector_with_fixtures(self, mock_streamlit_components):
        """Test visa selector using fixtures"""
        mocks = mock_streamlit_components
        
        # Configure mock returns
        mocks['selectbox'].side_effect = [
            "Employment-Based",
            "EB-2 (Advanced Degree)", 
            "India"
        ]
        
        result = render_visa_selector()
        
        assert result[0] == VisaCategory.EB2
        assert result[1] == CountryCode.INDIA
    
    def test_render_filters_with_fixtures(self, mock_streamlit_components):
        """Test individual filter components using fixtures"""
        mocks = mock_streamlit_components
        
        # Test country filter
        mocks['selectbox'].return_value = "China"
        country_result = render_country_filter()
        assert country_result == CountryCode.CHINA
        
        # Test category filter
        mocks['selectbox'].return_value = "EB-5"
        category_result = render_category_filter()
        assert category_result == VisaCategory.EB5