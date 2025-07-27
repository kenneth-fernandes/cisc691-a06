"""Tests for database connections"""
import pytest
from unittest.mock import MagicMock, patch
from src.utils.database import (
    DatabaseFactory,
    SQLiteDatabase,
    PostgreSQLDatabase,
    RedisManager
)

@pytest.fixture
def mock_config():
    """Mock configuration"""
    with patch('src.utils.database.Config') as mock:
        config = mock.return_value
        config.DATABASE_TYPE = "postgresql"
        config.POSTGRES_HOST = "test-db"
        config.POSTGRES_PORT = 5432
        config.POSTGRES_DB = "test_db"
        config.POSTGRES_USER = "test_user"
        config.POSTGRES_PASSWORD = "test_pass"
        config.REDIS_HOST = "test-redis"
        config.REDIS_PORT = 6380
        config.REDIS_PASSWORD = "test_redis_pass"
        yield config

def test_database_factory_postgresql_default(mock_config):
    """Test database factory returns PostgreSQL instance (default)"""
    mock_config.DATABASE_TYPE = "postgresql"
    db = DatabaseFactory.get_database()
    assert isinstance(db, PostgreSQLDatabase)

def test_database_factory_fallback_sqlite(mock_config):
    """Test database factory fallback to SQLite"""
    mock_config.DATABASE_TYPE = "unknown"  # Should fallback to SQLite
    db = DatabaseFactory.get_database()
    assert isinstance(db, SQLiteDatabase)

@patch('src.utils.database.Config')
def test_sqlite_connection_with_mock(mock_config_class):
    """Test SQLite connection creation with mocked config"""
    # Mock config to provide DATABASE_PATH
    mock_config = mock_config_class.return_value
    mock_config.DATABASE_PATH = ":memory:"
    
    db = SQLiteDatabase()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Drop table if exists
        cursor.execute("DROP TABLE IF EXISTS test")
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO test (id) VALUES (1)")
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()
        assert result[0] == 1

@patch('psycopg2.connect')
def test_postgresql_connection(mock_connect, mock_config):
    """Test PostgreSQL connection creation"""
    mock_config.POSTGRES_HOST = "test-db"
    db = PostgreSQLDatabase()
    with db.get_connection():
        mock_connect.assert_called_once()


@patch('redis.Redis')
def test_redis_manager_connection(mock_redis, mock_config):
    """Test Redis manager connection (Docker mode)"""
    mock_config.REDIS_HOST = "test-redis"
    manager = RedisManager()
    _ = manager.client  # Access client to trigger connection
    mock_redis.assert_called_once_with(
        host="test-redis",
        port=mock_config.REDIS_PORT,
        password=mock_config.REDIS_PASSWORD,
        decode_responses=True
    )