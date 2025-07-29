"""
Basic tests for visa prediction UI components
"""
import pytest
from unittest.mock import Mock, patch
from datetime import date

from visa.models import VisaCategory, CountryCode, PredictionResult, CategoryData, BulletinStatus


class TestVisaModelsIntegration:
    """Test that visa models work with UI components"""
    
    def test_visa_category_enum(self):
        """Test VisaCategory enum values"""
        assert VisaCategory.EB2.value == "EB-2"
        assert VisaCategory.F1.value == "F1"
        
    def test_country_code_enum(self):
        """Test CountryCode enum values"""
        assert CountryCode.INDIA.value == "India"
        assert CountryCode.CHINA.value == "China"
        assert CountryCode.WORLDWIDE.value == "Worldwide"
    
    def test_prediction_result_creation(self):
        """Test PredictionResult can be created"""
        pred = PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 6, 15),
            confidence_score=0.75,
            prediction_type="advancement",
            target_month=6,
            target_year=2024,
            model_version="1.0"
        )
        
        assert pred.category == VisaCategory.EB2
        assert pred.country == CountryCode.INDIA
        assert pred.confidence_score == 0.75
    
    def test_category_data_creation(self):
        """Test CategoryData can be created"""
        cat_data = CategoryData(
            category=VisaCategory.EB3,
            country=CountryCode.CHINA,
            final_action_date=date(2023, 1, 1),
            filing_date=date(2023, 1, 1),
            status=BulletinStatus.DATE_SPECIFIED
        )
        
        assert cat_data.category == VisaCategory.EB3
        assert cat_data.country == CountryCode.CHINA
        assert cat_data.status == BulletinStatus.DATE_SPECIFIED


class TestUIComponentImports:
    """Test that UI components can be imported"""
    
    def test_visa_selector_import(self):
        """Test that visa selector can be imported"""
        from ui.components.visa_selector import render_visa_selector
        assert callable(render_visa_selector)
    
    def test_prediction_display_import(self):
        """Test that prediction display can be imported"""
        from ui.components.prediction_display import render_prediction_results
        assert callable(render_prediction_results)
    
    def test_styles_import(self):
        """Test that styles can be imported"""
        from ui.components.styles import get_prediction_color, get_confidence_class
        assert callable(get_prediction_color)
        assert callable(get_confidence_class)
    
    def test_visa_prediction_page_import(self):
        """Test that visa prediction page can be imported"""
        from ui.pages.visa_prediction import render_visa_prediction_page
        assert callable(render_visa_prediction_page)


class TestStyleUtilities:
    """Test style utility functions"""
    
    def test_prediction_colors(self):
        """Test prediction color mapping"""
        from ui.components.styles import get_prediction_color
        
        assert get_prediction_color("advancement") == "#28a745"
        assert get_prediction_color("retrogression") == "#dc3545"
        assert get_prediction_color("stable") == "#ffc107"
        assert get_prediction_color("unknown") == "#007bff"  # Default
    
    def test_confidence_classes(self):
        """Test confidence class mapping"""
        from ui.components.styles import get_confidence_class
        
        assert get_confidence_class(0.8) == "confidence-high"
        assert get_confidence_class(0.5) == "confidence-medium"
        assert get_confidence_class(0.2) == "confidence-low"
    
    def test_trend_classes(self):
        """Test trend class mapping"""
        from ui.components.styles import get_trend_class
        
        assert get_trend_class("advancing") == "trend-advancing"
        assert get_trend_class("retrogressing") == "trend-retrogressing"
        assert get_trend_class("stable") == "trend-stable"
        assert get_trend_class("unknown") == ""


class TestDatabaseIntegration:
    """Test basic database integration"""
    
    @patch('visa.database.VisaDatabase')
    def test_database_can_be_created(self, mock_db_class):
        """Test that database can be instantiated"""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        from ui.pages.visa_prediction import get_database_connection
        
        result = get_database_connection()
        assert result is not None
    
    @patch('ui.pages.visa_prediction.VisaDatabase')
    @patch('streamlit.error')
    def test_database_error_handling(self, mock_error, mock_db_class):
        """Test database error handling"""
        mock_db_class.side_effect = Exception("Database error")
        
        from ui.pages.visa_prediction import get_database_connection
        
        result = get_database_connection()
        assert result is None
        mock_error.assert_called()


class TestFunctionIntegration:
    """Test function integration without streamlit caching"""
    
    def test_historical_data_function(self):
        """Test historical data function structure"""
        from ui.pages.visa_prediction import get_historical_data
        
        mock_db = Mock()
        mock_db.get_category_history.return_value = []
        
        result = get_historical_data("EB-2", "India", mock_db)
        assert result == []
        mock_db.get_category_history.assert_called()
    
    @patch('streamlit.error')
    def test_historical_data_error(self, mock_error):
        """Test historical data error handling"""
        from ui.pages.visa_prediction import get_historical_data
        
        mock_db = Mock()
        mock_db.get_category_history.side_effect = Exception("Database error")
        
        result = get_historical_data("EB-2", "India", mock_db)
        assert result == []
        mock_error.assert_called()
    
    @patch('ui.pages.visa_prediction.create_predictor')
    @patch('streamlit.spinner')
    @patch('streamlit.success')
    def test_prediction_generation_structure(self, mock_success, mock_spinner, mock_create_pred):
        """Test prediction generation function structure"""
        from ui.pages.visa_prediction import generate_prediction
        
        # Mock database with sufficient data
        mock_db = Mock()
        mock_db.get_category_history.return_value = [Mock(), Mock(), Mock()]  # 3 items
        
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.train.return_value = {'test_mae': 5.0}
        mock_prediction = PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 8, 15),
            confidence_score=0.75,
            prediction_type="advancement",
            target_month=8,
            target_year=2024,
            model_version="1.0"
        )
        mock_predictor.predict.return_value = mock_prediction
        mock_create_pred.return_value = mock_predictor
        
        # Mock spinner
        mock_spinner_ctx = Mock()
        mock_spinner_ctx.__enter__ = Mock()
        mock_spinner_ctx.__exit__ = Mock()
        mock_spinner.return_value = mock_spinner_ctx
        
        result, error = generate_prediction("EB-2", "India", 8, 2024, mock_db)
        
        assert result is not None
        assert error is None
    
    def test_prediction_insufficient_data(self):
        """Test prediction with insufficient data"""
        from ui.pages.visa_prediction import generate_prediction
        
        mock_db = Mock()
        mock_db.get_category_history.return_value = [Mock(), Mock()]  # Only 2 items
        
        result, error = generate_prediction("EB-2", "India", 8, 2024, mock_db)
        
        assert result is None
        assert "Insufficient historical data" in error


class TestComponentInitialization:
    """Test that components can be initialized"""
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.selectbox')
    def test_visa_selector_basic(self, mock_selectbox, mock_columns, mock_markdown):
        """Test basic visa selector functionality"""
        from ui.components.visa_selector import render_visa_selector
        
        # Mock column objects
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col, mock_col]
        
        # Mock selectbox returns
        mock_selectbox.side_effect = ["Select Category Type...", "Select Country..."]
        
        result = render_visa_selector()
        assert result == (None, None)
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    def test_prediction_display_basic(self, mock_expander, mock_metric, mock_columns, mock_markdown):
        """Test basic prediction display functionality"""
        from ui.components.prediction_display import render_prediction_results
        
        # Mock components
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        mock_exp = Mock()
        mock_exp.__enter__ = Mock(return_value=mock_exp)
        mock_exp.__exit__ = Mock(return_value=None)
        mock_expander.return_value = mock_exp
        
        # Test with None (should show warning)
        render_prediction_results(None)
        # Should not raise exception
    
    @patch('streamlit.markdown')
    def test_styles_css_loading(self, mock_markdown):
        """Test CSS loading"""
        from ui.components.styles import load_custom_css
        
        load_custom_css()
        mock_markdown.assert_called()


class TestErrorHandling:
    """Test error handling in various scenarios"""
    
    def test_invalid_enum_values(self):
        """Test handling of invalid enum values"""
        with pytest.raises(ValueError):
            VisaCategory("INVALID_CATEGORY")
        
        with pytest.raises(ValueError):
            CountryCode("INVALID_COUNTRY")
    
    def test_prediction_result_validation(self):
        """Test prediction result validation"""
        # Should work with valid data
        pred = PredictionResult(
            category=VisaCategory.EB1,
            country=CountryCode.WORLDWIDE,
            predicted_date=None,  # Can be None
            confidence_score=0.5,
            prediction_type="insufficient_data",
            target_month=1,
            target_year=2024,
            model_version="1.0"
        )
        
        assert pred.predicted_date is None
        assert pred.confidence_score == 0.5
    
    def test_function_with_none_inputs(self):
        """Test functions handle None inputs gracefully"""
        from ui.components.styles import get_prediction_color, get_confidence_class
        
        # Should return defaults for None/invalid inputs
        assert get_prediction_color(None) == "#007bff"
        assert get_confidence_class(-1) == "confidence-low"  # Clamps to valid range


class TestIntegrationBasics:
    """Test basic integration scenarios"""
    
    def test_enum_to_string_conversion(self):
        """Test enum to string conversion for UI"""
        category = VisaCategory.EB2
        country = CountryCode.INDIA
        
        assert category.value == "EB-2"
        assert country.value == "India"
    
    def test_prediction_display_data_structure(self):
        """Test that prediction data can be structured for display"""
        pred = PredictionResult(
            category=VisaCategory.F1,
            country=CountryCode.MEXICO,
            predicted_date=date(2024, 12, 1),
            confidence_score=0.65,
            prediction_type="stable",
            target_month=12,
            target_year=2024,
            model_version="1.0"
        )
        
        # Should be able to extract display information
        assert pred.category.value == "F1"
        assert pred.country.value == "Mexico"
        assert pred.confidence_score * 100 == 65.0  # Percentage
        assert pred.prediction_type.replace("_", " ").title() == "Stable"
    
    def test_component_module_structure(self):
        """Test that component modules are structured correctly"""
        # Test __init__.py imports
        from ui.components import (
            render_visa_selector, 
            render_prediction_results,
            get_prediction_color
        )
        
        assert callable(render_visa_selector)
        assert callable(render_prediction_results)
        assert callable(get_prediction_color)