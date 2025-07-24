"""
Database connection management for different environments
"""
from typing import Optional
import os
import sqlite3
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor
from pymongo import MongoClient
import redis

from .config import Config

class DatabaseFactory:
    """Factory for creating database connections based on environment"""
    
    @staticmethod
    def get_database():
        """Get appropriate database connection based on configuration"""
        config = Config()
        if config.DATABASE_TYPE == "postgresql":
            return PostgreSQLDatabase()
        return SQLiteDatabase()

class SQLiteDatabase:
    """SQLite database connection manager"""
    
    def __init__(self):
        self.db_path = Config().DATABASE_PATH
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get SQLite connection with context management"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

class PostgreSQLDatabase:
    """PostgreSQL database connection manager"""
    
    def __init__(self):
        self.config = Config()
    
    @contextmanager
    def get_connection(self):
        """Get PostgreSQL connection with context management"""
        conn = psycopg2.connect(
            host=self.config.POSTGRES_HOST,
            port=self.config.POSTGRES_PORT,
            database=self.config.POSTGRES_DB,
            user=self.config.POSTGRES_USER,
            password=self.config.POSTGRES_PASSWORD,
            cursor_factory=DictCursor
        )
        try:
            yield conn
        finally:
            conn.close()

class MongoManager:
    """MongoDB connection manager with local fallback"""
    
    def __init__(self):
        self.config = Config()
        self._client = None
        self._db = None
    
    @property
    def client(self):
        """Get MongoDB client with lazy initialization"""
        if self._client is None:
            if self.config.DOCKER_MODE:
                self._client = MongoClient(
                    host=self.config.MONGO_HOST,
                    port=self.config.MONGO_PORT,
                    username=self.config.MONGO_USER,
                    password=self.config.MONGO_PASSWORD
                )
            else:
                self._client = MongoClient()  # Local default connection
        return self._client
    
    @property
    def db(self):
        """Get database instance"""
        if self._db is None:
            self._db = self.client[self.config.MONGO_DB]
        return self._db
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

class RedisManager:
    """Redis connection manager with local fallback"""
    
    def __init__(self):
        self.config = Config()
        self._client = None
    
    @property
    def client(self):
        """Get Redis client with lazy initialization"""
        if self._client is None:
            if self.config.DOCKER_MODE:
                self._client = redis.Redis(
                    host=self.config.REDIS_HOST,
                    port=self.config.REDIS_PORT,
                    password=self.config.REDIS_PASSWORD,
                    decode_responses=True
                )
            else:
                self._client = redis.Redis(decode_responses=True)  # Local default connection
        return self._client
    
    def close(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            self._client = None

# Global instances for convenience
db = DatabaseFactory.get_database()
mongo = MongoManager()
redis_client = RedisManager()