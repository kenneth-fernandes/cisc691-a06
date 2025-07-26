#!/usr/bin/env python3
"""
Start the application in LOCAL mode
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Set environment for local mode
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
os.environ["DOCKER_MODE"] = "false"
os.environ["PYTHONPATH"] = str(src_path)

def start_api_server():
    """Start FastAPI server in background"""
    print("🚀 Starting FastAPI API server (local mode)...")
    return subprocess.Popen([
        sys.executable, "scripts/start_api.py"
    ], cwd=project_root)

def start_streamlit_app():
    """Start Streamlit frontend"""
    print("🌐 Starting Streamlit frontend (local mode)...")
    return subprocess.Popen([
        "streamlit", "run", "src/main.py",
        "--server.address", "localhost",
        "--server.port", "8501"
    ], cwd=project_root)

def main():
    """Main function to start both services"""
    print("🔧 Starting application in LOCAL mode...")
    print("📊 Database: SQLite")
    print("🌐 API: http://localhost:8000")
    print("💻 Frontend: http://localhost:8501")
    print("📖 API Docs: http://localhost:8000/docs")
    print("-" * 50)
    
    try:
        # Start API server
        api_process = start_api_server()
        
        # Wait for API to start
        print("⏳ Waiting for API server to start...")
        time.sleep(3)
        
        # Start Streamlit app
        streamlit_process = start_streamlit_app()
        
        print("✅ Both services started successfully!")
        print("Press Ctrl+C to stop all services")
        
        # Wait for user interrupt
        try:
            api_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            
            # Terminate processes
            if api_process.poll() is None:
                api_process.terminate()
            if streamlit_process.poll() is None:
                streamlit_process.terminate()
                
            print("✅ All services stopped")
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())