#!/usr/bin/env python3
"""
Start the FastAPI backend server
"""
import sys
import os
from pathlib import Path

# Add src to path (go up one level from scripts/ to project root, then to src/)
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import uvicorn
    
    # Set environment variables if not set
    os.environ.setdefault("PYTHONPATH", str(src_path))
    
    print("🚀 Starting FastAPI backend server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Interactive API: http://localhost:8000/redoc")
    print("📊 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )