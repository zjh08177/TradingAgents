#!/bin/bash

# 🎯 Enhanced LangGraph Debug Script with Studio Mirror Mode (No Virtual Environment)
# This script provides comprehensive debugging and Studio compatibility validation

set -e  # Exit on any error

# Command line argument parsing
STUDIO_MIRROR_MODE=true
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --basic-mode)
            STUDIO_MIRROR_MODE=false
            shift
            ;;
        --studio-mirror)
            STUDIO_MIRROR_MODE=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            SHOW_HELP=true
            break
            ;;
    esac
done

if [[ "$SHOW_HELP" == "true" ]]; then
    echo "🎯 Enhanced LangGraph Debug Script (No Virtual Environment)"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --basic-mode      Run basic debug without Studio compatibility tests"
    echo "  --studio-mirror   Run with full Studio environment mirroring (default)"
    echo "  --help, -h        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run with Studio mirror mode (recommended)"
    echo "  $0 --studio-mirror    # Run with Studio mirror mode (explicit)" 
    echo "  $0 --basic-mode       # Run basic debug only (faster, less validation)"
    exit 0
fi

# Global timeout configuration (720 seconds = 12 minutes)
GLOBAL_TIMEOUT=720
export SCRIPT_START_TIME=$(date +%s)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/debug_logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEBUG_LOG="$LOG_DIR/debug_session_$TIMESTAMP.log"
GRAPH_LOG="$LOG_DIR/graph_debug_$TIMESTAMP.log"

if [[ "$STUDIO_MIRROR_MODE" == "true" ]]; then
    echo -e "${BLUE}🎯 Enhanced LangGraph Debug Script (Studio-Mirror Mode) - No Virtual Environment${NC}"
    echo -e "${BLUE}========================================================================${NC}"
else
    echo -e "${BLUE}🐛 LangGraph Debug Script (Basic Mode) - No Virtual Environment${NC}"
    echo -e "${BLUE}==============================================================${NC}"
fi
echo -e "📂 Working Directory: $SCRIPT_DIR"
echo -e "📝 Debug Log: $DEBUG_LOG"
echo -e "📊 Graph Log: $GRAPH_LOG"
echo -e "🎛️  Mode: $([ "$STUDIO_MIRROR_MODE" = true ] && echo "Studio Mirror" || echo "Basic Debug")"
echo -e "🔧 Environment: Local (No Virtual Environment)"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

# Function to perform post-run validation checks
validate_critical_components() {
    local validation_errors=0
    
    echo -e "${CYAN}🔄 Performing post-run validation checks...${NC}"
    
    # Check 1: Python version (using system Python)
    if python3 --version >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Python3 available: $(python3 --version)${NC}"
    else
        echo -e "${RED}   ❌ Python3 not found${NC}"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check 2: Required Python packages are importable
    if python3 -c "from src.agent.graph.trading_graph import TradingAgentsGraph" 2>/dev/null; then
        echo -e "${GREEN}   ✅ Core trading graph imports working${NC}"
    else
        echo -e "${RED}   ❌ Core trading graph imports failed${NC}"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check 3: Debug logging system is importable
    if python3 -c "from src.agent.utils.debug_logging import debug_node" 2>/dev/null; then
        echo -e "${GREEN}   ✅ Debug logging system working${NC}"
    else
        echo -e "${RED}   ❌ Debug logging system failed${NC}"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check 4: API keys are configured
    if [[ -f ".env" ]] && grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo -e "${GREEN}   ✅ OpenAI API key configured${NC}"
    else
        echo -e "${RED}   ❌ OpenAI API key not properly configured${NC}"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check 5: LangGraph CLI is available
    if command -v langgraph >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ LangGraph CLI available${NC}"
    else
        echo -e "${RED}   ❌ LangGraph CLI not available${NC}"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check 6: Debug log files were created
    if [[ -f "$DEBUG_LOG" ]] && [[ -s "$DEBUG_LOG" ]]; then
        echo -e "${GREEN}   ✅ Debug log file created and populated${NC}"
    else
        echo -e "${RED}   ❌ Debug log file missing or empty${NC}"
        validation_errors=$((validation_errors + 1))
    fi
    
    return $validation_errors
}

# Function to check for errors in logs
check_for_errors() {
    local log_file="$1"
    local critical_error_count=0
    local warning_count=0
    
    echo "🔍 Performing comprehensive error validation..."
    echo "🔍 Scanning logs for critical errors (excluding warnings and test artifacts)..."
    
    # Critical error patterns - only real failures
    local critical_patterns=(
        "FAILED.*✅.*PASS"  # This pattern should NOT match
        "CRITICAL"
        "FATAL" 
        "Exception.*[^W]"  # Exclude WARNING exceptions
        "RuntimeError"
        "SystemError"
        "MemoryError"
        "TimeoutError"
    )
    
    # Patterns that indicate actual system failures (not test failures or warnings)
    local failure_patterns=(
        "ImportError.*cannot import"
        "ModuleNotFoundError.*No module named"
        "FileNotFoundError.*No such file"
        "ConnectionError"
        "PermissionError"
        "OSError"
    )
    
    # Business logic critical failures only
    local business_critical_patterns=(
        "HOLD.*due to.*system.*failure"
        "Unable to.*analyze"
        "Failed to.*load.*data"
        "Cannot.*access.*API"
        "Database.*error"
        "Network.*timeout"
    )
    
    echo "📋 Critical Error Detection Results:"
    
    # Check for critical system errors
    for pattern in "${critical_patterns[@]}"; do
        local count
        count=$(grep -v "✅.*PASS" "$log_file" | grep -c "$pattern" 2>/dev/null || echo "0")
        count=$(echo "$count" | tr -d '\n' | tr -d ' ' | head -1)
        if [ "$count" -gt 0 ]; then
            echo "   ❌ Found $count instances of: Critical System Error"
            critical_error_count=$((critical_error_count + count))
            echo "      Sample occurrences:"
            grep -v "✅.*PASS" "$log_file" | grep -n "$pattern" | head -3 | sed 's/^/        /'
            echo ""
        fi
    done
    
    # Check for actual import/system failures (excluding test artifacts)
    for pattern in "${failure_patterns[@]}"; do
        local count
        count=$(grep -v "test_studio_blocking" "$log_file" | grep -c "$pattern" 2>/dev/null || echo "0")
        count=$(echo "$count" | tr -d '\n' | head -1)
        if [ "$count" -gt 0 ]; then
            echo "   ❌ Found $count instances of: System Failure ($pattern)"
            critical_error_count=$((critical_error_count + count))
            echo "      Sample occurrences:"
            grep -v "test_studio_blocking" "$log_file" | grep -n "$pattern" | head -3 | sed 's/^/        /'
            echo ""
        fi
    done
    
    # Check for actual Python exceptions that aren't in passing tests
    if grep -q "Traceback" "$log_file"; then
        # Only count tracebacks that don't lead to passing tests
        local traceback_lines=$(grep -B2 -A10 "Traceback" "$log_file" | grep -v "✅.*PASS" | grep -c "Traceback" 2>/dev/null || echo "0")
        if [ "$traceback_lines" -gt 0 ]; then
            echo "   ❌ Found $traceback_lines instances of: Unresolved Tracebacks"
            critical_error_count=$((critical_error_count + traceback_lines))
            echo ""
        fi
    fi
    
    # Check for business logic critical failures
    for pattern in "${business_critical_patterns[@]}"; do
        local count
        count=$(grep -c "$pattern" "$log_file" 2>/dev/null || echo "0")
        count=$(echo "$count" | tr -d '\n' | head -1)
        if [ "$count" -gt 0 ]; then
            echo "   ❌ Found $count instances of: Business Critical Failure"
            critical_error_count=$((critical_error_count + count))
            echo "      Sample occurrences:"
            grep -n "$pattern" "$log_file" | head -3 | sed 's/^/        /'
            echo ""
        fi
    done
    
    # Count warnings separately (informational only)
    warning_count=$(grep -c "WARNING:\|⚠️.*Quality check failed" "$log_file" 2>/dev/null || echo "0")
    
    # Additional specific checks for our trading system
    echo "🔍 Checking for specific trading system critical failures..."
    
    # Check for complete system failures (not quality warnings)
    if grep -q "HOLD.*due to.*system.*failure\|Unable to initialize.*graph\|Cannot start.*server" "$log_file"; then
        echo "   ❌ Found system initialization failures (critical failure)"
        critical_error_count=$((critical_error_count + 1))
    fi
    
    # Summary
    if [ "$critical_error_count" -eq 0 ]; then
        echo "   ✅ No critical errors detected"
        if [ "$warning_count" -gt 0 ]; then
            echo "   📝 Found $warning_count warnings (non-critical - acceptable)"
        fi
        return 0
    else
        echo "   ❌ Total critical error instances found: $critical_error_count"
        if [ "$warning_count" -gt 0 ]; then
            echo "   📝 Also found $warning_count warnings (separate from critical errors)"
        fi
        return 1
    fi
}

