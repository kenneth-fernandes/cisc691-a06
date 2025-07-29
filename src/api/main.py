"""
FastAPI main application
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

# Import routers
from api.routers import agent, analytics, auth
from api.middleware.cache_middleware import add_cache_headers_middleware, CacheControlMiddleware
from utils.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting FastAPI backend server in Docker mode...")
    logger.info("📊 Database: PostgreSQL")
    logger.info("🔗 API: http://localhost:8000")
    logger.info("💻 Frontend: http://localhost:8501")
    logger.info("📖 API Docs: http://localhost:8000/docs")
    yield
    # Shutdown
    logger.info("🛑 Shutting down FastAPI backend server...")

# Create FastAPI application
app = FastAPI(
    title="AI Agent & Visa Analytics API",
    description="REST API for AI agent interactions and US visa bulletin analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],  # Streamlit and React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add caching middleware
app.add_middleware(CacheControlMiddleware)

# Add cache headers middleware
app.middleware("http")(add_cache_headers_middleware())

# Include routers
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# WebSocket router removed

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Agent & Visa Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running successfully"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )