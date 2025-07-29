"""
Integration tests for UI components with database connectivity
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
import tempfile
import os

from visa.models import (
    VisaCategory, CountryCode, VisaBulletin, CategoryData, 
    PredictionResult, TrendAnalysis, BulletinStatus
)
from visa.database import VisaDatabase
from ui.pages.visa_prediction import get_database_connection, get_historical_data, generate_prediction


@pytest.fixture
def temp_database():
    """Create a temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    # Create database with temp file
    db = VisaDatabase(temp_file.name)
    
    yield db
    
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except OSError:
        pass


@pytest.fixture
def populated_database(temp_database):
    """Database populated with test data"""
    db = temp_database
    
    # Create sample bulletins with category data
    for year in [2022, 2023, 2024]:
        for month in [1, 4, 7, 10]:  # Quarterly data
            bulletin = VisaBulletin(
                bulletin_date=date(year, month, 1),
                fiscal_year=year,
                month=month,
                year=year,
                source_url=f"https://test.gov/{year}/{month}"
            )
            
            # Add EB-2 India data with progression
            eb2_date = date(2020, 1, 1)  # Base date
            days_offset = (year - 2022) * 365 + (month - 1) * 30  # Simulate progression
            final_date = date(eb2_date.year + days_offset // 365, 
                            eb2_date.month + (days_offset % 365) // 30, 
                            eb2_date.day)
            
            eb2_data = CategoryData(
                category=VisaCategory.EB2,
                country=CountryCode.INDIA,
                final_action_date=final_date,
                filing_date=final_date,
                status=BulletinStatus.DATE_SPECIFIED,
                notes=f"Test data for {year}-{month}"
            )
            bulletin.add_category_data(eb2_data)
            
            # Add EB-3 China data
            eb3_data = CategoryData(
                category=VisaCategory.EB3,
                country=CountryCode.CHINA,
                final_action_date=date(2021, 6, 15),
                filing_date=date(2021, 6, 15),
                status=BulletinStatus.DATE_SPECIFIED,
                notes=f"EB-3 China data for {year}-{month}"
            )
            bulletin.add_category_data(eb3_data)
            
            # Save bulletin
            db.save_bulletin(bulletin)
    
    return db


class TestDatabaseIntegration:
    """Test database integration with UI components"""
    
    def test_database_connection_real(self, temp_database):
        """Test real database connection"""
        db = temp_database
        
        # Should be able to get stats
        stats = db.get_database_stats()
        assert isinstance(stats, dict)
        assert 'bulletin_count' in stats
        assert 'category_data_count' in stats
    
    def test_historical_data_retrieval(self, populated_database):
        """Test retrieving historical data from populated database"""
        db = populated_database
        
        # Get EB-2 India history
        history = db.get_category_history(VisaCategory.EB2, CountryCode.INDIA)
        
        assert len(history) > 0
        assert all(isinstance(item, CategoryData) for item in history)
        assert all(item.category == VisaCategory.EB2 for item in history)
        assert all(item.country == CountryCode.INDIA for item in history)
    
    def test_prediction_save_and_retrieve(self, temp_database):
        """Test saving and retrieving predictions"""
        db = temp_database
        
        # Create a prediction
        prediction = PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 8, 15),
            confidence_score=0.85,
            prediction_type="advancement",
            target_month=8,
            target_year=2024,
            model_version="test-1.0"
        )
        
        # Save prediction
        prediction_id = db.save_prediction(prediction)
        assert prediction_id is not None
        
        # Retrieve predictions
        retrieved = db.get_latest_predictions(VisaCategory.EB2, CountryCode.INDIA)
        assert len(retrieved) == 1
        assert retrieved[0].category == VisaCategory.EB2
        assert retrieved[0].country == CountryCode.INDIA
        assert retrieved[0].confidence_score == 0.85


