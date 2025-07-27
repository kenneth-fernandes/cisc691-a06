#!/usr/bin/env python3
"""
Script to install WebSocket dependencies if missing
"""
import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def check_and_install_websocket_deps():
    """Check and install WebSocket dependencies"""
    packages_to_install = []
    
    # Check websockets
    try:
        import websockets
        print("✅ websockets library is available")
    except ImportError:
        print("⚠️  websockets library not found")
        packages_to_install.append("websockets")
    
    # Check uvicorn[standard]
    try:
        import uvicorn
        import websockets  # This should be available with uvicorn[standard]
        print("✅ uvicorn with standard dependencies is available")
    except ImportError:
        print("⚠️  uvicorn[standard] not properly installed")
        packages_to_install.append("uvicorn[standard]")
    
    # Install missing packages
    if packages_to_install:
        print(f"\n📦 Installing missing packages: {', '.join(packages_to_install)}")
        for package in packages_to_install:
            install_package(package)
    else:
        print("\n🎉 All WebSocket dependencies are already installed!")

if __name__ == "__main__":
    check_and_install_websocket_deps()