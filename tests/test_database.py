"""Tests for database connections"""
import pytest
from unittest.mock import MagicMock, patch
from src.utils.database import (
    DatabaseFactory,
    SQLiteDatabase,
    PostgreSQLDatabase,
    MongoManager,
    RedisManager
)

@pytest.fixture
def mock_config():
    """Mock configuration"""
    with patch('src.utils.database.Config') as mock:
        config = mock.return_value
        config.DATABASE_TYPE = "sqlite"
        config.DATABASE_PATH = ":memory:"
        config.DOCKER_MODE = False
        yield config

def test_database_factory_sqlite(mock_config):
    """Test database factory returns SQLite instance"""
    mock_config.DATABASE_TYPE = "sqlite"
    db = DatabaseFactory.get_database()
    assert isinstance(db, SQLiteDatabase)

def test_database_factory_postgresql(mock_config):
    """Test database factory returns PostgreSQL instance"""
    mock_config.DATABASE_TYPE = "postgresql"
    db = DatabaseFactory.get_database()
    assert isinstance(db, PostgreSQLDatabase)

def test_sqlite_connection():
    """Test SQLite connection creation"""
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

@patch('src.utils.database.MongoClient')
def test_mongo_manager_docker_mode(mock_client, mock_config):
    """Test MongoDB manager in Docker mode"""
    mock_config.DOCKER_MODE = True
    mock_config.MONGO_HOST = "test-mongodb"
    mock_config.MONGO_PORT = 27017
    mock_config.MONGO_USER = "test_user"
    mock_config.MONGO_PASSWORD = "test_pass"
    manager = MongoManager()
    _ = manager.client  # Access client to trigger connection
    mock_client.assert_called_once_with(
        host="test-mongodb",
        port=27017,
        username="test_user",
        password="test_pass"
    )

@patch('redis.Redis')
def test_redis_manager_docker_mode(mock_redis, mock_config):
    """Test Redis manager in Docker mode"""
    mock_config.DOCKER_MODE = True
    mock_config.REDIS_HOST = "test-redis"
    manager = RedisManager()
    _ = manager.client  # Access client to trigger connection
    mock_redis.assert_called_once_with(
        host="test-redis",
        port=mock_config.REDIS_PORT,
        password=mock_config.REDIS_PASSWORD,
        decode_responses=True
    )

@patch('src.utils.database.MongoClient')
def test_mongo_manager_local_mode(mock_client, mock_config):
    """Test MongoDB manager in local mode"""
    mock_config.DOCKER_MODE = False
    manager = MongoManager()
    _ = manager.client  # Access client to trigger connection
    mock_client.assert_called_once_with()

def test_redis_manager_local_mode(mock_config):
    """Test Redis manager in local mode"""
    mock_config.DOCKER_MODE = False
    manager = RedisManager()
    with patch('redis.Redis') as mock_redis:
        _ = manager.client  # Access client to trigger connection
        mock_redis.assert_called_once_with(decode_responses=True)