#!/usr/bin/env python3
"""
Main entry point for Railway deployment
This file helps Railway detect this as a Python app and starts the FastAPI server
"""
import os
import sys

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# Change working directory to backend
os.chdir(backend_dir)

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from api import app
    
    # Get port from environment (Railway sets this)
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting TradingAgents API on {host}:{port}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    ) 