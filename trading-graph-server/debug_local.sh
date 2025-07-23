#!/bin/bash

# 🐛 LangGraph Local Debug Script
# This script provides comprehensive debugging for the trading graph locally

set -e  # Exit on any error

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

echo -e "${BLUE}🐛 LangGraph Local Debug Script${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "📂 Working Directory: $SCRIPT_DIR"
echo -e "📝 Debug Log: $DEBUG_LOG"
echo -e "📊 Graph Log: $GRAPH_LOG"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

# Function to perform post-run validation checks
validate_critical_components() {
    local validation_errors=0
    
    echo -e "${CYAN}🔄 Performing post-run validation checks...${NC}"
    
    # Check 1: Virtual environment is active
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo -e "${RED}   ❌ Virtual environment not active${NC}"
        validation_errors=$((validation_errors + 1))
    else
        echo -e "${GREEN}   ✅ Virtual environment active${NC}"
    fi
    
    # Check 2: Required Python packages are importable
    if python3 -c "from agent.graph.trading_graph import TradingAgentsGraph" 2>/dev/null; then
        echo -e "${GREEN}   ✅ Core trading graph imports working${NC}"
    else
        echo -e "${RED}   ❌ Core trading graph imports failed${NC}"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Check 3: Debug logging system is importable
    if python3 -c "from agent.utils.debug_logging import debug_node" 2>/dev/null; then
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
    local error_count=0
    
    echo "🔍 Performing comprehensive error validation..."
    echo "🔍 Scanning logs for errors, warnings, and fallback logic..."
    
    # Critical error patterns
    local error_patterns=(
        "Error:"
        "❌"
        "failed"
        "Traceback"
        "ValueError"
        "TypeError"
        "AttributeError"
        "ImportError"
        "ModuleNotFoundError"
        "KeyError"
        "RuntimeError"
        "Exception"
    )
    
    # Warning and fallback patterns (treat as errors)
    local warning_patterns=(
        "WARNING"
        "⚠️"
        "Warning"
        "warning"
        "WARN"
        "warn"
        "fallback"
        "Fallback"
        "FALLBACK"
        "default"
        "Default"
        "DEFAULT"
        "insufficient"
        "Insufficient"
        "INSUFFICIENT"
        "missing data"
        "Missing data"
        "MISSING DATA"
        "empty data"
        "Empty data"
        "EMPTY DATA"
        "no data"
        "No data"
        "NO DATA"
        "length: 0"
        "0 items"
        "0 chars"
        "empty report"
        "Empty report"
        "EMPTY REPORT"
        "incomplete"
        "Incomplete"
        "INCOMPLETE"
        "partial"
        "Partial"
        "PARTIAL"
        "backup"
        "Backup"
        "BACKUP"
    )
    
    # Business logic fallback patterns
    local business_fallback_patterns=(
        "HOLD.*insufficient"
        "HOLD.*missing"
        "HOLD.*incomplete"
        "fallback decision"
        "default decision"
        "safe fallback"
        "conservative fallback"
        "using default"
        "reverting to"
        "falling back"
        "backup strategy"
        "precautionary"
    )
    
    echo "📋 Error Detection Results:"
    
    # Check critical errors
    for pattern in "${error_patterns[@]}"; do
        local count
        count=$(grep -c "$pattern" "$log_file" 2>/dev/null || echo "0")
        count=$(echo "$count" | tr -d '\n' | tr -d ' ' | head -1)  # Clean the count variable
        if [ "$count" -gt 0 ]; then
            echo "   ❌ Found $count instances of: $pattern"
            error_count=$((error_count + count))
            echo "      Sample occurrences:"
            grep -n "$pattern" "$log_file" | head -3 | sed 's/^/        /'
            echo ""
        fi
    done
    
    # Check warnings and fallbacks (treat as errors)
    for pattern in "${warning_patterns[@]}"; do
        local count
        count=$(grep -i -c "$pattern" "$log_file" 2>/dev/null || echo "0")
        # Remove any newlines and ensure we have a valid integer
        count=$(echo "$count" | tr -d '\n' | head -1)
        if [ "$count" -gt 0 ] 2>/dev/null; then
            echo "   ❌ Found $count instances of WARNING/FALLBACK: $pattern"
            error_count=$((error_count + count))
            echo "      Sample occurrences:"
            grep -i -n "$pattern" "$log_file" | head -3 | sed 's/^/        /'
            echo ""
        fi
    done
    
    # Check business logic fallbacks
    for pattern in "${business_fallback_patterns[@]}"; do
        local count
        count=$(grep -i -c "$pattern" "$log_file" 2>/dev/null || echo "0")
        # Remove any newlines and ensure we have a valid integer
        count=$(echo "$count" | tr -d '\n' | head -1)
        if [ "$count" -gt 0 ] 2>/dev/null; then
            echo "   ❌ Found $count instances of BUSINESS FALLBACK: $pattern"
            error_count=$((error_count + count))
            echo "      Sample occurrences:"
            grep -i -n "$pattern" "$log_file" | head -3 | sed 's/^/        /'
            echo ""
        fi
    done
    
    # Additional specific checks for our trading system
    echo "🔍 Checking for specific trading system fallbacks..."
    
    # Check for empty reports
    if grep -q "report.*length.*0" "$log_file"; then
        echo "   ❌ Found empty reports (critical failure)"
        error_count=$((error_count + 1))
    fi
    
    # Check for missing debate data
    if grep -q "Missing.*debate" "$log_file"; then
        echo "   ❌ Found missing debate data (critical failure)"
        error_count=$((error_count + 1))
    fi
    
    # Check for insufficient analysis
    if grep -q "insufficient.*analysis" "$log_file"; then
        echo "   ❌ Found insufficient analysis warnings (critical failure)"
        error_count=$((error_count + 1))
    fi
    
    # Check for safe/conservative fallbacks in trading decisions
    if grep -q "HOLD.*due to.*missing\|HOLD.*insufficient\|HOLD.*incomplete" "$log_file"; then
        echo "   ❌ Found conservative fallback trading decisions (critical failure)"
        error_count=$((error_count + 1))
    fi
    
    if [ "$error_count" -eq 0 ]; then
        echo "   ✅ No errors, warnings, or fallbacks detected"
        return 0
    else
        echo "   ❌ Total error/warning/fallback instances found: $error_count"
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
else
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

# Check virtual environment
if [[ -d "venv" ]]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    log "Virtual environment directory exists"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found, creating...${NC}"
    run_cmd "python3 -m venv venv" "Creating virtual environment"
fi

# Activate virtual environment
echo -e "${CYAN}🔄 Activating virtual environment...${NC}"
source venv/bin/activate
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment activated: $VIRTUAL_ENV${NC}"
    log "Virtual environment activated: $VIRTUAL_ENV"
else
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

# Install/update dependencies
echo -e "${CYAN}🔄 Installing/updating dependencies...${NC}"
run_cmd "pip install -q --upgrade pip" "Upgrading pip"
run_cmd "pip install -q -e ." "Installing project dependencies"
run_cmd "pip install -q langchain-openai httpx aiofiles" "Installing additional debug dependencies"

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
    source .env
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
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
run_cmd "python3 -c 'from agent.graph.trading_graph import TradingAgentsGraph; print(\"✅ Core imports working\")'" "Testing core imports"
run_cmd "python3 -c 'from agent.utils.debug_logging import debug_node; print(\"✅ Debug logging imports working\")'" "Testing debug logging imports"
run_cmd "python3 -c 'from langchain_openai import ChatOpenAI; print(\"✅ LangChain imports working\")'" "Testing LangChain imports"

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
        from agent.graph.trading_graph import TradingAgentsGraph
        from agent.default_config import DEFAULT_CONFIG
        from langchain_openai import ChatOpenAI
        from agent.utils.debug_logging import debug_node
        logger.debug("✅ All imports successful")
        
        # Test 3: LLM creation
        logger.debug("🤖 Testing LLM creation...")
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        test_result = await llm.ainvoke([{"role": "user", "content": "Say 'LLM working'"}])
        logger.debug(f"✅ LLM test result: {test_result.content}")
        
        # Test 4: Memory system
        logger.debug("💾 Testing memory system...")
        from agent.utils.memory import FinancialSituationMemory
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
        
        test_state = {"company_of_interest": "TEST", "trade_date": "2024-01-01"}
        debug_result = await test_node(test_state)
        logger.debug(f"✅ Debug logging test: {debug_result}")
        
        # Test 7: Quick execution test (without full analysis)
        logger.debug("⚡ Testing quick graph execution...")
        start_time = datetime.now()
        
        # Test with minimal state
        minimal_result = await trading_graph.propagate("AAPL", "2024-01-15")
        
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
if python3 debug_test.py 2>&1 | tee -a "$DEBUG_LOG"; then
    echo -e "${GREEN}✅ Debug test completed successfully${NC}"
    log "Debug test passed"
else
    echo -e "${RED}❌ Debug test failed${NC}"
    log "Debug test failed"
    echo -e "${YELLOW}💡 Check $DEBUG_LOG for detailed error information${NC}"
fi

echo ""

# Phase 4: Server Testing
echo -e "${PURPLE}📋 Phase 4: Server Testing${NC}"
echo "=========================="
check_timeout

# Check if LangGraph CLI is installed
if command_exists langgraph; then
    echo -e "${GREEN}✅ LangGraph CLI found${NC}"
    log "LangGraph CLI available"
else
    echo -e "${YELLOW}⚠️  LangGraph CLI not found, installing...${NC}"
    run_cmd "pip install -q langgraph-cli" "Installing LangGraph CLI"
fi

# Test server startup (dry run)
echo -e "${CYAN}🔄 Testing server configuration...${NC}"
if langgraph dev --help >/dev/null 2>&1; then
    echo -e "${GREEN}✅ LangGraph dev command available${NC}"
    log "LangGraph dev command working"
else
    echo -e "${RED}❌ LangGraph dev command failed${NC}"
    log "LangGraph dev command failed"
fi

# Check if port 8123 is available
if command_exists lsof && lsof -Pi :8123 -sTCP:LISTEN -t >/dev/null; then
    echo -e "${YELLOW}⚠️  Port 8123 is in use${NC}"
    log "Port 8123 is occupied"
    echo -e "${CYAN}🔄 Attempting to free port 8123...${NC}"
    pkill -f "langgraph dev" 2>/dev/null || true
    sleep 2
else
    echo -e "${GREEN}✅ Port 8123 is available${NC}"
    log "Port 8123 is free"
fi

echo ""

# Phase 5: Graph Analysis
echo -e "${PURPLE}📋 Phase 5: Graph Analysis${NC}"
echo "=========================="
check_timeout

# Analyze graph structure
echo -e "${CYAN}🔄 Analyzing graph structure...${NC}"
cat > analyze_graph.py << 'EOF'
import asyncio
from agent.graph.trading_graph import TradingAgentsGraph
from agent.default_config import DEFAULT_CONFIG

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

if python3 analyze_graph.py 2>&1 | tee -a "$DEBUG_LOG"; then
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
# 🐛 LangGraph Debug Report

**Generated:** $(date)  
**Session ID:** $TIMESTAMP  
**Working Directory:** $SCRIPT_DIR

## 📋 Environment Status

- **Python Version:** $(python3 --version)
- **Virtual Environment:** $VIRTUAL_ENV
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

# Determine final status
if [[ "$VALIDATION_PASSED" == "true" ]] && [[ "$ERROR_CHECK_PASSED" == "true" ]]; then
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
echo -e "${CYAN}🚀 Next Steps:${NC}"
echo -e "   1. Review the debug report: ${YELLOW}cat $REPORT_FILE${NC}"
echo -e "   2. Start the server: ${YELLOW}langgraph dev --port 8123${NC}"
echo -e "   3. Monitor logs: ${YELLOW}tail -f $GRAPH_LOG${NC}"
echo ""
echo -e "${BLUE}🎯 Happy Debugging!${NC}"

# Calculate and display total execution time
SCRIPT_END_TIME=$(date +%s)
TOTAL_TIME=$((SCRIPT_END_TIME - SCRIPT_START_TIME))
echo ""
echo -e "${CYAN}⏱️  Total Execution Time: ${TOTAL_TIME}s (Timeout: ${GLOBAL_TIMEOUT}s)${NC}"
log "Script completed in ${TOTAL_TIME}s (under ${GLOBAL_TIMEOUT}s timeout)"

if [[ "$FINAL_STATUS" == "SUCCESS" ]]; then
    log "Debug session completed successfully - no errors detected"
    exit 0
else
    log "Debug session completed with errors detected"
    echo -e "${RED}⚠️  Please review the errors above and fix them before proceeding${NC}"
    exit 1
fi 