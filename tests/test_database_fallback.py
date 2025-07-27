"""
Tests for Database Fallback Functionality

This module tests the PostgreSQL fallback mechanism added to VisaDatabase
for Docker integration as part of issues #25 and #27.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime, date

from visa.database import VisaDatabase
from visa.models import VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus


class TestVisaDatabaseFallback:
    """Test VisaDatabase PostgreSQL fallback functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Clear environment variables
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def teardown_method(self):
        """Clean up after tests"""
        # Clear environment variables
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_init_postgres_preferred_success(self, mock_config):
        """Test successful PostgreSQL initialization when preferred"""
        # Set up environment for PostgreSQL
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            db = VisaDatabase()
            
            assert db.use_postgres is True
            assert db.database_url == 'postgresql://user:pass@db:5432/visadb'
            assert db.db_path is None
            mock_connect.assert_called_once_with('postgresql://user:pass@db:5432/visadb')
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_init_postgres_fallback_to_sqlite(self, mock_config):
        """Test fallback to SQLite when PostgreSQL fails"""
        # Set up environment for PostgreSQL
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_connect:
            # Simulate PostgreSQL connection failure
            mock_connect.side_effect = Exception("could not translate host name \"db\" to address")
            
            with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
                mock_sqlite_conn = Mock()
                mock_sqlite_cursor = Mock()
                mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
                mock_sqlite_connect.return_value = mock_sqlite_conn
                
                # Mock os.makedirs to prevent actual directory creation
                with patch('visa.database.os.makedirs'):
                    db = VisaDatabase()
                
                # Should fallback to SQLite
                assert db.use_postgres is False
                assert db.database_url is None
                assert db.db_path == '/app/data/test.db'
                
                # PostgreSQL should have been attempted first
                mock_connect.assert_called_once_with('postgresql://user:pass@db:5432/visadb')
    
    @patch('visa.database.POSTGRES_AVAILABLE', False)
    @patch('visa.database.VisaConfig')
    def test_init_postgres_unavailable_uses_sqlite(self, mock_config):
        """Test using SQLite when PostgreSQL is not available"""
        # Set up environment for PostgreSQL, but psycopg2 not available
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
            mock_sqlite_conn = Mock()
            mock_sqlite_cursor = Mock()
            mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
            mock_sqlite_connect.return_value = mock_sqlite_conn
            
            # Mock os.makedirs to prevent actual directory creation
            with patch('visa.database.os.makedirs'):
                db = VisaDatabase()
            
            # Should use SQLite because PostgreSQL is not available
            assert db.use_postgres is False
            assert db.database_url == 'postgresql://user:pass@db:5432/visadb'  # URL is still stored
            assert db.db_path == '/app/data/test.db'
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_init_no_database_url_uses_sqlite(self, mock_config):
        """Test using SQLite when no DATABASE_URL is set"""
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
            mock_sqlite_conn = Mock()
            mock_sqlite_cursor = Mock()
            mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
            mock_sqlite_connect.return_value = mock_sqlite_conn
            
            # Mock os.makedirs to prevent actual directory creation
            with patch('visa.database.os.makedirs'):
                db = VisaDatabase()
            
            # Should use SQLite because no DATABASE_URL
            assert db.use_postgres is False
            assert db.database_url is None
            assert db.db_path == '/app/data/test.db'
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_init_non_postgres_database_url_uses_sqlite(self, mock_config):
        """Test using SQLite when DATABASE_URL is not PostgreSQL"""
        # Set up environment for non-PostgreSQL database
        os.environ['DATABASE_URL'] = 'mysql://user:pass@localhost:3306/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
            mock_sqlite_conn = Mock()
            mock_sqlite_cursor = Mock()
            mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
            mock_sqlite_connect.return_value = mock_sqlite_conn
            
            # Mock os.makedirs to prevent actual directory creation
            with patch('visa.database.os.makedirs'):
                db = VisaDatabase()
            
            # Should use SQLite because DATABASE_URL is not PostgreSQL
            assert db.use_postgres is False
            assert db.database_url == 'mysql://user:pass@localhost:3306/visadb'  # URL is still stored
            assert db.db_path == '/app/data/test.db'


