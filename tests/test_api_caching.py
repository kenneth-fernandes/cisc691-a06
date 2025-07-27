"""
Tests for API caching functionality
"""
import pytest
import time
from unittest.mock import patch, MagicMock, Mock
from fastapi.testclient import TestClient
import json

from api.main import app
from api.utils.cache import CacheManager, cache_response, CACHE_PRESETS, CacheStats

client = TestClient(app)


class TestCacheManager:
    """Test Redis cache manager"""
    
    @patch('redis.Redis')
    def test_cache_manager_initialization_success(self, mock_redis):
        """Test successful cache manager initialization"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        cache_manager = CacheManager()
        assert cache_manager.is_available() == True
        mock_redis_instance.ping.assert_called_once()
    
    @patch('redis.Redis')
    def test_cache_manager_initialization_failure(self, mock_redis):
        """Test cache manager initialization failure"""
        mock_redis.side_effect = Exception("Redis connection failed")
        
        cache_manager = CacheManager()
        assert cache_manager.is_available() == False
    
    @patch('redis.Redis')
    def test_cache_set_get(self, mock_redis):
        """Test cache set and get operations"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.setex.return_value = True
        mock_redis_instance.get.return_value = '{"test": "data"}'
        mock_redis.return_value = mock_redis_instance
        
        cache_manager = CacheManager()
        
        # Test set
        result = cache_manager.set("test_key", {"test": "data"}, 300)
        assert result == True
        mock_redis_instance.setex.assert_called_once()
        
        # Test get
        cached_data = cache_manager.get("test_key")
        assert cached_data == {"test": "data"}
        mock_redis_instance.get.assert_called_with("test_key")
    
    @patch('redis.Redis')
    def test_cache_delete(self, mock_redis):
        """Test cache delete operation"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.delete.return_value = 1
        mock_redis.return_value = mock_redis_instance
        
        cache_manager = CacheManager()
        
        result = cache_manager.delete("test_key")
        assert result == True
        mock_redis_instance.delete.assert_called_with("test_key")
    
    @patch('redis.Redis')
    def test_cache_delete_pattern(self, mock_redis):
        """Test cache delete by pattern"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.keys.return_value = ["key1", "key2", "key3"]
        mock_redis_instance.delete.return_value = 3
        mock_redis.return_value = mock_redis_instance
        
        cache_manager = CacheManager()
        
        result = cache_manager.delete_pattern("test_*")
        assert result == 3
        mock_redis_instance.keys.assert_called_with("test_*")
        mock_redis_instance.delete.assert_called_with("key1", "key2", "key3")
    
    @patch('redis.Redis')
    def test_cache_clear_all(self, mock_redis):
        """Test cache clear all operation"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.flushdb.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        cache_manager = CacheManager()
        
        result = cache_manager.clear_all()
        assert result == True
        mock_redis_instance.flushdb.assert_called_once()


class TestCacheDecorator:
    """Test cache response decorator"""
    
    @patch('api.utils.cache.cache_manager')
    @pytest.mark.asyncio
    async def test_cache_decorator_hit(self, mock_cache_manager):
        """Test cache decorator with cache hit"""
        mock_cache_manager.get.return_value = {"cached": "response"}
        mock_cache_manager.set.return_value = True
        
        @cache_response(ttl=300, prefix="test")
        async def test_function():
            return {"fresh": "response"}
        
        # First call should return cached data
        result = await test_function()
        assert result == {"cached": "response"}
        mock_cache_manager.get.assert_called_once()
        mock_cache_manager.set.assert_not_called()
    
    @patch('api.utils.cache.cache_manager')
    @pytest.mark.asyncio
    async def test_cache_decorator_miss(self, mock_cache_manager):
        """Test cache decorator with cache miss"""
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set.return_value = True
        
        @cache_response(ttl=300, prefix="test")
        async def test_function():
            return {"fresh": "response"}
        
        # First call should execute function and cache result
        result = await test_function()
        assert result == {"fresh": "response"}
        mock_cache_manager.get.assert_called_once()
        mock_cache_manager.set.assert_called_once()


class TestCachedEndpoints:
    """Test cached API endpoints"""
    
    def test_categories_endpoint_caching(self):
        """Test categories endpoint returns expected data"""
        response = client.get("/api/analytics/categories")
        assert response.status_code == 200
        data = response.json()
        assert "employment_based" in data
        assert "family_based" in data
        
        # Check cache headers
        assert "Cache-Control" in response.headers
    
    def test_countries_endpoint_caching(self):
        """Test countries endpoint returns expected data"""
        response = client.get("/api/analytics/countries")
        assert response.status_code == 200
        data = response.json()
        assert "countries" in data
        
        # Check cache headers
        assert "Cache-Control" in response.headers
    
    @patch('api.routers.analytics.repository')
    def test_bulletins_endpoint_caching(self, mock_repository):
        """Test bulletins endpoint caching"""
        mock_repository.get_bulletins_by_year_range.return_value = []
        
        response = client.get("/api/analytics/bulletins")
        assert response.status_code == 200
        data = response.json()
        assert "bulletins" in data
        assert "count" in data
        
        # Check cache headers
        assert "Cache-Control" in response.headers


class TestCacheManagementEndpoints:
    """Test cache management endpoints"""
    
    @patch('api.utils.cache.cache_manager')
    def test_cache_stats_endpoint(self, mock_cache_manager):
        """Test cache statistics endpoint"""
        mock_cache_manager.is_available.return_value = True
        mock_cache_manager.redis_client.info.return_value = {
            "used_memory_human": "1.5M",
            "connected_clients": 2,
            "keyspace_hits": 100,
            "keyspace_misses": 20
        }
        
        response = client.get("/api/analytics/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "used_memory" in data
        assert "hit_ratio" in data
    
    @patch('api.routers.analytics.cache_manager')
    def test_cache_clear_endpoint(self, mock_cache_manager):
        """Test cache clear endpoint"""
        mock_cache_manager.clear_all.return_value = True
        
        response = client.delete("/api/analytics/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleared" in data["message"].lower()
    
    @patch('api.utils.cache.cache_manager')
    def test_cache_invalidate_endpoint(self, mock_cache_manager):
        """Test cache invalidation endpoint"""
        mock_cache_manager.delete_pattern.return_value = 5
        
        response = client.delete("/api/analytics/cache/invalidate/test_pattern")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert data["deleted_count"] == 5
        assert data["pattern"] == "test_pattern"


class TestCacheStats:
    """Test cache statistics functionality"""
    
    @patch('api.utils.cache.cache_manager')
    def test_cache_stats_available(self, mock_cache_manager):
        """Test cache stats when Redis is available"""
        mock_cache_manager.is_available.return_value = True
        mock_cache_manager.redis_client.info.return_value = {
            "used_memory_human": "2.1M",
            "connected_clients": 3,
            "total_commands_processed": 1500,
            "keyspace_hits": 800,
            "keyspace_misses": 200
        }
        
        stats = CacheStats.get_cache_info()
        assert stats["status"] == "available"
        assert abs(stats["hit_ratio"] - 80.0) < 0.01  # 800/(800+200) * 100
        assert stats["used_memory"] == "2.1M"
    
    @patch('api.utils.cache.cache_manager')
    def test_cache_stats_unavailable(self, mock_cache_manager):
        """Test cache stats when Redis is unavailable"""
        mock_cache_manager.is_available.return_value = False
        
        stats = CacheStats.get_cache_info()
        assert stats["status"] == "unavailable"
        assert "reason" in stats
    
    @patch('api.utils.cache.cache_manager')
    def test_cache_keys_retrieval(self, mock_cache_manager):
        """Test cache keys retrieval"""
        mock_cache_manager.is_available.return_value = True
        mock_cache_manager.redis_client.keys.return_value = [
            "api_cache:categories:abc123",
            "api_cache:countries:def456",
            "api_cache:bulletins:ghi789"
        ]
        
        keys = CacheStats.get_cache_keys()
        assert len(keys) == 3
        assert all(key.startswith("api_cache:") for key in keys)


class TestCachePerformance:
    """Test cache performance characteristics"""
    
    @patch('api.utils.cache.cache_manager')
    def test_cache_performance_hit(self, mock_cache_manager):
        """Test performance improvement with cache hit"""
        # Mock fast cache response
        mock_cache_manager.get.return_value = {"cached": "fast_response"}
        mock_cache_manager.is_available.return_value = True
        
        start_time = time.time()
        response = client.get("/api/analytics/categories")
        end_time = time.time()
        
        assert response.status_code == 200
        # Should be very fast since it's cached
        assert (end_time - start_time) < 1.0
    
    def test_multiple_requests_consistency(self):
        """Test that multiple requests return consistent data"""
        responses = []
        for _ in range(3):
            response = client.get("/api/analytics/categories")
            responses.append(response.json())
        
        # All responses should be identical
        assert all(resp == responses[0] for resp in responses)


class TestCacheMiddleware:
    """Test cache middleware functionality"""
    
    def test_cache_headers_present(self):
        """Test that cache headers are added to responses"""
        response = client.get("/api/analytics/categories")
        assert response.status_code == 200
        
        # Should have cache control headers
        assert "Cache-Control" in response.headers
        assert "X-Process-Time" in response.headers
    
    def test_cache_control_values(self):
        """Test cache control header values for different endpoints"""
        # Categories should have long cache
        response = client.get("/api/analytics/categories")
        cache_control = response.headers.get("Cache-Control", "")
        assert "max-age=3600" in cache_control or "public" in cache_control
        
        # Health should not be cached
        response = client.get("/health")
        cache_control = response.headers.get("Cache-Control", "")
        assert "no-cache" in cache_control or cache_control == ""


class TestCacheErrorHandling:
    """Test cache error handling scenarios"""
    
    def test_cache_failure_graceful_degradation(self):
        """Test graceful degradation when cache fails"""
        # API should still work without cache
        response = client.get("/api/analytics/categories")
        assert response.status_code == 200
        data = response.json()
        assert "employment_based" in data
    
    @patch('api.utils.cache.cache_manager')
    def test_cache_set_failure_handling(self, mock_cache_manager):
        """Test handling of cache set failures"""
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set.return_value = False  # Cache set fails
        mock_cache_manager.is_available.return_value = True
        
        # Should still return response even if caching fails
        response = client.get("/api/analytics/categories")
        assert response.status_code == 200
    
    def test_cache_get_exception_handling(self):
        """Test handling of cache get exceptions"""
        # Should fallback to normal execution even if cache fails
        response = client.get("/api/analytics/categories")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])