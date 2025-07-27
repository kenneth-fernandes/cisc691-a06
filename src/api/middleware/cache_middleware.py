"""
Caching middleware for automatic HTTP response caching
"""
import json
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

from api.utils.cache import cache_manager, cache_key_for_request

logger = logging.getLogger(__name__)


class CacheMiddleware:
    """Middleware for automatic HTTP response caching"""
    
    def __init__(
        self,
        app: Callable,
        default_ttl: int = 300,
        cache_get_requests: bool = True,
        cache_post_requests: bool = False,
        exclude_paths: list = None
    ):
        self.app = app
        self.default_ttl = default_ttl
        self.cache_get_requests = cache_get_requests
        self.cache_post_requests = cache_post_requests
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json",
            "/health", "/cache/", "/websocket"
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Check if we should cache this request
        if not self._should_cache_request(request):
            await self.app(scope, receive, send)
            return
        
        # Generate cache key
        cache_key = cache_key_for_request(request, "middleware")
        
        # Try to get cached response
        cached_response = cache_manager.get(cache_key)
        if cached_response and cache_manager.is_available():
            logger.info(f"Cache hit for {request.url.path}")
            
            # Send cached response
            response = JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response.get("headers", {})
            )
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Cache-Key"] = cache_key
            await response(scope, receive, send)
            return
        
        # Cache miss - execute request and cache response
        response_data = {
            "content": None,
            "status_code": 200,
            "headers": {}
        }
        
        async def cache_send(message):
            if message["type"] == "http.response.start":
                response_data["status_code"] = message["status"]
                response_data["headers"] = dict(message.get("headers", []))
            elif message["type"] == "http.response.body":
                if message.get("body"):
                    try:
                        # Try to parse as JSON for caching
                        body_str = message["body"].decode()
                        response_data["content"] = json.loads(body_str)
                        
                        # Cache successful responses
                        if 200 <= response_data["status_code"] < 300:
                            cache_manager.set(cache_key, response_data, self.default_ttl)
                            logger.info(f"Cached response for {request.url.path}")
                        
                        # Add cache headers
                        message["headers"] = [
                            (b"x-cache", b"MISS"),
                            (b"x-cache-key", cache_key.encode())
                        ] + list(message.get("headers", []))
                        
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Non-JSON responses are not cached
                        pass
            
            await send(message)
        
        await self.app(scope, receive, cache_send)
    
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached"""
        # Check HTTP method
        if request.method == "GET" and not self.cache_get_requests:
            return False
        if request.method == "POST" and not self.cache_post_requests:
            return False
        if request.method not in ["GET", "POST"]:
            return False
        
        # Check excluded paths
        path = request.url.path
        for exclude_path in self.exclude_paths:
            if exclude_path in path:
                return False
        
        # Check cache control headers
        cache_control = request.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True


def add_cache_headers_middleware():
    """Middleware to add cache-related headers to responses"""
    
    async def cache_headers_middleware(request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Add cache-related headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Cache-Status"] = response.headers.get("X-Cache", "MISS")
        
        # Add cache control headers for different endpoint types
        path = request.url.path
        if "/categories" in path or "/countries" in path:
            response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
        elif "/bulletins" in path:
            response.headers["Cache-Control"] = "public, max-age=1800"  # 30 minutes
        elif "/trends" in path or "/historical" in path:
            response.headers["Cache-Control"] = "public, max-age=300"   # 5 minutes
        else:
            response.headers["Cache-Control"] = "no-cache"
        
        return response
    
    return cache_headers_middleware


class CacheControlMiddleware:
    """Advanced cache control middleware with conditional caching"""
    
    def __init__(self, app: Callable):
        self.app = app
        self.cache_rules = {
            "/api/analytics/categories": {"ttl": 3600, "public": True},
            "/api/analytics/countries": {"ttl": 3600, "public": True},
            "/api/analytics/bulletins": {"ttl": 1800, "public": True},
            "/api/analytics/stats": {"ttl": 300, "public": False},
            "/api/analytics/historical": {"ttl": 600, "public": True},
            "/api/analytics/trends": {"ttl": 300, "public": True}
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        async def add_cache_headers(message):
            if message["type"] == "http.response.start":
                # Get cache rule for this path
                cache_rule = self._get_cache_rule(request.url.path)
                
                if cache_rule:
                    cache_control = []
                    if cache_rule["public"]:
                        cache_control.append("public")
                    else:
                        cache_control.append("private")
                    
                    cache_control.append(f"max-age={cache_rule['ttl']}")
                    
                    # Add cache control header
                    headers = list(message.get("headers", []))
                    headers.append((b"cache-control", ", ".join(cache_control).encode()))
                    message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, add_cache_headers)
    
    def _get_cache_rule(self, path: str) -> dict:
        """Get cache rule for given path"""
        for rule_path, rule_config in self.cache_rules.items():
            if path.startswith(rule_path):
                return rule_config
        return None