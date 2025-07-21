#!/bin/bash

echo "🔄 Restarting Trading Graph Server..."

# Step 1: Kill all existing LangGraph processes
echo "🛑 Terminating existing LangGraph processes..."

# Kill langgraph dev processes
pkill -f "langgraph dev" 2>/dev/null || true

# Kill any uvicorn processes on port 2024
lsof -ti:2024 | xargs kill -9 2>/dev/null || true

# Kill any python processes related to langgraph
pkill -f "langgraph" 2>/dev/null || true

# Wait a moment for processes to clean up
sleep 2

echo "✅ All LangGraph processes terminated"

# Step 2: Check if port 2024 is free
echo "🔍 Checking port 2024..."
if lsof -Pi :2024 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 2024 still in use, forcing kill..."
    lsof -ti:2024 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Step 3: Verify environment
echo "🔑 Checking environment variables..."
if [ -f ".env" ]; then
    echo "✅ .env file found"
    
    # Check for API keys (without exposing them)
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo "✅ OpenAI API key configured"
    elif grep -q "GOOGLE_API_KEY=" .env && ! grep -q "your_google_key_here" .env; then
        echo "✅ Google API key configured"  
    else
        echo "⚠️  No valid API keys found in .env"
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

# Step 4: Start the server
echo "🚀 Starting LangGraph server..."
echo "📍 API: http://localhost:2024"
echo "📍 Docs: http://localhost:2024/docs"
echo "📍 Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Start server in foreground so we can see logs
langgraph dev --port 2024