class TestDatabaseConnectionManagement:
    """Test database connection management for both PostgreSQL and SQLite"""
    
    def setup_method(self):
        """Set up test fixtures"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def teardown_method(self):
        """Clean up after tests"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_get_connection_postgres(self, mock_config):
        """Test get_connection context manager for PostgreSQL"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            db = VisaDatabase()
            
            # Test context manager
            with db.get_connection() as conn:
                assert conn == mock_conn
                assert conn.autocommit is False
            
            # Verify connection was closed (may be called multiple times due to context manager and initialization)
            assert mock_conn.close.call_count >= 1
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_get_connection_sqlite_fallback(self, mock_config):
        """Test get_connection context manager for SQLite fallback"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_pg_connect:
            # Simulate PostgreSQL connection failure during init
            mock_pg_connect.side_effect = Exception("Connection failed")
            
            with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
                mock_sqlite_conn = Mock()
                mock_sqlite_cursor = Mock()
                mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
                mock_sqlite_connect.return_value = mock_sqlite_conn
                
                with patch('visa.database.os.makedirs'):
                    db = VisaDatabase()
                
                # Should have fallen back to SQLite
                assert db.use_postgres is False
                
                # Test context manager uses SQLite
                with db.get_connection() as conn:
                    assert conn == mock_sqlite_conn
                    assert conn.row_factory == mock_sqlite_connect.return_value.row_factory
                
                # Verify connection was closed (may be called multiple times)
                assert mock_sqlite_conn.close.call_count >= 1
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_param_placeholder_postgres(self, mock_config):
        """Test parameter placeholder for PostgreSQL"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            db = VisaDatabase()
            
            assert db._get_param_placeholder() == "%s"
    
    @patch('visa.database.POSTGRES_AVAILABLE', False)
    @patch('visa.database.VisaConfig')
    def test_param_placeholder_sqlite(self, mock_config):
        """Test parameter placeholder for SQLite"""
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
            mock_sqlite_conn = Mock()
            mock_sqlite_cursor = Mock()
            mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
            mock_sqlite_connect.return_value = mock_sqlite_conn
            
            with patch('visa.database.os.makedirs'):
                db = VisaDatabase()
            
            assert db._get_param_placeholder() == "?"


class TestDatabaseOperationsCompatibility:
    """Test that database operations work correctly with both PostgreSQL and SQLite"""
    
    def setup_method(self):
        """Set up test fixtures"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        # Create a sample bulletin for testing
        self.sample_bulletin = VisaBulletin(
            bulletin_date=date(2024, 1, 15),
            fiscal_year=2024,
            month=1,
            year=2024,
            source_url="https://example.com/bulletin"
        )
        
        # Add sample category data
        self.sample_bulletin.add_category_data(CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2023, 6, 15),
            filing_date=date(2023, 8, 1),
            status=BulletinStatus.CURRENT,
            notes="Test notes"
        ))
    
    def teardown_method(self):
        """Clean up after tests"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_save_bulletin_postgres_fallback_to_sqlite(self, mock_config):
        """Test saving bulletin with PostgreSQL fallback to SQLite"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_pg_connect:
            # Simulate PostgreSQL connection failure during init
            mock_pg_connect.side_effect = Exception("Connection failed")
            
            with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
                mock_sqlite_conn = Mock()
                mock_sqlite_cursor = Mock()
                mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
                mock_sqlite_conn.__enter__ = Mock(return_value=mock_sqlite_conn)
                mock_sqlite_conn.__exit__ = Mock(return_value=None)
                mock_sqlite_connect.return_value = mock_sqlite_conn
                
                # Mock cursor methods
                mock_sqlite_cursor.fetchone.return_value = None  # No existing bulletin
                mock_sqlite_cursor.lastrowid = 1
                
                with patch('visa.database.os.makedirs'):
                    db = VisaDatabase()
                
                # Should have fallen back to SQLite
                assert db.use_postgres is False
                
                # Test saving bulletin
                bulletin_id = db.save_bulletin(self.sample_bulletin)
                
                assert bulletin_id == 1
                
                # Verify SQLite-specific calls were made
                assert mock_sqlite_cursor.execute.call_count >= 2  # Insert bulletin + category data (plus table creation)
                assert mock_sqlite_conn.commit.call_count >= 1  # May be called multiple times (init + operation)
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_get_database_stats_postgres_fallback(self, mock_config):
        """Test getting database stats with PostgreSQL fallback to SQLite"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_pg_connect:
            # Simulate PostgreSQL connection failure during init
            mock_pg_connect.side_effect = Exception("Connection failed")
            
            with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
                mock_sqlite_conn = Mock()
                mock_sqlite_cursor = Mock()
                mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
                mock_sqlite_conn.__enter__ = Mock(return_value=mock_sqlite_conn)
                mock_sqlite_conn.__exit__ = Mock(return_value=None)
                mock_sqlite_connect.return_value = mock_sqlite_conn
                
                # Mock stats queries
                mock_sqlite_cursor.fetchone.side_effect = [
                    (25,),      # bulletin_count
                    (250,),     # category_data_count  
                    (10,),      # prediction_count
                    (2020, 2024)  # date_range
                ]
                
                with patch('visa.database.os.makedirs'):
                    db = VisaDatabase()
                
                # Should have fallen back to SQLite
                assert db.use_postgres is False
                
                # Test getting stats
                stats = db.get_database_stats()
                
                assert stats['bulletin_count'] == 25
                assert stats['category_data_count'] == 250
                assert stats['prediction_count'] == 10
                assert stats['year_range'] == '2020-2024'
                
                # Verify SQLite queries were called (includes table creation + stats queries)
                assert mock_sqlite_cursor.execute.call_count >= 4


class TestFallbackErrorScenarios:
    """Test error scenarios during fallback process"""
    
    def setup_method(self):
        """Set up test fixtures"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def teardown_method(self):
        """Clean up after tests"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_fallback_sqlite_also_fails(self, mock_config):
        """Test behavior when both PostgreSQL and SQLite fail"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_pg_connect:
            # Simulate PostgreSQL connection failure
            mock_pg_connect.side_effect = Exception("PostgreSQL connection failed")
            
            with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
                # Simulate SQLite connection failure too
                mock_sqlite_connect.side_effect = Exception("SQLite connection failed")
                
                with patch('visa.database.os.makedirs'):
                    # Should raise the SQLite exception since that's the fallback
                    with pytest.raises(Exception, match="SQLite connection failed"):
                        VisaDatabase()
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_table_creation_failure_during_fallback(self, mock_config):
        """Test table creation failure during fallback"""
        os.environ['DATABASE_URL'] = 'postgresql://user:pass@db:5432/visadb'
        mock_config.DATABASE_PATH = '/app/data/test.db'
        
        with patch('visa.database.psycopg2.connect') as mock_pg_connect:
            # Simulate PostgreSQL connection failure during table creation
            mock_pg_connect.side_effect = Exception("PostgreSQL connection failed")
            
            with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
                mock_sqlite_conn = Mock()
                mock_sqlite_cursor = Mock()
                mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
                mock_sqlite_conn.__enter__ = Mock(return_value=mock_sqlite_conn)
                mock_sqlite_conn.__exit__ = Mock(return_value=None)
                mock_sqlite_connect.return_value = mock_sqlite_conn
                
                # Simulate table creation failure
                mock_sqlite_cursor.execute.side_effect = Exception("Table creation failed")
                
                with patch('visa.database.os.makedirs'):
                    # Should raise the table creation exception
                    with pytest.raises(Exception, match="Table creation failed"):
                        VisaDatabase()


