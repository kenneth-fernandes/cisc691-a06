"""
Unit tests for visa database functionality (multi-database architecture)
"""
import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from contextlib import contextmanager

from visa.database import VisaDatabase
from visa.models import VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus, PredictionResult, TrendAnalysis
from visa.config import VisaConfig


class TestVisaDatabase:
    """Test VisaDatabase multi-database manager"""
    
    def _create_test_db(self, db_path=None):
        """Helper method to create a test database with tables"""
        # Use a temporary file instead of :memory: to avoid connection isolation issues
        import tempfile
        import os
        if db_path is None:
            # Create a temporary file for the database
            fd, db_path = tempfile.mkstemp(suffix='.db')
            os.close(fd)  # Close the file descriptor, we just need the path
            
        # Create the database - tables will be created in __init__
        db = VisaDatabase(db_path=db_path)
        
        # Store the path so we can clean up later if needed
        db._temp_path = db_path if db_path != ":memory:" else None
        return db
    
    @pytest.fixture
    def sample_bulletin(self):
        """Sample bulletin for testing"""
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024,
            source_url="https://example.com"
        )
        
        # Add sample category data
        cat_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2022, 1, 15),
            filing_date=date(2022, 6, 1),
            status=BulletinStatus.DATE_SPECIFIED,
            notes="Test category"
        )
        bulletin.add_category_data(cat_data)
        
        return bulletin
    
    @pytest.fixture
    def sample_prediction(self):
        """Sample prediction result for testing"""
        return PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 8, 15),
            confidence_score=0.75,
            prediction_type="advancement",
            target_month=8,
            target_year=2024,
            created_at=datetime.now(),
            model_version="v1.0"
        )
    
    def test_initialization_sqlite_default(self):
        """Test initialization defaults to SQLite"""
        with patch.dict('os.environ', {}, clear=True):
            db = VisaDatabase()
            assert db.use_postgres is False
            assert db.db_path is not None
            assert 'visa_bulletins.db' in db.db_path
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaDatabase._create_tables')
    @patch('psycopg2.connect')
    def test_initialization_postgresql(self, mock_connect, mock_create_tables):
        """Test initialization with PostgreSQL"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://user:pass@localhost/db'}):
            db = VisaDatabase()
            assert db.use_postgres is True
            assert db.db_path is None
            mock_create_tables.assert_called_once()
    
    def test_initialization_postgresql_not_available(self):
        """Test initialization when PostgreSQL not available"""
        with patch('visa.database.POSTGRES_AVAILABLE', False):
            with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://user:pass@localhost/db'}):
                db = VisaDatabase()
                assert db.use_postgres is False  # Should fallback to SQLite
    
    @patch('visa.database.VisaDatabase._create_tables')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_ensure_directory_exists(self, mock_exists, mock_makedirs, mock_create_tables):
        """Test directory creation for SQLite database"""
        mock_exists.return_value = False
        
        db = VisaDatabase(db_path="/test/path/database.db")
        
        mock_makedirs.assert_called_once_with('/test/path', exist_ok=True)
        mock_create_tables.assert_called_once()
    
    def test_get_param_placeholder_sqlite(self):
        """Test parameter placeholder for SQLite"""
        with patch.dict('os.environ', {}, clear=True):
            db = VisaDatabase()
            assert db._get_param_placeholder() == "?"
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaDatabase._create_tables')
    @patch('psycopg2.connect')
    def test_get_param_placeholder_postgresql(self, mock_connect, mock_create_tables):
        """Test parameter placeholder for PostgreSQL"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://user:pass@localhost/db'}):
            db = VisaDatabase()
            assert db._get_param_placeholder() == "%s"
            mock_create_tables.assert_called_once()
    
    def test_get_connection_sqlite(self):
        """Test SQLite connection context manager"""
        db = self._create_test_db()
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    @patch('psycopg2.connect')
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    def test_get_connection_postgresql(self, mock_connect):
        """Test PostgreSQL connection context manager"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://user:pass@localhost/db'}):
            db = VisaDatabase()
            
            with db.get_connection() as conn:
                assert conn == mock_conn
                assert conn.autocommit is False
    
    def test_create_tables_sqlite(self):
        """Test table creation for SQLite"""
        # Use the helper to create a test database with tables
        db = self._create_test_db()
        
        # Tables should be created during initialization
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check visa_bulletins table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='visa_bulletins'")
            assert cursor.fetchone() is not None
            
            # Check category_data table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category_data'")
            assert cursor.fetchone() is not None
            
            # Check predictions table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
            assert cursor.fetchone() is not None
            
            # Check trend_analysis table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trend_analysis'")
            assert cursor.fetchone() is not None
    
    @patch('psycopg2.connect')
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    def test_create_tables_postgresql(self, mock_connect):
        """Test table creation for PostgreSQL"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://user:pass@localhost/db'}):
            db = VisaDatabase()
            
            # Verify PostgreSQL-specific table creation was attempted
            calls = mock_cursor.execute.call_args_list
            
            # Should have created tables with PostgreSQL syntax
            table_creation_calls = [call for call in calls if 'CREATE TABLE' in str(call)]
            assert len(table_creation_calls) >= 4  # At least 4 tables
            
            # Check for PostgreSQL-specific syntax
            postgres_calls = [call for call in calls if 'SERIAL PRIMARY KEY' in str(call)]
            assert len(postgres_calls) > 0
    
    def test_save_bulletin_sqlite(self, sample_bulletin):
        """Test saving bulletin in SQLite"""
        db = self._create_test_db()
        
        bulletin_id = db.save_bulletin(sample_bulletin)
        
        assert bulletin_id is not None
        assert isinstance(bulletin_id, int)
        
        # Verify bulletin was saved
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM visa_bulletins")
            count = cursor.fetchone()[0]
            assert count == 1
            
            cursor.execute("SELECT COUNT(*) FROM category_data")
            count = cursor.fetchone()[0]
            assert count == 1  # One category data entry
    
    def test_save_bulletin_update_existing(self, sample_bulletin):
        """Test updating existing bulletin"""
        db = self._create_test_db()
        
        # Save initial bulletin
        bulletin_id1 = db.save_bulletin(sample_bulletin)
        
        # Save same bulletin again (should update)
        bulletin_id2 = db.save_bulletin(sample_bulletin)
        
        assert bulletin_id1 == bulletin_id2
        
        # Should still have only one bulletin
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM visa_bulletins")
            count = cursor.fetchone()[0]
            assert count == 1
    
    def test_get_bulletin(self, sample_bulletin):
        """Test retrieving bulletin"""
        db = self._create_test_db()
        
        # Save bulletin
        db.save_bulletin(sample_bulletin)
        
        # Retrieve bulletin
        retrieved = db.get_bulletin(
            sample_bulletin.fiscal_year,
            sample_bulletin.month,
            sample_bulletin.year
        )
        
        assert retrieved is not None
        assert retrieved.fiscal_year == sample_bulletin.fiscal_year
        assert retrieved.month == sample_bulletin.month
        assert retrieved.year == sample_bulletin.year
        assert retrieved.bulletin_date == sample_bulletin.bulletin_date
        assert len(retrieved.categories) == 1
    
    def test_get_bulletin_not_found(self):
        """Test retrieving non-existent bulletin"""
        db = self._create_test_db()
        
        retrieved = db.get_bulletin(2024, 12, 2024)
        assert retrieved is None
    
    def test_get_bulletins_range(self, sample_bulletin):
        """Test retrieving bulletins by year range"""
        db = self._create_test_db()
        
        # Save bulletin
        db.save_bulletin(sample_bulletin)
        
        # Create another bulletin for different year
        bulletin2 = VisaBulletin(
            bulletin_date=date(2023, 6, 1),
            fiscal_year=2023,
            month=6,
            year=2023,
            source_url="https://example.com/2023"
        )
        db.save_bulletin(bulletin2)
        
        # Get range
        bulletins = db.get_bulletins_range(2023, 2024)
        
        assert len(bulletins) == 2
        years = [b.year for b in bulletins]
        assert 2023 in years
        assert 2024 in years
    
    def test_get_category_history(self, sample_bulletin):
        """Test retrieving category history"""
        db = self._create_test_db()
        
        # Save bulletin
        db.save_bulletin(sample_bulletin)
        
        # Get history
        history = db.get_category_history(
            VisaCategory.EB2,
            CountryCode.INDIA,
            start_year=2024,
            end_year=2024
        )
        
        assert len(history) == 1
        assert history[0].category == VisaCategory.EB2
        assert history[0].country == CountryCode.INDIA
        assert history[0].final_action_date == date(2022, 1, 15)
    
    def test_save_prediction(self, sample_prediction):
        """Test saving prediction result"""
        db = self._create_test_db()
        
        prediction_id = db.save_prediction(sample_prediction)
        
        assert prediction_id is not None
        assert isinstance(prediction_id, int)
        
        # Verify prediction was saved
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            count = cursor.fetchone()[0]
            assert count == 1
    
    def test_get_latest_predictions(self, sample_prediction):
        """Test retrieving latest predictions"""
        db = self._create_test_db()
        
        # Save prediction
        db.save_prediction(sample_prediction)
        
        # Get all predictions
        predictions = db.get_latest_predictions()
        assert len(predictions) == 1
        assert predictions[0].category == VisaCategory.EB2
        assert predictions[0].country == CountryCode.INDIA
        
        # Get filtered predictions
        filtered = db.get_latest_predictions(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA
        )
        assert len(filtered) == 1
        
        # Get non-matching filter
        no_match = db.get_latest_predictions(
            category=VisaCategory.EB1,
            country=CountryCode.CHINA
        )
        assert len(no_match) == 0
    
    def test_delete_bulletin(self, sample_bulletin):
        """Test deleting bulletin"""
        db = self._create_test_db()
        
        # Save bulletin
        db.save_bulletin(sample_bulletin)
        
        # Verify it exists
        retrieved = db.get_bulletin(sample_bulletin.fiscal_year, sample_bulletin.month, sample_bulletin.year)
        assert retrieved is not None
        
        # Delete bulletin
        result = db.delete_bulletin(sample_bulletin.fiscal_year, sample_bulletin.month, sample_bulletin.year)
        assert result is True
        
        # Verify it's deleted
        retrieved = db.get_bulletin(sample_bulletin.fiscal_year, sample_bulletin.month, sample_bulletin.year)
        assert retrieved is None
        
        # Verify category data is also deleted (cascade)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM category_data")
            count = cursor.fetchone()[0]
            assert count == 0
    
    def test_delete_bulletin_not_found(self):
        """Test deleting non-existent bulletin"""
        db = self._create_test_db()
        
        result = db.delete_bulletin(2024, 12, 2024)
        assert result is False
    
    def test_get_database_stats(self, sample_bulletin, sample_prediction):
        """Test database statistics"""
        db = self._create_test_db()
        
        # Add some data
        db.save_bulletin(sample_bulletin)
        db.save_prediction(sample_prediction)
        
        stats = db.get_database_stats()
        
        assert 'bulletin_count' in stats
        assert 'category_data_count' in stats
        assert 'prediction_count' in stats
        assert 'year_range' in stats
        
        assert stats['bulletin_count'] == 1
        assert stats['category_data_count'] == 1
        assert stats['prediction_count'] == 1
        assert '2024' in stats['year_range']
    
    def test_get_database_stats_empty(self):
        """Test database statistics when empty"""
        db = self._create_test_db()
        
        stats = db.get_database_stats()
        
        assert stats['bulletin_count'] == 0
        assert stats['category_data_count'] == 0
        assert stats['prediction_count'] == 0
        assert stats['year_range'] == "No data"


class TestVisaDatabasePostgreSQL:
    """Test PostgreSQL-specific functionality"""
    
    @patch('psycopg2.connect')
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    def test_postgresql_date_handling(self, mock_connect):
        """Test PostgreSQL native date handling"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock fetchone to return native date objects
        mock_cursor.fetchone.return_value = [
            1,  # id
            date(2024, 7, 1),  # bulletin_date (native date)
            2024,  # fiscal_year
            7,  # month
            2024,  # year
            "https://example.com",  # source_url
            datetime(2024, 7, 1, 10, 0, 0),  # created_at (native datetime)
            datetime(2024, 7, 1, 10, 0, 0)   # updated_at (native datetime)
        ]
        
        # Mock category data
        mock_cursor.fetchall.return_value = [
            [
                1,  # id
                1,  # bulletin_id
                'EB-2',  # category
                'India',  # country
                date(2022, 1, 15),  # final_action_date (native date)
                date(2022, 6, 1),   # filing_date (native date)
                'DATE',  # status
                'Test'   # notes
            ]
        ]
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://user:pass@localhost/db'}):
            db = VisaDatabase()
            
            # Test retrieval with native PostgreSQL date objects
            bulletin = db.get_bulletin(2024, 7, 2024)
            
            # Should handle native date/datetime objects correctly
            assert bulletin is not None
            mock_cursor.execute.assert_called()
    
    @patch('psycopg2.connect')
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    def test_postgresql_upsert_syntax(self, mock_connect):
        """Test PostgreSQL ON CONFLICT syntax"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock existing bulletin check
        mock_cursor.fetchone.side_effect = [
            None,  # First call: bulletin doesn't exist
            [1]    # Second call: return bulletin ID
        ]
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://user:pass@localhost/db'}):
            db = VisaDatabase()
            
            # Create sample bulletin
            bulletin = VisaBulletin(
                bulletin_date=date(2024, 7, 1),
                fiscal_year=2024,
                month=7,
                year=2024,
                source_url="https://example.com"
            )
            
            cat_data = CategoryData(
                category=VisaCategory.EB2,
                country=CountryCode.INDIA,
                final_action_date=date(2022, 1, 15),
                status=BulletinStatus.DATE_SPECIFIED
            )
            bulletin.add_category_data(cat_data)
            
            db.save_bulletin(bulletin)
            
            # Verify PostgreSQL-specific SQL was used
            calls = mock_cursor.execute.call_args_list
            
            # Should have INSERT with RETURNING for PostgreSQL
            returning_calls = [call for call in calls if 'RETURNING' in str(call)]
            assert len(returning_calls) > 0
            
            # Should have ON CONFLICT for category data
            conflict_calls = [call for call in calls if 'ON CONFLICT' in str(call)]
            assert len(conflict_calls) > 0


