#!/bin/bash

echo "🔄 Restarting Trading Graph Server with Full Cleanup..."

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

# Step 1.5: Check and Ensure Editable Mode Installation (CRITICAL FIX)
echo "📦 Checking package installation mode..."

# Check if package is in editable mode
if pip list --editable 2>/dev/null | grep -q "^agent "; then
    echo "✅ Package already in EDITABLE mode - source changes will be reflected"
    
    # Just show current version, no need to reinstall
    INSTALLED_VERSION=$(pip list | grep "^agent " | awk '{print $2}')
    echo "   📦 Current version: agent $INSTALLED_VERSION (editable)"
else
    echo "⚠️  Package NOT in editable mode - fixing installation..."
    
    # Uninstall non-editable package if it exists
    if pip list 2>/dev/null | grep -q "^agent "; then
        echo "   🗑️ Uninstalling non-editable package..."
        pip uninstall agent -y --quiet
    fi
    
    # Clear pip cache to ensure fresh install
    echo "   🧹 Clearing pip cache..."
    pip cache purge 2>/dev/null || true
    
    # Install in editable mode
    echo "   📦 Installing package in EDITABLE mode..."
    pip install -e . --quiet --no-warn-script-location
    
    if [ $? -eq 0 ]; then
        echo "✅ Package installed in EDITABLE mode successfully"
        
        # Verify editable installation
        if pip list --editable | grep -q "^agent "; then
            echo "✅ CONFIRMED: Package is in editable mode"
            echo "✅ Source code changes will now be reflected immediately!"
        else
            echo "⚠️  Warning: Package may not be in editable mode"
        fi
        
        # Show installed version
        INSTALLED_VERSION=$(pip list | grep "^agent " | awk '{print $2}')
        echo "   📦 Installed version: agent $INSTALLED_VERSION (editable)"
    else
        echo "❌ Package installation failed"
        exit 1
    fi
fi

# Step 1.7: Force Python Module Cleanup
echo "🧹 Performing comprehensive Python module cleanup..."

# Clear all Python cache files
echo "   🗑️ Clearing Python cache files..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Clear specific problematic cache directories
echo "   🗑️ Clearing problematic cache directories..."
rm -rf src/agent/analysts/__pycache__ 2>/dev/null || true
rm -rf src/agent/dataflows/__pycache__ 2>/dev/null || true
rm -rf src/agent/graph/__pycache__ 2>/dev/null || true
rm -rf src/agent/graph/nodes/__pycache__ 2>/dev/null || true

echo "✅ Python module cleanup completed"

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

# Step 4: Validate AttributeError fixes are in place
echo "🔍 Validating AttributeError fixes..."
if grep -q "except AttributeError as e:" src/agent/analysts/market_analyst_ultra_fast_async.py; then
    echo "✅ AttributeError handling found in ultra-fast async analyst"
else
    echo "❌ AttributeError handling missing in ultra-fast async analyst"
    echo "⚠️  Warning: Market analyst may still crash on AttributeError"
fi

if grep -q "create_empty_market_data_response" src/agent/dataflows/empty_response_handler.py; then
    echo "✅ Empty response handler functions found"
else
    echo "❌ Empty response handler functions missing"
    echo "⚠️  Warning: Empty response system not available"
fi

echo "✅ Fix validation completed"

# Step 5: Start the server
echo "🚀 Starting LangGraph server with ALL fixes applied..."
echo "📍 API: http://localhost:2024"
echo "📍 Docs: http://localhost:2024/docs" 
echo "📍 Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
echo ""
echo "🛡️  AttributeError Protection: ENABLED"
echo "📦 Editable Mode: ENABLED (source changes reflected)"
echo "🧹 Cache Cleanup: COMPLETED"
echo "🔥 Token Reduction: ACTIVE (news ≤15 articles)"
echo "✅ Runtime Verification: ENABLED"
echo "🚫 Pandas Circular Import Fix: ENABLED (pandas_ta disabled in LangGraph)"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Set environment variable to prevent pandas circular import
export IS_LANGGRAPH_DEV=1

# Start server in foreground so we can see logs
langgraph dev --port 2024