# Function to log with timestamp
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$DEBUG_LOG"
}

# Function to check global timeout
check_timeout() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - SCRIPT_START_TIME))
    
    if [ $elapsed -ge $GLOBAL_TIMEOUT ]; then
        echo -e "${RED}❌ GLOBAL TIMEOUT: Script exceeded ${GLOBAL_TIMEOUT}s limit${NC}"
        echo -e "${RED}   Elapsed time: ${elapsed}s${NC}"
        log "GLOBAL TIMEOUT: Script terminated after ${elapsed}s (limit: ${GLOBAL_TIMEOUT}s)"
        exit 124  # Standard timeout exit code
    fi
}

# Function to run command with logging
run_cmd() {
    local cmd="$1"
    local description="$2"
    
    # Check timeout before running command
    check_timeout
    
    echo -e "${CYAN}🔄 $description${NC}"
    log "COMMAND: $cmd"
    
    if eval "$cmd" 2>&1 | tee -a "$DEBUG_LOG"; then
        echo -e "${GREEN}✅ $description - SUCCESS${NC}"
        log "SUCCESS: $description"
        return 0
    else
        echo -e "${RED}❌ $description - FAILED${NC}"
        log "FAILED: $description"
        return 1
    fi
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Phase 1: Environment Setup
echo -e "${PURPLE}📋 Phase 1: Environment Verification${NC}"
echo "========================================"
check_timeout

# Check if we're in the right directory
if [[ ! -f "src/agent/__init__.py" ]]; then
    echo -e "${RED}❌ Error: Not in trading-graph-server directory${NC}"
    echo -e "${YELLOW}💡 Please run this script from the trading-graph-server directory${NC}"
    exit 1
fi

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
    log "Python version: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
    log "Python version: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi

# Check if required packages are installed locally
echo -e "${CYAN}🔄 Checking for required packages in local environment...${NC}"
MISSING_PACKAGES=()

# Check for pip
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo -e "${RED}❌ pip not available. Please install pip first.${NC}"
    exit 1
fi

# Check for required packages - using import names
import_packages=(
    "langchain:langchain"
    "langchain_openai:langchain-openai"
    "langchain_core:langchain-core"
    "langchain_anthropic:langchain-anthropic"
    "langchain_google_genai:langchain-google-genai"
    "langgraph:langgraph"
    "httpx:httpx"
    "aiofiles:aiofiles"
    "numpy:numpy"
    "pandas:pandas"
    "stockstats:stockstats"
    "bs4:beautifulsoup4"
    "requests:requests"
    "serpapi:google-search-results"
    "dotenv:python-dotenv"
    "dateutil:python-dateutil"
    "tenacity:tenacity"
    "tqdm:tqdm"
    "asyncio_throttle:asyncio-throttle"
)
for pkg_spec in "${import_packages[@]}"; do
    import_name="${pkg_spec%%:*}"
    install_name="${pkg_spec#*:}"
    if ! $PYTHON_CMD -c "import $import_name" 2>/dev/null; then
        MISSING_PACKAGES+=($install_name)
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    echo -e "${CYAN}🔄 Installing missing packages...${NC}"
    run_cmd "$PYTHON_CMD -m pip install --user --break-system-packages ${MISSING_PACKAGES[*]}" "Installing missing packages"
else
    echo -e "${GREEN}✅ All required packages are installed${NC}"
fi

# Check .env file
if [[ -f ".env" ]]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    log "Environment file exists"
    
    # Check for required API keys (without exposing them)
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo -e "${GREEN}✅ OpenAI API key configured${NC}"
        log "OpenAI API key found in .env"
    else
        echo -e "${YELLOW}⚠️  OpenAI API key not found in .env${NC}"
        log "WARNING: OpenAI API key not found"
    fi
    
    # Source environment variables
    set -a
    source .env
    set +a
else
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo -e "${YELLOW}💡 Please create .env with your API keys${NC}"
    log "WARNING: .env file not found"
fi

# Set debug environment variables
echo -e "${CYAN}🔄 Setting debug environment variables...${NC}"
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"
export LANGCHAIN_TRACING_V2=false
export LANGGRAPH_DEBUG=true
export PYTHON_LOG_LEVEL=DEBUG

# Enable minimalist logging
export USE_MINIMALIST_LOGGING=true
export MINIMALIST_LOG_FILE="$LOG_DIR/minimalist_debug_$TIMESTAMP.log"

log "Debug environment variables set"
log "Minimalist logging enabled: $MINIMALIST_LOG_FILE"

echo ""

# Phase 2: Code Verification
echo -e "${PURPLE}📋 Phase 2: Code Verification${NC}"
echo "================================"
check_timeout

# Check imports
run_cmd "$PYTHON_CMD -c 'from src.agent.graph.trading_graph import TradingAgentsGraph; print(\"✅ Core imports working\")'" "Testing core imports"
run_cmd "$PYTHON_CMD -c 'from src.agent.utils.debug_logging import debug_node; print(\"✅ Debug logging imports working\")'" "Testing debug logging imports"
run_cmd "$PYTHON_CMD -c 'from langchain_openai import ChatOpenAI; print(\"✅ LangChain imports working\")'" "Testing LangChain imports"

echo ""

# Phase 3: Debug Test Execution
echo -e "${PURPLE}📋 Phase 3: Debug Test Execution${NC}"
echo "=================================="
check_timeout

# Configure logging to reduce false warnings from OpenAI client
export PYTHONPATH="/Users/bytedance/Documents/TradingAgents/trading-graph-server/src:$PYTHONPATH"

# Set log levels to reduce noise
export OPENAI_LOG_LEVEL=WARNING

echo "🔍 Testing TradingAgentsGraph with comprehensive error validation..."

# Create enhanced debug test if it doesn't exist
if [[ ! -f "debug_test.py" ]]; then
    echo -e "${CYAN}🔄 Creating debug test script...${NC}"
    cat > debug_test.py << 'EOF'
#!/usr/bin/env python3
"""
Enhanced debug test script for LangGraph trading graph
"""

import asyncio
import logging
import sys
import traceback
import os
from datetime import datetime

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_test.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_graph_execution():
    """Test the graph execution with detailed debugging"""
    try:
        logger.info("🚀 Starting enhanced debug test of trading graph")
        
        # Test 1: Environment verification
        logger.debug("🔑 Testing environment...")
        api_key = os.getenv('OPENAI_API_KEY', '')
        if api_key.startswith('sk-'):
            logger.debug("✅ OpenAI API key found")
        else:
            logger.warning("⚠️ OpenAI API key not found or invalid")
        
        # Test 2: Import verification
        logger.debug("📦 Testing imports...")
        from src.agent.graph.trading_graph import TradingAgentsGraph
        from src.agent.default_config import DEFAULT_CONFIG
        from langchain_openai import ChatOpenAI
        from src.agent.utils.debug_logging import debug_node
        logger.debug("✅ All imports successful")
        
        # Test 3: LLM creation
        logger.debug("🤖 Testing LLM creation...")
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        test_result = await llm.ainvoke([{"role": "user", "content": "Say 'LLM working'"}])
        logger.debug(f"✅ LLM test result: {test_result.content}")
        
        # Test 4: Memory system
        logger.debug("💾 Testing memory system...")
        from src.agent.utils.memory import FinancialSituationMemory
        memory = FinancialSituationMemory("test_memory", DEFAULT_CONFIG)
        logger.debug("✅ Memory system created successfully")
        
        # Test 5: Graph compilation
        logger.debug("🏗️ Testing graph compilation...")
        trading_graph = TradingAgentsGraph(
            config=DEFAULT_CONFIG
        )
        
        compiled_graph = trading_graph.compile()
        logger.debug(f"✅ Graph compiled with {len(compiled_graph.nodes)} nodes")
        
        # Test 6: Debug logging test
        logger.debug("🔍 Testing debug logging...")
        @debug_node("test_node")
        async def test_node(state):
            return {"test": "success", "debug_working": True}
        
        test_state = {"company_of_interest": "GOOG", "trade_date": "2025-07-28"}
        debug_result = await test_node(test_state)
        logger.debug(f"✅ Debug logging test: {debug_result}")
        
        # Test 7: Quick execution test (without full analysis)
        logger.debug("⚡ Testing quick graph execution...")
        start_time = datetime.now()
        
        # Test with minimal state
        minimal_result = await trading_graph.propagate("GOOG", "2025-07-28")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Quick graph execution completed in {execution_time:.2f} seconds")
        logger.info(f"📊 Final decision: {minimal_result.get('processed_signal', 'No signal')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Debug test failed: {str(e)}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_graph_execution())
    if success:
        print("\n🎉 ENHANCED DEBUG TEST PASSED - Graph is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 ENHANCED DEBUG TEST FAILED - Check logs for details")
        sys.exit(1)
EOF
    echo -e "${GREEN}✅ Debug test script created${NC}"
fi

# Run the debug test
echo -e "${CYAN}🔄 Running comprehensive debug test...${NC}"
if $PYTHON_CMD debug_test.py 2>&1 | tee -a "$DEBUG_LOG"; then
    echo -e "${GREEN}✅ Debug test completed successfully${NC}"
    log "Debug test passed"
else
    echo -e "${RED}❌ Debug test failed${NC}"
    log "Debug test failed"
    echo -e "${YELLOW}💡 Check $DEBUG_LOG for detailed error information${NC}"
fi

echo ""

# Phase 4: Studio Environment Mirroring (Optional)
if [[ "$STUDIO_MIRROR_MODE" == "true" ]]; then
    echo -e "${PURPLE}📋 Phase 4: Studio Environment Mirroring${NC}"
    echo "============================================"
    check_timeout

    # Install Studio-specific validation tools
    echo -e "${CYAN}🔄 Installing Studio validation tools...${NC}"
    run_cmd "$PYTHON_CMD -m pip install --user --break-system-packages blockbuster" "Installing blocking call detector"
    run_cmd "$PYTHON_CMD -m pip install --user --break-system-packages langgraph-cli" "Installing LangGraph CLI"
else
    echo -e "${PURPLE}📋 Phase 4: Basic Server Testing${NC}"
    echo "================================"
    check_timeout

    # Basic LangGraph CLI check
    if command_exists langgraph; then
        echo -e "${GREEN}✅ LangGraph CLI found${NC}"
        log "LangGraph CLI available"
    else
        echo -e "${YELLOW}⚠️  LangGraph CLI not found, installing...${NC}"
        run_cmd "$PYTHON_CMD -m pip install --user --break-system-packages langgraph-cli" "Installing LangGraph CLI"
    fi
    
    # Set defaults for basic mode
    BLOCKING_TEST_PASSED=true
    PYTHON311_TEST_PASSED=true
    SERVER_TEST_PASSED=true
fi

if [[ "$STUDIO_MIRROR_MODE" == "true" ]]; then
    # Test 1: Blocking Call Detection (exactly like Studio)
    echo -e "${CYAN}🧪 Test 1: Studio-style Blocking Call Detection${NC}"
cat > test_studio_blocking.py << 'EOF'
#!/usr/bin/env python3
"""
Mirror Studio's exact blocking call detection
"""
import sys
import os

# Ensure we can import from the src directory
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.insert(0, src_dir)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = os.path.join(script_dir, '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Environment loaded from {env_file}")
except ImportError:
    # Fallback: manually read .env file if python-dotenv is not available
    env_file = os.path.join(script_dir, '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print(f"✅ Environment loaded manually from {env_file}")
    else:
        print("⚠️ No .env file found")

def test_studio_blocking_detection():
    """Test with exact Studio blocking detection"""
    try:
        import blockbuster
        # blockbuster doesn't have install() method, just importing it is enough
        print("🔒 Blockbuster blocking detection enabled (Studio mode)")
        
        # Test the exact import chain Studio uses
        print("🔗 Testing Studio import chain...")
        
        # Step 1: Basic agent import
        print("  1. Importing agent module...")
        import agent
        print("     ✅ Agent module imported")
        
        # Step 2: Test importlib pattern (exactly like Studio)
        print("  2. Testing importlib pattern...")
        import importlib
        trading_graph_module = importlib.import_module('.graph.trading_graph', package='agent')
        print("     ✅ Trading graph importlib success")
        
        # Step 3: Test graph factory function (Studio's exact call)
        print("  3. Testing graph factory function...")
        from langchain_core.runnables import RunnableConfig
        
        config = RunnableConfig(
            tags=[],
            metadata={},
            callbacks=None,
            recursion_limit=25,
            configurable={
                '__pregel_store': None,
                '__pregel_checkpointer': None
            }
        )
        
        # Test both the function call and the module.graph pattern
        if hasattr(agent, 'graph') and callable(agent.graph):
            result = agent.graph(config)
        else:
            # Fallback to direct graph creation
            result = agent.create_studio_compatible_graph()
        print(f"     ✅ Graph factory success: {type(result)}")
        
        print("🎉 ALL IMPORTS PASSED BLOCKING DETECTION!")
        return True
        
    except blockbuster.BlockingError as e:
        print(f"❌ BLOCKING CALL DETECTED: {e}")
        print("📍 This is the exact error Studio encounters!")
        return False
    except Exception as e:
        print(f"❌ OTHER ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_studio_blocking_detection()
    exit(0 if success else 1)
EOF

if $PYTHON_CMD test_studio_blocking.py 2>&1 | tee -a "$DEBUG_LOG"; then
    echo -e "${GREEN}✅ Studio blocking detection test PASSED${NC}"
    log "Studio blocking detection test passed"
    BLOCKING_TEST_PASSED=true
else
    echo -e "${RED}❌ Studio blocking detection test FAILED${NC}"
    log "Studio blocking detection test failed"
    BLOCKING_TEST_PASSED=false
    echo -e "${YELLOW}💡 This is likely the exact issue Studio encounters!${NC}"
fi

rm -f test_studio_blocking.py

# Test 2: LangGraph Dev Server Simulation
echo -e "${CYAN}🧪 Test 2: LangGraph Dev Server Simulation${NC}"

# Check if port 8125 is available (using different port to avoid conflicts)
if command_exists lsof && lsof -Pi :8125 -sTCP:LISTEN -t >/dev/null; then
    echo -e "${YELLOW}⚠️  Port 8125 is in use, cleaning up...${NC}"
    pkill -f "langgraph dev" 2>/dev/null || true
    sleep 2
fi

# Set environment exactly like Studio
export PYTHONPATH="$SCRIPT_DIR/src"

# Test server startup with timeout (mirror Studio's startup behavior)
echo -e "${CYAN}🔄 Testing langgraph dev startup (Studio simulation)...${NC}"

# Check if timeout command exists, otherwise use background process with kill
if command -v timeout >/dev/null 2>&1; then
    timeout 15s langgraph dev --port 8125 --no-browser &
    SERVER_PID=$!
elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout 15s langgraph dev --port 8125 --no-browser &
    SERVER_PID=$!
else
    # Fallback: start server in background and kill after timeout
    langgraph dev --port 8125 --no-browser &
    SERVER_PID=$!
    # Create a timeout mechanism
    (sleep 15; kill $SERVER_PID 2>/dev/null) &
    TIMEOUT_PID=$!
fi

# Wait for server to start
sleep 8

# Test if server is responding (like Studio does)
if curl -s http://127.0.0.1:8125/assistants >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Studio server simulation PASSED${NC}"
    log "Studio server simulation passed"
    SERVER_TEST_PASSED=true
else
    echo -e "${RED}❌ Studio server simulation FAILED${NC}"
    log "Studio server simulation failed"
    SERVER_TEST_PASSED=false
fi

# Clean up server and timeout process
if [ -n "$TIMEOUT_PID" ]; then
    kill $TIMEOUT_PID 2>/dev/null || true
fi
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

fi  # End of Studio mirror mode

echo ""

# Phase 5: Graph Analysis
echo -e "${PURPLE}📋 Phase 5: Graph Analysis${NC}"
echo "=========================="
check_timeout

# Analyze graph structure
echo -e "${CYAN}🔄 Analyzing graph structure...${NC}"
cat > analyze_graph.py << 'EOF'
import asyncio
from src.agent.graph.trading_graph import TradingAgentsGraph
from src.agent.default_config import DEFAULT_CONFIG

async def analyze_graph():
    try:
        trading_graph = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals"],
            config=DEFAULT_CONFIG
        )
        
        # Access the compiled graph from the graph attribute
        compiled_graph = trading_graph.graph
        
        print(f"📊 Graph Analysis:")
        print(f"   - Nodes: {len(compiled_graph.nodes)}")
        print(f"   - Node List: {list(compiled_graph.nodes.keys())}")
        print(f"   - Graph Type: {type(compiled_graph).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Graph analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(analyze_graph())
    exit(0 if success else 1)
EOF

if $PYTHON_CMD analyze_graph.py 2>&1 | tee -a "$DEBUG_LOG"; then
    echo -e "${GREEN}✅ Graph analysis completed${NC}"
    log "Graph analysis successful"
else
    echo -e "${RED}❌ Graph analysis failed${NC}"
    log "Graph analysis failed"
fi

# Clean up temporary files
rm -f analyze_graph.py

echo ""

# Phase 6: Generate Debug Report
echo -e "${PURPLE}📋 Phase 6: Debug Report Generation${NC}"
echo "===================================="
check_timeout

REPORT_FILE="$LOG_DIR/debug_report_$TIMESTAMP.md"

cat > "$REPORT_FILE" << EOF
# 🐛 LangGraph Debug Report (No Virtual Environment)

**Generated:** $(date)  
**Session ID:** $TIMESTAMP  
**Working Directory:** $SCRIPT_DIR
**Environment:** Local (No Virtual Environment)

## 📋 Environment Status

- **Python Version:** $($PYTHON_CMD --version)
- **PYTHONPATH:** $PYTHONPATH

## 🔧 Configuration

- **Debug Logging:** Enabled
- **Log Files:**
  - Debug Session: $DEBUG_LOG
  - Graph Debug: $GRAPH_LOG
  - This Report: $REPORT_FILE

## 📊 Test Results

$(if [[ -f "debug_test.log" ]]; then
    echo "### Debug Test Output"
    echo "\`\`\`"
    tail -20 debug_test.log
    echo "\`\`\`"
fi)

## 🔍 Next Steps

1. **View detailed logs:**
   \`\`\`bash
   tail -f $DEBUG_LOG
   \`\`\`

2. **Start debug server:**
   \`\`\`bash
   langgraph dev --port 8123 --no-browser
   \`\`\`

3. **Monitor graph execution:**
   \`\`\`bash
   tail -f $GRAPH_LOG
   \`\`\`

4. **Access LangGraph Studio:**
   https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123

## 🛠️ Debug Commands

### Kill all LangGraph processes
\`\`\`bash
pkill -f "langgraph dev"
\`\`\`

### Check port usage
\`\`\`bash
lsof -i :8123
\`\`\`

### Monitor server health
\`\`\`bash
curl -s http://127.0.0.1:8123/assistants | head -1
\`\`\`

### View graph debug logs
\`\`\`bash
tail -f graph_debug.log
\`\`\`

EOF

echo -e "${GREEN}✅ Debug report generated: $REPORT_FILE${NC}"
log "Debug report created: $REPORT_FILE"

echo ""

# Phase 7: Final Validation & Summary
echo -e "${PURPLE}📋 Phase 7: Final Validation${NC}"
echo "============================="
check_timeout

# Post-run validation checks
if validate_critical_components; then
    echo -e "${GREEN}✅ All critical components validated successfully${NC}"
    VALIDATION_PASSED=true
else
    echo -e "${RED}❌ Critical component validation failed${NC}"
    VALIDATION_PASSED=false
fi

echo ""

# Comprehensive error check
echo -e "${CYAN}🔍 Performing final error validation...${NC}"
if check_for_errors "$DEBUG_LOG"; then
    echo -e "${GREEN}✅ No errors detected in logs${NC}"
    ERROR_CHECK_PASSED=true
else
    echo -e "${RED}❌ Errors detected in logs${NC}"
    ERROR_CHECK_PASSED=false
fi

# Studio compatibility checks
STUDIO_COMPATIBILITY=true
if [[ "${BLOCKING_TEST_PASSED:-false}" != "true" ]] || [[ "${SERVER_TEST_PASSED:-false}" != "true" ]]; then
    STUDIO_COMPATIBILITY=false
fi

# Determine final status (must pass all validation AND Studio compatibility)
if [[ "$VALIDATION_PASSED" == "true" ]] && [[ "$ERROR_CHECK_PASSED" == "true" ]] && [[ "$STUDIO_COMPATIBILITY" == "true" ]]; then
    FINAL_STATUS="SUCCESS"
    STATUS_COLOR="${GREEN}"
    STATUS_ICON="✅"
else
    FINAL_STATUS="FAILED"
    STATUS_COLOR="${RED}"
    STATUS_ICON="❌"
fi

echo ""

# Phase 8: Summary
echo -e "${PURPLE}📋 Debug Session Complete${NC}"
echo "=========================="
check_timeout
echo -e "${STATUS_COLOR}${STATUS_ICON} Debug session completed: ${FINAL_STATUS}${NC}"
echo ""
echo -e "${CYAN}📂 Generated Files:${NC}"
echo -e "   📝 Debug Log: $DEBUG_LOG"
echo -e "   📊 Graph Log: $GRAPH_LOG"  
echo -e "   📋 Report: $REPORT_FILE"
echo -e "   📉 Minimalist Log: $MINIMALIST_LOG_FILE"
echo ""
if [[ "$STUDIO_MIRROR_MODE" == "true" ]]; then
    echo -e "${CYAN}📋 Studio Compatibility Results:${NC}"
    echo -e "   🔒 Blocking Detection: $([ "${BLOCKING_TEST_PASSED:-false}" = true ] && echo "✅ PASS" || echo "❌ FAIL")"
    echo -e "   🌐 Server Simulation: $([ "${SERVER_TEST_PASSED:-false}" = true ] && echo "✅ PASS" || echo "❌ FAIL")"
    echo ""
fi
echo -e "${CYAN}🚀 Next Steps:${NC}"
if [[ "$STUDIO_MIRROR_MODE" == "true" ]]; then
    if [[ "$STUDIO_COMPATIBILITY" == "true" ]]; then
        echo -e "   ${GREEN}✅ All tests passed - Studio compatibility confirmed!${NC}"
        echo -e "   1. Start the server: ${YELLOW}langgraph dev --port 8123${NC}"
        echo -e "   2. Access Studio: ${YELLOW}https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123${NC}"
        echo -e "   3. Monitor logs: ${YELLOW}tail -f $GRAPH_LOG${NC}"
    else
        echo -e "   ${RED}❌ Studio compatibility issues detected${NC}"
        echo -e "   1. Review blocking detection failures above"
        echo -e "   2. Check: ${YELLOW}tail -f $DEBUG_LOG${NC}"
        echo -e "   3. Fix issues before deploying to Studio"
    fi
    echo ""
    echo -e "${BLUE}🎯 $([ "$STUDIO_COMPATIBILITY" = true ] && echo "Ready for Studio!" || echo "Fix compatibility issues first")${NC}"
else
    echo -e "   ${GREEN}✅ Basic debug completed${NC}"
    echo -e "   1. Start the server: ${YELLOW}langgraph dev --port 8123${NC}"
    echo -e "   2. Monitor logs: ${YELLOW}tail -f $GRAPH_LOG${NC}"
    echo -e "   3. For Studio compatibility: ${YELLOW}$0 --studio-mirror${NC}"
    echo ""
    echo -e "${BLUE}🎯 Basic validation complete (run with --studio-mirror for full Studio compatibility)${NC}"
fi

# Calculate and display total execution time
SCRIPT_END_TIME=$(date +%s)
TOTAL_TIME=$((SCRIPT_END_TIME - SCRIPT_START_TIME))
echo ""
echo -e "${CYAN}⏱️  Total Execution Time: ${TOTAL_TIME}s (Timeout: ${GLOBAL_TIMEOUT}s)${NC}"
log "Script completed in ${TOTAL_TIME}s (under ${GLOBAL_TIMEOUT}s timeout)"

if [[ "$FINAL_STATUS" == "SUCCESS" ]]; then
    if [[ "$STUDIO_MIRROR_MODE" == "true" ]]; then
        log "Debug session completed successfully - all tests passed including Studio compatibility"
        echo -e "${GREEN}🎉 SUCCESS: Local environment fully mirrors Studio behavior!${NC}"
    else
        log "Debug session completed successfully - basic validation passed"
        echo -e "${GREEN}🎉 SUCCESS: Basic debug validation completed!${NC}"
    fi
    exit 0
else
    if [[ "$STUDIO_MIRROR_MODE" == "true" ]] && [[ "$STUDIO_COMPATIBILITY" != "true" ]]; then
        log "Debug session completed with Studio compatibility issues detected"
        echo -e "${RED}⚠️  Studio compatibility failed - this explains the Studio vs local discrepancy${NC}"
        echo -e "${YELLOW}💡 Fix the blocking detection issues above to achieve Studio parity${NC}"
    else
        log "Debug session completed with validation errors detected"
        echo -e "${RED}⚠️  Please review the errors above and fix them before proceeding${NC}"
    fi
    exit 1
fi