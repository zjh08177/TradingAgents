#!/bin/bash

# Quick Trading-Graph-Server Restart
# Minimal script for fast server restart

echo "🔄 Quick Server Restart..."

# Kill existing processes quickly
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "run_api.py" 2>/dev/null || true
pkill -f "api.py" 2>/dev/null || true

# Kill processes on port 8000
if command -v lsof >/dev/null 2>&1; then
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
fi

# Wait a moment
sleep 1

# Change to backend directory if needed
if [ ! -f "api.py" ] && [ -f "backend/api.py" ]; then
    cd backend
fi

# Activate venv if available
venv_paths=(
    "../.venv/bin/activate"
    ".venv/bin/activate" 
    "venv/bin/activate"
    "../venv/bin/activate"
    "../../.venv/bin/activate"
)

for venv_path in "${venv_paths[@]}"; do
    if [ -f "$venv_path" ]; then
        echo "Activating virtual environment at $venv_path..."
        source "$venv_path"
        break
    fi
done

echo "🚀 Starting server..."

# Start the server
if [ -f "run_api.py" ]; then
    exec python3 run_api.py
else
    exec python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
fi 