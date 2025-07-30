#!/usr/bin/env python3
"""
Start the application in DOCKER mode
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """Start containerized application"""
    print("🚀 Starting AgentVisa application...")
    print("📊 Database: PostgreSQL")
    print("🔗 API: http://localhost:8000")
    print("💻 Frontend: http://localhost:8501")
    print("📖 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    try:
        # Change to docker directory (go up from scripts/ to project root, then to docker/)
        project_root = Path(__file__).parent.parent
        docker_dir = project_root / "docker"
        
        # Start docker compose
        result = subprocess.run([
            "docker-compose", "up", "--build"
        ], cwd=docker_dir)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Docker services...")
        subprocess.run([
            "docker-compose", "down"
        ], cwd=docker_dir)
        print("✅ Docker services stopped")
        return 0
        
    except Exception as e:
        print(f"❌ Error starting Docker services: {e}")
        return 1

if __name__ == "__main__":
    exit(main())