class TestDockerEnvironmentIntegration:
    """Test integration with Docker environment variables"""
    
    def setup_method(self):
        """Set up test fixtures"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def teardown_method(self):
        """Clean up after tests"""
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_docker_database_url_detection(self, mock_config):
        """Test detection of Docker-style DATABASE_URL"""
        # Docker-style PostgreSQL URL
        os.environ['DATABASE_URL'] = 'postgresql://postgres:password@db:5432/visa_data'
        mock_config.DATABASE_PATH = '/app/data/visa.db'
        
        with patch('visa.database.psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            db = VisaDatabase()
            
            assert db.use_postgres is True
            assert 'db:5432' in db.database_url
            assert 'postgresql://' in db.database_url
    
    @patch('visa.database.POSTGRES_AVAILABLE', True)
    @patch('visa.database.VisaConfig')
    def test_docker_host_resolution_failure(self, mock_config):
        """Test handling of Docker host resolution failure"""
        # Docker-style PostgreSQL URL with host that can't be resolved
        os.environ['DATABASE_URL'] = 'postgresql://postgres:password@db:5432/visa_data'
        mock_config.DATABASE_PATH = '/app/data/visa.db'
        
        with patch('visa.database.psycopg2.connect') as mock_pg_connect:
            # Simulate Docker host resolution failure
            mock_pg_connect.side_effect = Exception('could not translate host name "db" to address: Name or service not known')
            
            with patch('visa.database.sqlite3.connect') as mock_sqlite_connect:
                mock_sqlite_conn = Mock()
                mock_sqlite_cursor = Mock()
                mock_sqlite_conn.cursor.return_value = mock_sqlite_cursor
                mock_sqlite_connect.return_value = mock_sqlite_conn
                
                with patch('visa.database.os.makedirs'):
                    db = VisaDatabase()
                
                # Should fallback to SQLite gracefully
                assert db.use_postgres is False
                assert db.db_path == '/app/data/visa.db'