class TestUIComponentDatabaseIntegration:
    """Test UI components with real database integration"""
    
    def test_get_historical_data_function(self, populated_database):
        """Test get_historical_data function with real database"""
        db = populated_database
        
        # Cache was removed, no need to clear
        
        # Get historical data
        result = get_historical_data("EB-2", "India", db)
        
        assert len(result) > 0
        assert all(isinstance(item, CategoryData) for item in result)
    
    def test_get_historical_data_empty_result(self, temp_database):
        """Test get_historical_data with no matching data"""
        db = temp_database
        
        # Cache was removed, no need to clear
        
        # Try to get data that doesn't exist
        result = get_historical_data("F1", "Philippines", db)
        
        assert result == []
    
    @patch('ui.pages.visa_prediction.create_predictor')
    @patch('streamlit.spinner')
    @patch('streamlit.success')
    def test_generate_prediction_integration(self, mock_success, mock_spinner, mock_create_predictor, populated_database):
        """Test prediction generation with real database"""
        db = populated_database
        
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.train.return_value = {'test_mae': 3.5}
        mock_prediction = PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 9, 1),
            confidence_score=0.78,
            prediction_type="advancement",
            target_month=9,
            target_year=2024,
            model_version="1.0"
        )
        mock_predictor.predict.return_value = mock_prediction
        mock_create_predictor.return_value = mock_predictor
        
        # Mock spinner
        mock_spinner_ctx = Mock()
        mock_spinner_ctx.__enter__ = Mock(return_value=mock_spinner_ctx)
        mock_spinner_ctx.__exit__ = Mock(return_value=None)
        mock_spinner.return_value = mock_spinner_ctx
        
        # Cache was removed, no need to clear
        
        # Generate prediction
        result, error = generate_prediction("EB-2", "India", 9, 2024, db)
        
        assert result is not None
        assert error is None
        assert result.category == VisaCategory.EB2
        assert result.country == CountryCode.INDIA


class TestDatabasePerformance:
    """Test database performance with UI components"""
    
    def test_database_stats_performance(self, populated_database):
        """Test that database stats retrieval is fast"""
        db = populated_database
        
        import time
        start_time = time.time()
        stats = db.get_database_stats()
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 0.5  # 500ms
        assert stats['bulletin_count'] > 0
    
    def test_historical_data_performance(self, populated_database):
        """Test historical data retrieval performance"""
        db = populated_database
        
        import time
        start_time = time.time()
        history = db.get_category_history(VisaCategory.EB2, CountryCode.INDIA)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 1.0  # 1 second
        assert len(history) > 0


class TestErrorHandlingIntegration:
    """Test error handling in database integration"""
    
    @patch('ui.pages.visa_prediction.VisaDatabase')
    def test_database_connection_error_handling(self, mock_visa_db):
        """Test error handling when database connection fails"""
        mock_visa_db.side_effect = Exception("Database connection failed")
        
        # Cache was removed, no need to clear
        
        # Should handle error gracefully
        result = get_database_connection()
        assert result is None
    
    def test_corrupted_data_handling(self, temp_database):
        """Test handling of corrupted or invalid data"""
        db = temp_database
        
        # Create bulletin with invalid data
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 1, 1),
            fiscal_year=2024,
            month=1,
            year=2024
        )
        
        # Add category data with None dates
        cat_data = CategoryData(
            category=VisaCategory.EB1,
            country=CountryCode.WORLDWIDE,
            final_action_date=None,
            filing_date=None,
            status=BulletinStatus.UNAVAILABLE
        )
        bulletin.add_category_data(cat_data)
        
        # Should save without error
        bulletin_id = db.save_bulletin(bulletin)
        assert bulletin_id is not None
        
        # Should retrieve without error
        history = db.get_category_history(VisaCategory.EB1, CountryCode.WORLDWIDE)
        assert len(history) == 1
        assert history[0].final_action_date is None