class TestVisaDatabaseEdgeCases:
    """Test edge cases and error conditions"""
    
    def _create_test_db(self, db_path=None):
        """Helper method to create a test database with tables"""
        # Use a temporary file instead of :memory: to avoid connection isolation issues
        import tempfile
        import os
        if db_path is None:
            # Create a temporary file for the database
            fd, db_path = tempfile.mkstemp(suffix='.db')
            os.close(fd)  # Close the file descriptor, we just need the path
            
        # Create the database - tables will be created in __init__
        db = VisaDatabase(db_path=db_path)
        
        # Store the path so we can clean up later if needed
        db._temp_path = db_path if db_path != ":memory:" else None
        return db
    
    def test_bulletin_with_no_categories(self):
        """Test saving bulletin with no category data"""
        db = self._create_test_db()
        
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024,
            source_url="https://example.com"
        )
        # No categories added
        
        bulletin_id = db.save_bulletin(bulletin)
        assert bulletin_id is not None
        
        # Should have bulletin but no category data
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM visa_bulletins")
            assert cursor.fetchone()[0] == 1
            
            cursor.execute("SELECT COUNT(*) FROM category_data")
            assert cursor.fetchone()[0] == 0
    
    def test_category_data_with_null_dates(self):
        """Test category data with null dates"""
        db = self._create_test_db()
        
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024,
            source_url="https://example.com"
        )
        
        # Category with null dates
        cat_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=None,  # Null date
            filing_date=None,        # Null date
            status=BulletinStatus.CURRENT
        )
        bulletin.add_category_data(cat_data)
        
        bulletin_id = db.save_bulletin(bulletin)
        assert bulletin_id is not None
        
        # Retrieve and verify null dates are handled
        retrieved = db.get_bulletin(2024, 7, 2024)
        assert retrieved is not None
        assert len(retrieved.categories) == 1
        assert retrieved.categories[0].final_action_date is None
        assert retrieved.categories[0].filing_date is None
    
    @patch('visa.database.VisaDatabase._create_tables')
    @patch('visa.database.VisaDatabase._ensure_directory_exists')
    @patch('sqlite3.connect')
    def test_database_connection_error_handling(self, mock_connect, mock_ensure_dir, mock_create_tables):
        """Test database connection error handling"""
        # Mock sqlite3.connect to raise an OperationalError
        mock_connect.side_effect = sqlite3.OperationalError("Unable to open database file")
        
        db = VisaDatabase(db_path="/invalid_path/cannot_create.db")
        
        # Should handle connection errors gracefully
        with pytest.raises(sqlite3.OperationalError):
            with db.get_connection():
                pass
    
    def test_large_bulletin_data(self):
        """Test handling of bulletin with many categories"""
        db = self._create_test_db()
        
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024,
            source_url="https://example.com"
        )
        
        # Add many categories (all combinations)
        categories = [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3, VisaCategory.F1, VisaCategory.F2A]
        countries = [CountryCode.WORLDWIDE, CountryCode.INDIA, CountryCode.CHINA, CountryCode.MEXICO]
        
        for category in categories:
            for country in countries:
                cat_data = CategoryData(
                    category=category,
                    country=country,
                    final_action_date=date(2022, 1, 15),
                    status=BulletinStatus.DATE_SPECIFIED
                )
                bulletin.add_category_data(cat_data)
        
        bulletin_id = db.save_bulletin(bulletin)
        assert bulletin_id is not None
        
        # Should have all combinations
        expected_count = len(categories) * len(countries)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM category_data")
            count = cursor.fetchone()[0]
            assert count == expected_count
        
        # Retrieve and verify all categories
        retrieved = db.get_bulletin(2024, 7, 2024)
        assert len(retrieved.categories) == expected_count


