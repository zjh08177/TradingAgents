#!/usr/bin/env python
"""
Run the TradingAgents FastAPI server
"""
import uvicorn
from tradingagents.default_config import DEFAULT_CONFIG

if __name__ == "__main__":
    host = "0.0.0.0"  # Allow connections from any interface
    port = DEFAULT_CONFIG["api_port"]
    
    print(f"\n🚀 Starting TradingAgents API server...")
    print(f"📍 Server will be available at http://localhost:{port}")
    print(f"📚 API docs will be at http://localhost:{port}/docs\n")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )