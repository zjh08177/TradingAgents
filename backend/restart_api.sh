#!/bin/bash

# TradingAgents API Restart Script
# This script kills all existing API processes and restarts the server cleanly

echo "🔄 TradingAgents API Restart Script"
echo "=================================="

# Function to kill processes by pattern
kill_processes() {
    local pattern=$1
    local description=$2
    
    echo "🔍 Looking for $description..."
    pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
    
    if [ -n "$pids" ]; then
        echo "💀 Killing $description: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        echo "✅ No $description found"
    fi
}

# Function to kill process on specific port
kill_port() {
    local port=$1
    echo "🔍 Looking for processes on port $port..."
    
    # Try lsof first
    if command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "💀 Killing processes on port $port: $pids"
            echo "$pids" | xargs kill -9 2>/dev/null || true
            sleep 1
        else
            echo "✅ No processes found on port $port"
        fi
    else
        echo "⚠️  lsof not available, skipping port check"
    fi
}

# Step 1: Kill all Python API processes
echo
echo "📋 Step 1: Killing existing API processes..."
kill_processes "run_api.py" "run_api.py processes"
kill_processes "uvicorn" "uvicorn processes"
kill_processes "TradingAgents" "TradingAgents processes"

# Step 2: Kill processes on port 8000
echo
echo "📋 Step 2: Killing processes on port 8000..."
kill_port 8000

# Step 3: Wait for cleanup
echo
echo "📋 Step 3: Waiting for cleanup..."
sleep 3

# Step 4: Verify port is free
echo
echo "📋 Step 4: Verifying port 8000 is free..."
if command -v lsof >/dev/null 2>&1; then
    if lsof -ti :8000 >/dev/null 2>&1; then
        echo "⚠️  Port 8000 is still in use. Trying force kill..."
        lsof -ti :8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
fi

# Step 5: Change to backend directory
echo
echo "📋 Step 5: Changing to backend directory..."
if [ ! -f "run_api.py" ]; then
    if [ -f "../backend/run_api.py" ]; then
        cd ../backend
        echo "✅ Changed to backend directory"
    elif [ -f "backend/run_api.py" ]; then
        cd backend
        echo "✅ Changed to backend directory"
    else
        echo "❌ Cannot find run_api.py. Please run this script from the project root or backend directory."
        exit 1
    fi
else
    echo "✅ Already in backend directory"
fi

# Step 6: Activate virtual environment
echo
echo "📋 Step 6: Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found. Continuing without activation..."
fi

# Step 7: Check if port is really free
echo
echo "📋 Step 7: Final port check..."
if command -v nc >/dev/null 2>&1; then
    if nc -z localhost 8000 2>/dev/null; then
        echo "❌ Port 8000 is still occupied!"
        echo "💡 Try running: sudo lsof -ti :8000 | xargs sudo kill -9"
        echo "💡 Or use a different port in the script"
        exit 1
    else
        echo "✅ Port 8000 is free"
    fi
fi

# Step 8: Start the API server
echo
echo "📋 Step 8: Starting TradingAgents API server..."
echo "🚀 Server will be available at http://localhost:8000"
echo "🚀 Server will be available at http://192.168.4.223:8000 (for iOS)"
echo "📚 API docs will be at http://localhost:8000/docs"
echo
echo "💡 Press Ctrl+C to stop the server"
echo "💡 Enhanced logging is active - you'll see detailed tool usage"
echo
echo "=================================="

# Start the server (not in background so we can see logs)
python run_api.py 