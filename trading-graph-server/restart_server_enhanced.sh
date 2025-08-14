#!/bin/bash

# 🎯 Enhanced Trading Graph Server Restart with Auto-Execution
# Now supports automatic ticker execution after server startup
# Usage: ./restart_server_enhanced.sh [TICKER] [OPTIONS]
# Example: ./restart_server_enhanced.sh TSLA --auto-execute

set -e  # Exit on any error

# Parse command line arguments
TICKER=""
AUTO_EXECUTE=false
WAIT_TIME=10
SHOW_HELP=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        --auto-execute|-a)
            AUTO_EXECUTE=true
            shift
            ;;
        --wait|-w)
            WAIT_TIME="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            # If not a flag, assume it's the ticker
            if [[ -z "$TICKER" ]]; then
                TICKER="$1"
            else
                echo "Unknown option or multiple tickers provided: $1"
                SHOW_HELP=true
            fi
            shift
            ;;
    esac
done

if [[ "$SHOW_HELP" == "true" ]]; then
    echo "🎯 Enhanced Trading Graph Server Restart with Auto-Execution"
    echo ""
    echo "Usage: $0 [TICKER] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  TICKER                Stock ticker to analyze (e.g., TSLA, NVDA, AAPL)"
    echo "                        If provided, can be auto-executed after server startup"
    echo ""
    echo "Options:"
    echo "  --auto-execute, -a    Automatically execute analysis for ticker after startup"
    echo "  --wait, -w SECONDS    Wait time before auto-execution (default: 10)"
    echo "  --skip-tests          Skip preliminary tests during auto-execution"
    echo "  --help, -h            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Start server only"
    echo "  $0 TSLA                         # Start server, display TSLA execution command"
    echo "  $0 TSLA --auto-execute          # Start server and auto-execute TSLA analysis"
    echo "  $0 NVDA -a --wait 15            # Start server, wait 15s, then execute NVDA"
    echo "  $0 AAPL -a --skip-tests         # Start server and execute AAPL without tests"
    echo ""
    exit 0
fi

echo "🔄 Enhanced Trading Graph Server Restart with Auto-Execution..."
if [[ -n "$TICKER" ]]; then
    echo "🎯 Target Ticker: $TICKER"
    if [[ "$AUTO_EXECUTE" == "true" ]]; then
        echo "⚡ Auto-execution: ENABLED (wait: ${WAIT_TIME}s)"
    else
        echo "📋 Auto-execution: DISABLED (command will be displayed)"
    fi
fi
echo ""

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

# Step 4: Validate fixes are in place
echo "🔍 Validating system fixes..."

# Check async-compatible market analyst
if [ -f "src/agent/analysts/market_analyst_pandas_enabled.py" ]; then
    if grep -q "asyncio.to_thread" src/agent/analysts/market_analyst_pandas_enabled.py; then
        echo "✅ Async-compatible pandas market analyst found"
    else
        echo "⚠️  Market analyst may not be async-compatible"
    fi
else
    echo "❌ Market analyst file not found"
fi

# Check empty response handler
if grep -q "create_empty_market_data_response" src/agent/dataflows/empty_response_handler.py 2>/dev/null; then
    echo "✅ Empty response handler functions found"
else
    echo "⚠️  Warning: Empty response handler not available"
fi

echo "✅ Fix validation completed"

# Step 5: Create ticker execution script if needed
if [[ -n "$TICKER" ]]; then
    # Convert ticker to lowercase for script name
    TICKER_LOWER=$(echo "$TICKER" | tr '[:upper:]' '[:lower:]')
    EXECUTION_SCRIPT="execute_${TICKER_LOWER}_analysis.sh"
    
    echo "📝 Creating execution script: $EXECUTION_SCRIPT"
    
    cat > "$EXECUTION_SCRIPT" << EOF
#!/bin/bash
# Auto-generated execution script for $TICKER analysis
# Created by restart_server_enhanced.sh

echo "🎯 Executing Trading Graph Analysis for $TICKER"
echo "=========================================="

SCRIPT_FLAGS=""
if [[ "$SKIP_TESTS" == "true" ]]; then
    SCRIPT_FLAGS="--skip-tests"
fi

# Execute the analysis
echo "🚀 Running: ./debug_local.sh $TICKER \$SCRIPT_FLAGS"
./debug_local.sh $TICKER \$SCRIPT_FLAGS

echo ""
echo "✅ Analysis complete for $TICKER"
echo "📂 Check debug_logs/ for detailed results"
EOF

    chmod +x "$EXECUTION_SCRIPT"
    echo "✅ Execution script created and made executable"
fi

# Step 6: Start the server
echo ""
echo "🚀 Starting Enhanced LangGraph Server..."
echo "=========================================="
echo "📍 API: http://localhost:2024"
echo "📍 Docs: http://localhost:2024/docs" 
echo "📍 Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
echo ""
echo "🛡️  Enhancements Active:"
echo "   • Async-compatible pandas integration"
echo "   • AttributeError protection"
echo "   • Editable mode package installation"
echo "   • Comprehensive cache cleanup"
echo "   • Token optimization (news ≤15 articles)"
echo "   • Runtime verification enabled"
echo ""

if [[ -n "$TICKER" ]]; then
    echo "🎯 Ticker Analysis Ready:"
    echo "   • Target: $TICKER"
    if [[ "$AUTO_EXECUTE" == "true" ]]; then
        echo "   • Auto-execution: ENABLED (${WAIT_TIME}s wait)"
        echo "   • Script: ./$EXECUTION_SCRIPT"
    else
        echo "   • Manual execution: ./$EXECUTION_SCRIPT"
        echo "   • Quick command: ./debug_local.sh $TICKER"
    fi
    echo ""
fi

echo "Press Ctrl+C to stop the server"
echo "=========================================="

# Set environment variable to prevent pandas circular import
export IS_LANGGRAPH_DEV=1

# Function to run ticker analysis in background
run_ticker_analysis() {
    if [[ -n "$TICKER" && "$AUTO_EXECUTE" == "true" ]]; then
        echo ""
        echo "⏰ Waiting ${WAIT_TIME} seconds for server startup..."
        sleep "$WAIT_TIME"
        
        echo "🎯 Auto-executing analysis for $TICKER..."
        echo "=========================================="
        
        # Execute in a new terminal session or background
        if command -v gnome-terminal >/dev/null 2>&1; then
            gnome-terminal -- bash -c "./$EXECUTION_SCRIPT; read -p 'Press Enter to close...'"
        elif command -v osascript >/dev/null 2>&1; then
            # macOS Terminal
            osascript -e "tell application \"Terminal\" to do script \"cd '$(pwd)' && ./$EXECUTION_SCRIPT\""
        else
            # Fallback: run in background and show output
            echo "📱 Running analysis in background..."
            "./$EXECUTION_SCRIPT" &
            ANALYSIS_PID=$!
            echo "📊 Analysis PID: $ANALYSIS_PID"
            echo "📋 Use 'ps $ANALYSIS_PID' to check status"
        fi
        
        echo "✅ Auto-execution initiated for $TICKER"
        echo "📂 Monitor progress in debug_logs/"
    fi
}

# Start ticker analysis in background if enabled
if [[ "$AUTO_EXECUTE" == "true" ]]; then
    run_ticker_analysis &
fi

# Start server in foreground so we can see logs
langgraph dev --port 2024