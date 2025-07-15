#!/usr/bin/env python3
"""
Startup script for AI Financial Advisor
"""
import subprocess
import sys
import time
import os
import signal

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import reflex
        import httpx
        print("✅ All required dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements with:")
        print("  pip install -r requirements.txt")
        print("  cd frontend && pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment variables"""
    if not os.getenv('GROQ_API_KEY'):
        print("⚠️  GROQ_API_KEY not found in environment variables")
        print("Set it with: export GROQ_API_KEY='your-api-key'")
        print("The app will still run but AI analysis will not work")
    else:
        print("✅ GROQ_API_KEY found")

def find_process_on_port(port):
    """Find process ID running on a specific port"""
    try:
        # Use lsof to find process on port
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
    except Exception as e:
        print(f"⚠️  Error checking port {port}: {e}")
        return []

def stop_process_on_port(port):
    """Stop any process running on the specified port"""
    pids = find_process_on_port(port)
    if not pids:
        return True
    
    print(f"🔍 Found process(es) on port {port}: {', '.join(pids)}")
    
    for pid in pids:
        try:
            pid = int(pid.strip())
            print(f"🛑 Stopping process {pid} on port {port}...")
            
            # Try graceful termination first
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            
            # Check if process is still running
            try:
                os.kill(pid, 0)  # This will raise OSError if process doesn't exist
                print(f"⚠️  Process {pid} still running, forcing termination...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
            except OSError:
                # Process already terminated
                pass
                
            print(f"✅ Process {pid} stopped successfully")
            
        except (ValueError, OSError) as e:
            print(f"⚠️  Error stopping process {pid}: {e}")
            continue
    
    return True

def cleanup_ports():
    """Clean up any existing services on required ports"""
    print("🧹 Checking for existing services on required ports...")
    
    # Stop services on backend ports (8000 and 8001 in case of fallback)
    stop_process_on_port(8000)
    stop_process_on_port(8001)
    
    # Stop services on frontend port (3000)
    stop_process_on_port(3000)
    
    print("✅ Port cleanup completed")

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend on port 8000...")
    try:
        return subprocess.Popen([
            sys.executable, "app.py"
        ], cwd=".")
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the Reflex frontend"""
    print("🚀 Starting Reflex frontend on port 3000...")
    try:
        return subprocess.Popen([
            sys.executable, "-m", "reflex", "run"
        ], cwd="frontend")
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    print("🏦 AI Financial Advisor - Startup Script")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Clean up any existing services on required ports
    cleanup_ports()
    
    print("\n📋 Starting application components...")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    # Wait a moment for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(3)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)
    
    print("\n🎉 Application started successfully!")
    print("📍 Backend: http://localhost:8000")
    print("📍 Frontend: http://localhost:3000")
    print("📍 API Health: http://localhost:8000/health")
    print("\n💡 Note: If backend uses port 8001, check http://localhost:8001/health")
    print("💡 Press Ctrl+C to stop both servers")
    
    try:
        # Wait for user interrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Wait for processes to finish
        backend_process.wait()
        frontend_process.wait()
        
        print("✅ Servers stopped successfully")

if __name__ == "__main__":
    main() 
