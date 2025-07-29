"""
Working tests for visa prediction UI components
"""
import pytest
from unittest.mock import Mock, patch
from datetime import date, datetime

from visa.models import VisaCategory, CountryCode, PredictionResult, CategoryData, BulletinStatus


class TestVisaModels:
    """Test visa model functionality"""
    
    def test_visa_category_values(self):
        """Test VisaCategory enum values"""
        assert VisaCategory.EB1.value == "EB-1"
        assert VisaCategory.EB2.value == "EB-2"
        assert VisaCategory.F1.value == "F1"
    
    def test_country_code_values(self):
        """Test CountryCode enum values"""
        assert CountryCode.INDIA.value == "India"
        assert CountryCode.CHINA.value == "China"
        assert CountryCode.WORLDWIDE.value == "Worldwide"
    
    def test_prediction_result_creation(self):
        """Test creating PredictionResult"""
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
        assert pred.prediction_type == "advancement"


class TestStyleUtilities:
    """Test style utility functions"""
    
    def test_prediction_colors(self):
        """Test prediction color mapping"""
        from ui.components.styles import get_prediction_color
        
        assert get_prediction_color("advancement") == "#28a745"
        assert get_prediction_color("retrogression") == "#dc3545"
        assert get_prediction_color("stable") == "#ffc107"
        assert get_prediction_color("unknown") == "#007bff"
    
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


class TestUIComponents:
    """Test UI component functions"""
    
    def test_visa_selector_import(self):
        """Test visa selector can be imported"""
        from ui.components.visa_selector import render_visa_selector, render_country_filter
        assert callable(render_visa_selector)
        assert callable(render_country_filter)
    
    def test_prediction_display_import(self):
        """Test prediction display can be imported"""
        from ui.components.prediction_display import render_prediction_results
        assert callable(render_prediction_results)
    
    def test_styles_import(self):
        """Test styles can be imported"""
        from ui.components.styles import load_custom_css, get_prediction_color
        assert callable(load_custom_css)
        assert callable(get_prediction_color)


class TestDatabaseFunctions:
    """Test database-related functions"""
    
    @patch('visa.database.VisaDatabase')
    def test_database_connection_function(self, mock_db_class):
        """Test database connection function"""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        from ui.pages.visa_prediction import get_database_connection
        
        result = get_database_connection()
        assert result == mock_db
    
    @patch('ui.pages.visa_prediction.VisaDatabase')
    @patch('streamlit.error')
    def test_database_connection_error(self, mock_error, mock_db_class):
        """Test database connection error handling"""
        mock_db_class.side_effect = Exception("Connection failed")
        
        from ui.pages.visa_prediction import get_database_connection
        
        result = get_database_connection()
        assert result is None
        mock_error.assert_called()
    
    def test_historical_data_function(self):
        """Test historical data function"""
        from ui.pages.visa_prediction import get_historical_data
        
        mock_db = Mock()
        mock_db.get_category_history.return_value = []
        
        result = get_historical_data("EB-2", "India", mock_db)
        assert result == []
        mock_db.get_category_history.assert_called_once()
    
    @patch('streamlit.error')
    def test_historical_data_error(self, mock_error):
        """Test historical data error handling"""
        from ui.pages.visa_prediction import get_historical_data
        
        mock_db = Mock()
        mock_db.get_category_history.side_effect = Exception("DB error")
        
        result = get_historical_data("EB-2", "India", mock_db)
        assert result == []
        mock_error.assert_called()


class TestPredictionGeneration:
    """Test prediction generation"""
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        from ui.pages.visa_prediction import generate_prediction
        
        mock_db = Mock()
        mock_db.get_category_history.return_value = [Mock(), Mock()]  # Only 2 items
        
        result, error = generate_prediction("EB-2", "India", 8, 2024, mock_db)
        
        assert result is None
        assert "Insufficient historical data" in error
    
    @patch('ui.pages.visa_prediction.create_predictor')
    @patch('streamlit.spinner')
    @patch('streamlit.success')
    def test_prediction_generation_success(self, mock_success, mock_spinner, mock_create_pred):
        """Test successful prediction generation"""
        from ui.pages.visa_prediction import generate_prediction
        
        # Mock database with sufficient data
        mock_db = Mock()
        mock_db.get_category_history.return_value = [Mock(), Mock(), Mock()]
        
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
        assert result.category == VisaCategory.EB2


class TestComponentBasics:
    """Test basic component functionality"""
    
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.selectbox')
    def test_visa_selector_basic(self, mock_selectbox, mock_columns, mock_markdown):
        """Test basic visa selector"""
        from ui.components.visa_selector import render_visa_selector
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock(return_value=None)
        mock_columns.return_value = [mock_col, mock_col]
        
        # Mock no selection
        mock_selectbox.side_effect = ["Select Category Type...", "Select Country..."]
        
        result = render_visa_selector()
        assert result == (None, None)
    
    @patch('streamlit.warning')
    def test_prediction_display_none(self, mock_warning):
        """Test prediction display with None input"""
        from ui.components.prediction_display import render_prediction_results
        
        render_prediction_results(None)
        mock_warning.assert_called_with("⚠️ No prediction data available")
    
    @patch('streamlit.markdown')
    def test_css_loading(self, mock_markdown):
        """Test CSS loading"""
        from ui.components.styles import load_custom_css
        
        load_custom_css()
        mock_markdown.assert_called()
        
        # Check that CSS was passed to markdown
        args = mock_markdown.call_args
        assert args is not None
        assert len(args[0]) > 0  # Should have CSS content


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_enum_values(self):
        """Test invalid enum values raise errors"""
        with pytest.raises(ValueError):
            VisaCategory("INVALID")
        
        with pytest.raises(ValueError):
            CountryCode("INVALID")
    
    def test_style_functions_with_invalid_inputs(self):
        """Test style functions handle invalid inputs"""
        from ui.components.styles import get_prediction_color, get_confidence_class
        
        # Should return defaults for invalid inputs
        assert get_prediction_color(None) == "#007bff"
        assert get_prediction_color("") == "#007bff"
        assert get_confidence_class(-1) == "confidence-low"
        assert get_confidence_class(2) == "confidence-high"
    
    def test_status_badge_rendering(self):
        """Test status badge rendering"""
        from ui.components.styles import render_status_badge
        
        # Test various status values
        assert "CURRENT" in render_status_badge("current")
        assert "UNAVAILABLE" in render_status_badge("unavailable")
        assert "DATE" in render_status_badge("other")


class TestDataStructures:
    """Test data structure handling"""
    
    def test_category_data_with_none_dates(self):
        """Test CategoryData with None dates"""
        cat_data = CategoryData(
            category=VisaCategory.EB1,
            country=CountryCode.WORLDWIDE,
            final_action_date=None,
            filing_date=None,
            status=BulletinStatus.UNAVAILABLE
        )
        
        assert cat_data.final_action_date is None
        assert cat_data.filing_date is None
        assert cat_data.status == BulletinStatus.UNAVAILABLE
    
    def test_prediction_result_with_none_date(self):
        """Test PredictionResult with None predicted_date"""
        pred = PredictionResult(
            category=VisaCategory.F1,
            country=CountryCode.MEXICO,
            predicted_date=None,
            confidence_score=0.0,
            prediction_type="insufficient_data",
            target_month=1,
            target_year=2024,
            model_version="1.0"
        )
        
        assert pred.predicted_date is None
        assert pred.confidence_score == 0.0


class TestIntegrationBasics:
    """Test basic integration scenarios"""
    
    def test_enum_string_conversion(self):
        """Test enum to string conversion for UI display"""
        category = VisaCategory.EB3
        country = CountryCode.PHILIPPINES
        
        assert category.value == "EB-3"
        assert country.value == "Philippines"
        
        # Test that these can be used in UI contexts
        display_text = f"{category.value} - {country.value}"
        assert display_text == "EB-3 - Philippines"
    
    def test_confidence_percentage_calculation(self):
        """Test confidence score to percentage conversion"""
        pred = PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 6, 1),
            confidence_score=0.73,
            prediction_type="advancement",
            target_month=6,
            target_year=2024,
            model_version="1.0"
        )
        
        percentage = int(pred.confidence_score * 100)
        assert percentage == 73
    
    def test_prediction_type_formatting(self):
        """Test prediction type formatting for display"""
        pred = PredictionResult(
            category=VisaCategory.F2A,
            country=CountryCode.CHINA,
            predicted_date=date(2024, 9, 1),
            confidence_score=0.6,
            prediction_type="insufficient_data",
            target_month=9,
            target_year=2024,  
            model_version="1.0"
        )
        
        formatted = pred.prediction_type.replace("_", " ").title()
        assert formatted == "Insufficient Data"


class TestModuleStructure:
    """Test module structure and imports"""
    
    def test_component_init_imports(self):
        """Test that __init__.py imports work"""
        from ui.components import (
            render_visa_selector,
            render_prediction_results,
            get_prediction_color
        )
        
        assert callable(render_visa_selector)
        assert callable(render_prediction_results)
        assert callable(get_prediction_color)
    
    def test_page_function_import(self):
        """Test that page functions can be imported"""
        from ui.pages.visa_prediction import (
            get_database_connection,
            get_historical_data,
            generate_prediction,
            render_visa_prediction_page
        )
        
        assert callable(get_database_connection)
        assert callable(get_historical_data)
        assert callable(generate_prediction)
        assert callable(render_visa_prediction_page)
    
    def test_all_visa_models_import(self):
        """Test that all required visa models can be imported"""
        from visa.models import (
            VisaCategory, CountryCode, VisaBulletin, CategoryData,
            PredictionResult, TrendAnalysis, BulletinStatus
        )
        
        # Should all be available
        assert VisaCategory
        assert CountryCode
        assert VisaBulletin
        assert CategoryData
        assert PredictionResult
        assert TrendAnalysis
        assert BulletinStatus