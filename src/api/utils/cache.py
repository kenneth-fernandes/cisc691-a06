"""
Redis-based caching utilities for API responses
"""
import json
import hashlib
from typing import Any, Optional, Dict, Union
from functools import wraps
import logging
import redis
from fastapi import Request

from utils.config import get_config

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for API responses"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.config = get_config()
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                password=self.config.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Connected to Redis at {self.config.REDIS_HOST}:{self.config.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_client is not None
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        # Create a string from args and kwargs
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        # Hash to ensure consistent key length
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"api_cache:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available():
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (default 5 minutes)"""
        if not self.is_available():
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache pattern delete error: {e}")
        return 0
    
    def clear_all(self) -> bool:
        """Clear all cache entries"""
        if not self.is_available():
            return False
        
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()


def cache_response(ttl: int = 300, prefix: str = "default"):
    """
    Decorator for caching API responses
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        prefix: Cache key prefix for organization
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if cache_manager.set(cache_key, result, ttl):
                logger.info(f"Cached result for {func.__name__} (TTL: {ttl}s)")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """Invalidate cache entries matching pattern"""
    deleted_count = cache_manager.delete_pattern(f"api_cache:{pattern}*")
    if deleted_count > 0:
        logger.info(f"Invalidated {deleted_count} cache entries for pattern: {pattern}")
    return deleted_count


def cache_key_for_request(request: Request, prefix: str = "endpoint") -> str:
    """Generate cache key for HTTP request"""
    # Include path, query params, and relevant headers
    path = request.url.path
    query_params = str(sorted(request.query_params.items()))
    
    # Create cache key
    key_data = f"{prefix}:{path}:{query_params}"
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    return f"api_cache:{prefix}:{key_hash}"


class CacheStats:
    """Cache statistics and monitoring"""
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """Get Redis cache information"""
        if not cache_manager.is_available():
            return {"status": "unavailable", "reason": "Redis not connected"}
        
        try:
            info = cache_manager.redis_client.info()
            return {
                "status": "available",
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_ratio": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 2
                )
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def get_cache_keys(pattern: str = "api_cache:*") -> list:
        """Get all cache keys matching pattern"""
        if not cache_manager.is_available():
            return []
        
        try:
            return cache_manager.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting cache keys: {e}")
            return []


# Cache configuration presets
CACHE_PRESETS = {
    "short": 60,      # 1 minute
    "medium": 300,    # 5 minutes  
    "long": 1800,     # 30 minutes
    "very_long": 3600 # 1 hour
}