@pytest.mark.integration
class TestVisaDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def _create_test_db(self, db_path=None):
        """Helper method to create a test database with tables"""
        # Use a temporary file instead of :memory: to avoid connection isolation issues
        import tempfile
        import os
        if db_path is None:
            # Create a temporary file for the database
            fd, db_path = tempfile.mkstemp(suffix='.db')
            os.close(fd)  # Close the file descriptor, we just need the path
            
        # Create the database - tables will be created in __init__
        db = VisaDatabase(db_path=db_path)
        
        # Store the path so we can clean up later if needed
        db._temp_path = db_path if db_path != ":memory:" else None
        return db
    
    def test_full_bulletin_lifecycle(self):
        """Test complete bulletin lifecycle"""
        db = self._create_test_db()
        
        # Create bulletin with multiple categories
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024,
            source_url="https://example.com"
        )
        
        # Add EB and Family categories
        eb_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2022, 1, 15),
            status=BulletinStatus.DATE_SPECIFIED
        )
        
        family_data = CategoryData(
            category=VisaCategory.F1,
            country=CountryCode.CHINA,
            final_action_date=date(2020, 6, 1),
            status=BulletinStatus.DATE_SPECIFIED
        )
        
        bulletin.add_category_data(eb_data)
        bulletin.add_category_data(family_data)
        
        # Save bulletin
        bulletin_id = db.save_bulletin(bulletin)
        assert bulletin_id is not None
        
        # Retrieve bulletin
        retrieved = db.get_bulletin(2024, 7, 2024)
        assert retrieved is not None
        assert len(retrieved.categories) == 2
        
        # Get category history
        eb_history = db.get_category_history(VisaCategory.EB2, CountryCode.INDIA)
        assert len(eb_history) == 1
        
        family_history = db.get_category_history(VisaCategory.F1, CountryCode.CHINA)
        assert len(family_history) == 1
        
        # Get statistics
        stats = db.get_database_stats()
        assert stats['bulletin_count'] == 1
        assert stats['category_data_count'] == 2
        
        # Update bulletin (add more data)
        bulletin.categories.clear()
        new_data = CategoryData(
            category=VisaCategory.EB3,
            country=CountryCode.MEXICO,
            final_action_date=date(2021, 12, 1),
            status=BulletinStatus.DATE_SPECIFIED
        )
        bulletin.add_category_data(new_data)
        
        # Save updated bulletin
        updated_id = db.save_bulletin(bulletin)
        assert updated_id == bulletin_id  # Same ID
        
        # Verify update
        retrieved = db.get_bulletin(2024, 7, 2024)
        assert len(retrieved.categories) == 1  # Should have only new data
        assert retrieved.categories[0].category == VisaCategory.EB3
        
        # Delete bulletin
        deleted = db.delete_bulletin(2024, 7, 2024)
        assert deleted is True
        
        # Verify deletion
        retrieved = db.get_bulletin(2024, 7, 2024)
        assert retrieved is None
        
        # Stats should reflect deletion
        stats = db.get_database_stats()
        assert stats['bulletin_count'] == 0
        assert stats['category_data_count'] == 0
    
    def test_multi_year_data_operations(self):
        """Test operations across multiple years"""
        db = self._create_test_db()
        
        # Create bulletins for multiple years
        years = [2022, 2023, 2024]
        for year in years:
            for month in [1, 6, 12]:  # 3 bulletins per year
                bulletin = VisaBulletin(
                    bulletin_date=date(year, month, 1),
                    fiscal_year=year if month < 10 else year + 1,
                    month=month,
                    year=year,
                    source_url=f"https://example.com/{year}-{month}"
                )
                
                cat_data = CategoryData(
                    category=VisaCategory.EB2,
                    country=CountryCode.INDIA,
                    final_action_date=date(year - 2, month, 1),
                    status=BulletinStatus.DATE_SPECIFIED
                )
                bulletin.add_category_data(cat_data)
                
                db.save_bulletin(bulletin)
        
        # Test range queries
        all_bulletins = db.get_bulletins_range(2022, 2024)
        assert len(all_bulletins) == 9  # 3 years * 3 bulletins each
        
        partial_range = db.get_bulletins_range(2023, 2023)
        assert len(partial_range) == 3  # Only 2023 bulletins
        
        # Test category history across years
        history = db.get_category_history(
            VisaCategory.EB2, 
            CountryCode.INDIA,
            start_year=2022,
            end_year=2024
        )
        assert len(history) == 9  # All entries
        
        # Test statistics
        stats = db.get_database_stats()
        assert stats['bulletin_count'] == 9
        assert stats['category_data_count'] == 9
        assert '2022-2024' in stats['year_range']


@pytest.mark.mock
class TestVisaDatabaseMocked:
    """Mock tests for database external dependencies"""
    
    @patch('sqlite3.connect')
    def test_sqlite_connection_mocked(self, mock_connect):
        """Test SQLite connection with mocking"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        db = VisaDatabase(db_path=":memory:")
        
        with db.get_connection() as conn:
            assert conn == mock_conn
            
        mock_connect.assert_called_with(":memory:")
    
    @patch('visa.database.VisaDatabase._create_tables')
    @patch('os.path.dirname')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_directory_creation_mocked(self, mock_makedirs, mock_exists, mock_dirname, mock_create_tables):
        """Test directory creation logic"""
        mock_dirname.return_value = "/test/path"
        mock_exists.return_value = False
        
        db = VisaDatabase(db_path="/test/path/database.db")
        mock_create_tables.assert_called_once()
        
        mock_dirname.assert_called_with("/test/path/database.db")
        mock_exists.assert_called_with("/test/path")
        mock_makedirs.assert_called_with("/test/path", exist_ok=True)