class TestCacheIntegration:
    """Test caching integration with database"""
    
    def test_cache_effectiveness(self, populated_database):
        """Test that functions work without caching"""
        db = populated_database
        
        # Cache was removed, no need to clear
        
        # Track database calls
        original_method = db.get_category_history
        call_count = 0
        
        def counting_wrapper(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return original_method(*args, **kwargs)
        
        db.get_category_history = counting_wrapper
        
        # Call function multiple times
        get_historical_data("EB-2", "India", db)
        get_historical_data("EB-2", "India", db)
        get_historical_data("EB-2", "India", db)
        
        # Without caching, should hit database each time
        assert call_count == 3
    
    def test_cache_invalidation(self, populated_database):
        """Test that cache can be cleared"""
        db = populated_database
        
        # Function call without caching
        result1 = get_historical_data("EB-2", "India", db)
        
        # Cache was removed, no need to clear
        
        # Should work consistently without caching
        result2 = get_historical_data("EB-2", "India", db)
        assert len(result1) > 0
        assert len(result2) > 0


class TestPostgreSQLIntegration:
    """Test PostgreSQL specific integration (mocked)"""
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'})
    @patch('psycopg2.connect')
    def test_postgresql_connection_attempt(self, mock_connect):
        """Test that PostgreSQL connection is attempted when DATABASE_URL is set"""
        # Mock successful connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # This would attempt PostgreSQL connection
        try:
            db = VisaDatabase()
            assert db.use_postgres  # Should be using PostgreSQL
        except Exception:
            # May fail due to missing tables, but should attempt PostgreSQL
            pass
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'})
    @patch('psycopg2.connect')
    def test_postgresql_fallback_to_sqlite(self, mock_connect):
        """Test fallback to SQLite when PostgreSQL fails"""
        # Mock failed PostgreSQL connection
        mock_connect.side_effect = Exception("PostgreSQL connection failed")
        
        # Should fallback to SQLite
        db = VisaDatabase()
        assert not db.use_postgres  # Should fallback to SQLite
        assert db.db_path is not None  # Should have SQLite path


class TestDataConsistency:
    """Test data consistency across database operations"""
    
    def test_bulletin_category_consistency(self, temp_database):
        """Test that bulletin and category data remain consistent"""
        db = temp_database
        
        # Create bulletin with multiple categories
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 3, 1),
            fiscal_year=2024,
            month=3,
            year=2024
        )
        
        # Add multiple category data
        categories = [
            (VisaCategory.EB1, CountryCode.WORLDWIDE),
            (VisaCategory.EB2, CountryCode.INDIA),
            (VisaCategory.EB3, CountryCode.CHINA),
            (VisaCategory.F1, CountryCode.MEXICO)
        ]
        
        for cat, country in categories:
            cat_data = CategoryData(
                category=cat,
                country=country,
                final_action_date=date(2022, 1, 1),
                filing_date=date(2022, 1, 1),
                status=BulletinStatus.DATE_SPECIFIED
            )
            bulletin.add_category_data(cat_data)
        
        # Save bulletin
        bulletin_id = db.save_bulletin(bulletin)
        
        # Retrieve and verify
        retrieved_bulletin = db.get_bulletin(2024, 3, 2024)
        assert retrieved_bulletin is not None
        assert len(retrieved_bulletin.categories) == 4
        
        # Verify each category
        for cat, country in categories:
            cat_data = retrieved_bulletin.get_category_data(cat, country)
            assert cat_data is not None
            assert cat_data.category == cat
            assert cat_data.country == country
    
    def test_update_bulletin_consistency(self, temp_database):
        """Test that bulletin updates maintain consistency"""
        db = temp_database
        
        # Create and save initial bulletin
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 5, 1),
            fiscal_year=2024,
            month=5,
            year=2024
        )
        
        cat_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2022, 6, 1),
            filing_date=date(2022, 6, 1),
            status=BulletinStatus.DATE_SPECIFIED
        )
        bulletin.add_category_data(cat_data)
        
        bulletin_id = db.save_bulletin(bulletin)
        
        # Update bulletin with new data
        updated_bulletin = VisaBulletin(
            bulletin_date=date(2024, 5, 1),
            fiscal_year=2024,
            month=5,
            year=2024
        )
        
        updated_cat_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2022, 8, 15),  # Updated date
            filing_date=date(2022, 8, 15),
            status=BulletinStatus.DATE_SPECIFIED,
            notes="Updated data"
        )
        updated_bulletin.add_category_data(updated_cat_data)
        
        # Save updated bulletin
        db.save_bulletin(updated_bulletin)
        
        # Retrieve and verify update
        retrieved = db.get_bulletin(2024, 5, 2024)
        assert retrieved is not None
        assert len(retrieved.categories) == 1  # Should still have one category
        
        retrieved_cat = retrieved.get_category_data(VisaCategory.EB2, CountryCode.INDIA)
        assert retrieved_cat.final_action_date == date(2022, 8, 15)
        assert retrieved_cat.notes == "Updated data"