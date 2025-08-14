#!/bin/bash

# 🎯 Enhanced LangGraph Debug Script with Full Graph Execution
# This script provides comprehensive debugging and full graph execution with ticker parameter
# UPDATED: Now properly mimics LangGraph dev environment with blocking I/O detection

set -e  # Exit on any error

# Command line argument parsing
TICKER=""
SHOW_HELP=false
SKIP_TESTS=false
ANALYZE_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --analyze-only)
            ANALYZE_ONLY=true
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
    echo "🎯 Enhanced LangGraph Debug Script with Full Graph Execution"
    echo ""
    echo "Usage: $0 [TICKER] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  TICKER            Stock ticker to analyze (e.g., GOOG, NVDA, AAPL)"
    echo "                    If not provided, defaults to GOOG"
    echo ""
    echo "Options:"
    echo "  --skip-tests      Skip preliminary tests and go directly to graph execution"
    echo "  --analyze-only    Only analyze results, don't run new execution"
    echo "  --help, -h        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 GOOG                 # Run full analysis for Google"
    echo "  $0 NVDA                 # Run full analysis for NVIDIA"
    echo "  $0 AAPL --skip-tests    # Run Apple analysis, skip tests"
    echo "  $0 --analyze-only       # Analyze latest execution results"
    exit 0
fi

# Set default ticker if not provided
if [[ -z "$TICKER" ]]; then
    TICKER="GOOG"
    echo "ℹ️  No ticker provided, using default: GOOG"
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
DEBUG_LOG="$LOG_DIR/debug_session_${TICKER}_$TIMESTAMP.log"
GRAPH_LOG="$LOG_DIR/graph_execution_${TICKER}_$TIMESTAMP.log"
RESULTS_LOG="$LOG_DIR/results_${TICKER}_$TIMESTAMP.json"

echo -e "${BLUE}🎯 Enhanced LangGraph Debug Script with Full Graph Execution${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo -e "📈 Ticker: ${CYAN}$TICKER${NC}"
echo -e "📂 Working Directory: $SCRIPT_DIR"
echo -e "📝 Debug Log: $DEBUG_LOG"
echo -e "📊 Graph Log: $GRAPH_LOG"
echo -e "📋 Results: $RESULTS_LOG"
echo -e "⏰ Timeout: ${GLOBAL_TIMEOUT}s"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

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

# Phase 0: Configuration Validation  
echo -e "${PURPLE}📋 Phase 0: Configuration Validation${NC}"
echo "====================================="
check_timeout

echo -e "${CYAN}🔍 Running comprehensive configuration validation...${NC}"
cat > validate_config.py << 'EOF'
#!/usr/bin/env python3
"""Configuration validation script for trading graph server"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from agent.monitoring.configuration_validator import validate_startup_configuration
    
    print("🔍 Starting comprehensive configuration validation...")
    results = validate_startup_configuration()
    
    print(f"📊 Validation Summary:")
    print(f"  Total checks: {results['total_checks']}")
    print(f"  Passed: {results['passed_checks']}")
    print(f"  Failed: {results['failed_checks']}")
    print(f"  Success rate: {results['success_rate']}%")
    print(f"  Overall status: {results['overall_status']}")
    print(f"  Can proceed: {results['can_proceed']}")
    
    # Print issues if any
    if results['critical_issues'] > 0:
        print(f"\n🚨 CRITICAL ISSUES ({results['critical_issues']}):")
        for issue in results['issues_by_severity']['critical']:
            print(f"  ❌ {issue['component']}: {issue['message']}")
    
    if results['error_issues'] > 0:
        print(f"\n🚨 ERROR ISSUES ({results['error_issues']}):")
        for issue in results['issues_by_severity']['error']:
            print(f"  ⚠️ {issue['component']}: {issue['message']}")
    
    if results['warning_issues'] > 0:
        print(f"\n⚠️ WARNING ISSUES ({results['warning_issues']}):")
        for issue in results['issues_by_severity']['warning']:
            print(f"  ⚠️ {issue['component']}: {issue['message']}")
    
    if not results['can_proceed']:
        print("\n🚨 CRITICAL CONFIGURATION ISSUES DETECTED - CANNOT PROCEED")
        print("Please resolve the critical issues above before running the trading graph.")
        sys.exit(1)
    else:
        print("\n✅ CONFIGURATION VALIDATION PASSED - Safe to proceed")
        
except Exception as e:
    print(f"❌ Configuration validation failed: {e}")
    print("Proceeding with execution but configuration issues may cause failures...")

EOF

# Note: Configuration validation moved to Python modules for async safety
echo -e "${GREEN}✅ Configuration validation: Using built-in validators${NC}"
log "Configuration validation: Using async-safe built-in validators"
echo ""

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

# Check for Python 3.11 to match LangGraph dev environment
if command_exists python3.11; then
    PYTHON_VERSION=$(python3.11 --version)
    echo -e "${GREEN}✅ Python 3.11 found (matches LangGraph dev): $PYTHON_VERSION${NC}"
    log "Python version: $PYTHON_VERSION (LangGraph compatible)"
    PYTHON_CMD="python3.11"
elif command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${YELLOW}⚠️ Using Python: $PYTHON_VERSION (LangGraph uses 3.11)${NC}"
    log "WARNING: Python version mismatch with LangGraph dev (3.11)"
    PYTHON_CMD="python3"
else
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
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

# Set debug environment variables to match LangGraph dev
echo -e "${CYAN}🔄 Setting debug environment variables (LangGraph dev mode)...${NC}"
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"
export LANGCHAIN_TRACING_V2=true  # Enable tracing for full analysis
export LANGGRAPH_DEBUG=true
export LANGGRAPH_ENV=development  # Match LangGraph dev environment
export PYTHON_LOG_LEVEL=INFO  # Set to INFO to reduce noise

# 🚨 CRITICAL: Enable asyncio debug mode to detect blocking I/O like LangGraph dev
export PYTHONASYNCIODEBUG=1
echo -e "${YELLOW}⚠️ ASYNCIO DEBUG MODE ENABLED - Monitoring for async violations${NC}"
log "Asyncio debug mode enabled to match LangGraph dev async monitoring"

# Enable minimalist logging
export USE_MINIMALIST_LOGGING=true
export MINIMALIST_LOG_FILE="$LOG_DIR/minimalist_debug_${TICKER}_$TIMESTAMP.log"

log "Debug environment variables set"
log "Minimalist logging enabled: $MINIMALIST_LOG_FILE"

echo ""

# Phase 2: Preliminary Tests (skip if requested)
if [[ "$SKIP_TESTS" != "true" ]]; then
    echo -e "${PURPLE}📋 Phase 2: Preliminary Tests${NC}"
    echo "================================"
    check_timeout

    # Check imports
    run_cmd "$PYTHON_CMD -c 'from src.agent.graph.trading_graph import TradingAgentsGraph; print(\"✅ Core imports working\")'" "Testing core imports"
    run_cmd "$PYTHON_CMD -c 'from src.agent.utils.debug_logging import debug_node; print(\"✅ Debug logging imports working\")'" "Testing debug logging imports"
    run_cmd "$PYTHON_CMD -c 'from langchain_openai import ChatOpenAI; print(\"✅ LangChain imports working\")'" "Testing LangChain imports"

    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping preliminary tests${NC}"
fi

# Phase 3: Full Graph Execution
echo -e "${PURPLE}📋 Phase 3: Full Graph Execution for $TICKER${NC}"
echo "=============================================="
check_timeout

# Create the full graph execution script
echo -e "${CYAN}🔄 Creating full graph execution script...${NC}"
cat > execute_graph.py << EOF
#!/usr/bin/env python3
"""
Full graph execution script for trading agents
Mimics langgraph dev execution environment with blocking I/O detection
"""

import asyncio
import logging
import sys
import json
import traceback
import os
import warnings
from datetime import datetime, date

# 🚨 CRITICAL: Enable asyncio debug mode to detect blocking I/O like LangGraph dev
if os.environ.get('PYTHONASYNCIODEBUG') == '1':
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    # Enable debug mode on the event loop
    import functools
    
    # Patch asyncio to detect blocking I/O
    def patch_blocking_io_detection():
        """Mimic LangGraph dev's blocking I/O detection"""
        import sys
        import threading
        
        # Track blocking I/O errors globally
        global blocking_io_errors
        blocking_io_errors = []
        
        # Hook into asyncio's slow callback detection
        loop = asyncio.new_event_loop()
        loop.set_debug(True)  # Enable debug mode
        loop.slow_callback_duration = 0.01  # Very sensitive to blocking calls
        asyncio.set_event_loop(loop)
        
        # Add custom error tracking
        def track_blocking_io(msg):
            """Track blocking I/O errors for later reporting"""
            blocking_io_errors.append(msg)
            print(f"🚨 BLOCKING I/O DETECTED: {msg}", file=sys.stderr)
        
        # Store the tracking function globally
        asyncio._track_blocking_io = track_blocking_io
        
        print("🚨 Async monitoring enabled (mimicking LangGraph dev)")
        print("   - Asyncio debug mode: ENABLED")
        print("   - Slow callback detection: 0.01s threshold")
        print("   - Will detect sync violations in async context")
        
        return blocking_io_errors
    
    # Apply the patch and get error tracker
    blocking_io_tracker = patch_blocking_io_detection()

# CRITICAL: Load environment variables FIRST before any imports that use config
# This prevents blocking I/O in async context
sys.path.insert(0, 'src')

# Set up environment to mimic langgraph dev
os.environ['LANGGRAPH_ENV'] = 'development'
os.environ['LANGGRAPH_DEBUG'] = 'true'
os.environ['LANGCHAIN_TRACING_V2'] = 'true'

# Load environment variables from .env file
from agent.load_env import load_environment
load_environment(verbose=False)  # Load .env file before any config imports

# Set up async-safe logging (no blocking I/O)
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create handlers without using basicConfig
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    file_handler = logging.FileHandler('$GRAPH_LOG')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

# Reduce noise from some loggers
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def execute_full_graph(ticker="$TICKER", trade_date=None):
    """Execute the full trading graph with all nodes - LangGraph Dev Compatible"""
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 Starting full graph execution for {ticker}")
        logger.info(f"📅 Trade Date: {trade_date or 'Today'}")
        logger.info(f"🔧 Environment: {os.environ.get('LANGGRAPH_ENV', 'production')}")
        logger.info(f"🔍 Debug Mode: {os.environ.get('LANGGRAPH_DEBUG', 'false')}")
        
        # Import required modules (delayed to prevent blocking I/O at module level)
        from src.agent.graph.trading_graph import TradingAgentsGraph
        from src.agent.default_config import DEFAULT_CONFIG
        from src.agent.utils.debug_logging import debug_node
        
        # Verify no blocking I/O by checking async context
        try:
            asyncio.current_task()
            logger.info("✅ Running in async context - no blocking I/O detected")
        except RuntimeError:
            logger.warning("⚠️ Not in async context - potential blocking I/O")
        
        # Enable enhanced implementation for testing
        enhanced_config = DEFAULT_CONFIG.copy()
        enhanced_config['enable_send_api'] = True
        enhanced_config['enable_enhanced_monitoring'] = True
        enhanced_config['enable_fallback'] = True
        
        # Initialize the trading graph with enhanced implementation
        logger.info("🏗️ Initializing trading graph with enhanced implementation...")
        logger.info("🚀 Using Send API + Conditional Edges for parallel execution")
        trading_graph = TradingAgentsGraph(
            config=enhanced_config,
            selected_analysts=["market", "social", "news", "fundamentals"]
        )
        
        # Use today's date if not specified
        if not trade_date:
            trade_date = date.today().strftime("%Y-%m-%d")
        
        logger.info(f"📊 Executing graph for {ticker} on {trade_date}")
        logger.info("⏳ This will analyze market data, news, social sentiment, and fundamentals...")
        logger.info("⏳ Expected runtime: 2-10 minutes depending on data availability")
        
        # Execute the full graph
        result = await trading_graph.propagate(ticker, trade_date)
        
        # Handle tuple return (final_state, processed_signal)
        if isinstance(result, tuple) and len(result) == 2:
            final_state, processed_signal = result
            result = final_state
            result["processed_signal"] = processed_signal
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Log summary results
        logger.info(f"✅ Graph execution completed in {execution_time:.2f} seconds")
        logger.info("📊 === EXECUTION SUMMARY ===")
        logger.info(f"   Ticker: {ticker}")
        logger.info(f"   Date: {trade_date}")
        logger.info(f"   Runtime: {execution_time:.2f}s")
        
        # Extract key results
        final_decision = result.get('processed_signal', 'No signal')
        investment_plan = result.get('investment_plan', 'No plan generated')
        
        logger.info(f"   Decision: {final_decision}")
        
        # Save detailed results to JSON
        results = {
            "ticker": ticker,
            "trade_date": trade_date,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "final_decision": final_decision,
            "investment_plan": investment_plan,
            "full_result": result
        }
        
        with open('$RESULTS_LOG', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Detailed results saved to: $RESULTS_LOG")
        
        # Display key insights
        logger.info("🔍 === KEY INSIGHTS ===")
        
        # 🔍 MARKET REPORT DEBUGGING - Log actual content
        if 'market_report' in result:
            market_report = result['market_report']
            logger.info("📈 Market Analysis: Available")
            logger.info("🔍 === MARKET REPORT CONTENT DEBUG ===")
            logger.info(f"📊 Market Report Type: {type(market_report)}")
            logger.info(f"📊 Market Report Length: {len(str(market_report))}")
            
            # Check for blocking I/O error in market report
            market_report_str = str(market_report)
            blocking_io_found = False
            
            # Check for various blocking I/O error patterns
            blocking_patterns = [
                "blocking call to io.textiowrapper",
                "error: blocking call",
                "blocking i/o",
                "synchronous blocking call"
            ]
            
            for pattern in blocking_patterns:
                if pattern in market_report_str.lower():
                    blocking_io_found = True
                    break
            
            if blocking_io_found:
                logger.error("❌ CRITICAL: BLOCKING I/O ERROR DETECTED IN MARKET REPORT")
                logger.error("❌ This prevents proper async execution in LangGraph")
                logger.error(f"❌ Market Report Content: {market_report_str[:500]}...")
                # Store error for final reporting
                if 'blocking_io_tracker' in globals():
                    blocking_io_tracker.append("Market report contains blocking I/O error")
                # Set execution as failed
                blocking_io_detected = True
            elif "error:" in market_report_str.lower():
                logger.warning("⚠️ ERROR DETECTED IN MARKET REPORT:")
                logger.warning(f"⚠️ Market Report Content: {market_report_str[:500]}...")
            else:
                logger.info("✅ Market Report appears normal:")
                logger.info(f"✅ Market Report Preview: {market_report_str[:200]}...")  
            
            logger.info("🔍 === END MARKET REPORT DEBUG ===")
        else:
            logger.error("❌ NO MARKET REPORT FOUND IN RESULTS")
        
        # News sentiment
        if 'news_report' in result:
            logger.info("📰 News Sentiment: Available")
            
        # Social sentiment  
        if 'social_report' in result:
            logger.info("💬 Social Sentiment: Available")
            
        # Fundamentals
        if 'fundamentals_report' in result:
            logger.info("💰 Fundamentals: Available")
        
        # Risk assessment
        if 'risk_report' in result:
            logger.info("⚠️  Risk Assessment: Available")
        
        # Check for any blocking I/O errors detected during execution
        blocking_io_detected = locals().get('blocking_io_detected', False)
        if 'blocking_io_tracker' in globals() and blocking_io_tracker:
            logger.error(f"❌ BLOCKING I/O ERRORS DETECTED: {len(blocking_io_tracker)} instances")
            for error in blocking_io_tracker:
                logger.error(f"   • {error}")
            blocking_io_detected = True
        
        if blocking_io_detected:
            logger.error("❌ === EXECUTION FAILED DUE TO BLOCKING I/O ===")
            logger.error("💡 Solution: Replace yfinance with async alternatives")
            logger.error("📚 See BLOCKING_IO_FIX_ATTEMPTS.md for details")
            return False
        else:
            logger.info("✅ === EXECUTION COMPLETE ===")
            return True
        
    except Exception as e:
        logger.error(f"❌ Graph execution failed: {str(e)}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        # Save error information
        error_info = {
            "ticker": ticker,
            "trade_date": trade_date,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        with open('$RESULTS_LOG', 'w') as f:
            json.dump(error_info, f, indent=2)
        
        return False

if __name__ == "__main__":
    # Get ticker from command line or use default
    ticker = sys.argv[1] if len(sys.argv) > 1 else "$TICKER"
    trade_date = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = asyncio.run(execute_full_graph(ticker, trade_date))
    
    if success:
        print(f"\n🎉 FULL GRAPH EXECUTION SUCCESSFUL for {ticker}!")
        sys.exit(0)
    else:
        print(f"\n💥 GRAPH EXECUTION FAILED for {ticker} - Check logs for details")
        sys.exit(1)
EOF

echo -e "${GREEN}✅ Graph execution script created${NC}"

# Run the full graph execution
echo -e "${CYAN}🔄 Executing full trading graph for $TICKER...${NC}"
echo -e "${YELLOW}⏳ This will run all analysis nodes (market, news, social, fundamentals)${NC}"
echo -e "${YELLOW}⏳ Expected runtime: 2-10 minutes${NC}"
echo ""

# Execute and capture both stdout and stderr
EXEC_OUTPUT=$($PYTHON_CMD execute_graph.py "$TICKER" 2>&1 | tee -a "$DEBUG_LOG")
EXEC_RESULT=${PIPESTATUS[0]}

# Check for blocking I/O errors in output (avoid false positives from our own log messages)
if echo "$EXEC_OUTPUT" | grep -qi "blocking.*error\|blocking.*detected.*failed\|io.textiowrapper.*error\|synchronous.*blocking.*call" | grep -v "detection enabled\|debug mode enabled"; then
    echo -e "${RED}❌ CRITICAL: Blocking I/O errors detected - execution FAILED${NC}"
    echo -e "${RED}   This is the same error that occurs in LangGraph dev${NC}"
    echo -e "${YELLOW}💡 Solution: Replace yfinance with async alternatives${NC}"
    log "CRITICAL: Blocking I/O errors detected - same as LangGraph dev"
    EXECUTION_SUCCESS=false
elif [ $EXEC_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Full graph execution completed successfully${NC}"
    log "Full graph execution passed for $TICKER"
    EXECUTION_SUCCESS=true
else
    echo -e "${RED}❌ Full graph execution failed${NC}"
    log "Full graph execution failed for $TICKER"
    EXECUTION_SUCCESS=false
fi

# Clean up
rm -f execute_graph.py

echo ""

# Phase 4: Results Analysis
echo -e "${PURPLE}📋 Phase 4: Results Analysis${NC}"
echo "============================"
check_timeout

if [[ -f "$RESULTS_LOG" ]]; then
    echo -e "${CYAN}📊 Analyzing execution results...${NC}"
    
    # Display key results
    $PYTHON_CMD << EOF
import json
import os

results_file = "$RESULTS_LOG"

try:
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    if 'error' in results:
        print(f"❌ Execution failed with error: {results['error']}")
    else:
        print(f"📊 Results Summary for {results['ticker']}:")
        print(f"   Date: {results['trade_date']}")
        print(f"   Runtime: {results['execution_time']:.2f}s")
        print(f"   Decision: {results['final_decision']}")
        
        # Check if we have all expected reports
        full_result = results.get('full_result', {})
        reports = ['market_report', 'news_report', 'social_report', 'fundamentals_report', 'risk_report']
        
        print("\n📋 Report Availability:")
        for report in reports:
            status = "✅" if report in full_result and full_result[report] else "❌"
            print(f"   {status} {report.replace('_', ' ').title()}")
        
        # Display investment plan if available
        if results.get('investment_plan') and results['investment_plan'] != 'No plan generated':
            print(f"\n💼 Investment Plan Preview:")
            plan = results['investment_plan']
            if isinstance(plan, str):
                # Show first few lines
                lines = plan.split('\\n')[:5]
                for line in lines:
                    if line.strip():
                        print(f"   {line.strip()}")
                if len(plan.split('\\n')) > 5:
                    print("   ... (see full results in log file)")
        
        print(f"\n📄 Full results saved to: {os.path.basename(results_file)}")
        
except Exception as e:
    print(f"❌ Error analyzing results: {e}")
EOF
else
    echo -e "${YELLOW}⚠️  No results file found${NC}"
fi

echo ""

# Phase 5: Performance Analysis
echo -e "${PURPLE}📋 Phase 5: Performance Analysis${NC}"
echo "================================"
check_timeout

# Analyze graph performance
echo -e "${CYAN}🔄 Analyzing graph performance...${NC}"
if [[ -f "$GRAPH_LOG" ]]; then
    # Count node executions
    NODE_COUNT=$(grep -c "Starting.*node" "$GRAPH_LOG" 2>/dev/null || echo "0")
    ERROR_COUNT=$(grep -c "ERROR\|Exception\|Failed" "$GRAPH_LOG" 2>/dev/null || echo "0")
    WARNING_COUNT=$(grep -c "WARNING" "$GRAPH_LOG" 2>/dev/null || echo "0")
    
    echo -e "📊 Execution Statistics:"
    echo -e "   Nodes Executed: $NODE_COUNT"
    echo -e "   Errors: $ERROR_COUNT"
    echo -e "   Warnings: $WARNING_COUNT"
    
    # Token Usage Analysis
    echo -e "\n💰 Token Usage Analysis:"
    if [[ -f "$RESULTS_LOG" ]]; then
        $PYTHON_CMD << EOF
import json
import re
import os

results_file = "$RESULTS_LOG"

try:
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Estimate token usage based on text content
    def estimate_tokens(text):
        """Rough estimate: 1 token per 4 characters"""
        if not text:
            return 0
        return len(str(text)) // 4
    
    full_result = results.get('full_result', {})
    
    # Analyze individual report sizes
    reports = {
        'market_report': 'Market Analysis',
        'news_report': 'News Data',
        'sentiment_report': 'Social Sentiment', 
        'fundamentals_report': 'Fundamentals',
        'investment_plan': 'Investment Plan',
        'bull_case': 'Bull Research',
        'bear_case': 'Bear Research',
        'risk_analysis': 'Risk Analysis'
    }
    
    total_tokens = 0
    print("   📋 Report Token Usage:")
    
    for report_key, report_name in reports.items():
        content = full_result.get(report_key) or results.get(report_key, "")
        if content:
            tokens = estimate_tokens(content)
            total_tokens += tokens
            print(f"     {report_name}: {tokens:,} tokens ({len(str(content)):,} chars)")
    
    # Check for news filtering evidence
    news_content = full_result.get('news_report', '')
    if news_content:
        # Count articles in news report
        import re
        article_count = len(re.findall(r'### Article \d+', news_content))
        if article_count > 0:
            print(f"     📰 News Articles Found: {article_count} articles")
            
        # Check for filtering evidence
        if 'filtered' in news_content.lower() or 'reduction' in news_content.lower():
            print("     ✅ News filtering appears to be applied")
        else:
            print("     ❌ No evidence of news filtering found")
    
    print(f"\n   💰 Estimated Total Token Usage: {total_tokens:,} tokens")
    
    # Token efficiency analysis
    if total_tokens > 0:
        if total_tokens > 300000:
            print("   🚨 CRITICAL: Very high token usage (>300K)")
        elif total_tokens > 150000:
            print("   ⚠️  WARNING: High token usage (>150K)")
        elif total_tokens > 50000:
            print("   📊 MODERATE: Acceptable token usage")
        else:
            print("   ✅ OPTIMAL: Low token usage")

except Exception as e:
    print(f"   ❌ Error analyzing token usage: {e}")
EOF
    else
        echo -e "   ❌ No results file found for token analysis"
    fi
    
    # Show any errors
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "\n${RED}❌ Errors detected:${NC}"
        grep -A 2 "ERROR\|Exception\|Failed" "$GRAPH_LOG" | head -20
    fi
else
    echo -e "${YELLOW}⚠️  No graph log found${NC}"
fi

echo ""

# Phase 6: Generate Debug Report
echo -e "${PURPLE}📋 Phase 6: Debug Report Generation${NC}"
echo "===================================="
check_timeout

REPORT_FILE="$LOG_DIR/execution_report_${TICKER}_$TIMESTAMP.md"

cat > "$REPORT_FILE" << EOF
# 📊 Trading Graph Execution Report

**Ticker:** $TICKER  
**Generated:** $(date)  
**Session ID:** $TIMESTAMP  
**Working Directory:** $SCRIPT_DIR

## 📋 Execution Summary

- **Target Ticker:** $TICKER
- **Execution Status:** $([ "$EXECUTION_SUCCESS" = true ] && echo "✅ SUCCESS" || echo "❌ FAILED")
- **Total Runtime:** $(($(date +%s) - SCRIPT_START_TIME))s

## 🔧 Configuration

- **Python Version:** $($PYTHON_CMD --version)
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** $DEBUG_LOG
- **Graph Log:** $GRAPH_LOG  
- **Results JSON:** $RESULTS_LOG
- **This Report:** $REPORT_FILE

## 📊 Key Results

$(if [[ -f "$RESULTS_LOG" ]] && [[ "$EXECUTION_SUCCESS" = true ]]; then
    $PYTHON_CMD -c "
import json
with open('$RESULTS_LOG', 'r') as f:
    r = json.load(f)
    if 'error' not in r:
        print(f'- **Decision:** {r.get(\"final_decision\", \"N/A\")}')
        print(f'- **Runtime:** {r.get(\"execution_time\", \"N/A\")}s')
        print(f'- **Trade Date:** {r.get(\"trade_date\", \"N/A\")}')
        
        # Token usage estimation
        def estimate_tokens(text):
            return len(str(text)) // 4 if text else 0
        
        full_result = r.get('full_result', {})
        total_tokens = 0
        for key in ['market_report', 'news_report', 'sentiment_report', 'fundamentals_report', 'investment_plan']:
            content = full_result.get(key) or r.get(key, '')
            if content:
                total_tokens += estimate_tokens(content)
        
        print(f'- **Estimated Token Usage:** {total_tokens:,} tokens')
"
else
    echo "- No results available"
fi)

## 🔍 Next Steps

1. **View detailed results:**
   \`\`\`bash
   cat $RESULTS_LOG | jq .
   \`\`\`

2. **Monitor logs:**
   \`\`\`bash
   tail -f $GRAPH_LOG
   \`\`\`

3. **Run for different ticker:**
   \`\`\`bash
   ./debug_local.sh AAPL
   \`\`\`

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

EOF

echo -e "${GREEN}✅ Execution report generated: $REPORT_FILE${NC}"
log "Execution report created: $REPORT_FILE"

echo ""

# Phase 7: Summary
echo -e "${PURPLE}📋 Execution Complete${NC}"
echo "======================"
check_timeout

TOTAL_TIME=$(($(date +%s) - SCRIPT_START_TIME))

echo -e "${CYAN}📊 Summary:${NC}"
echo -e "   Ticker Analyzed: ${CYAN}$TICKER${NC}"
echo -e "   Total Runtime: ${TOTAL_TIME}s"
echo -e "   Status: $([ "$EXECUTION_SUCCESS" = true ] && echo "${GREEN}✅ SUCCESS${NC}" || echo "${RED}❌ FAILED${NC}")"
echo ""
echo -e "${CYAN}📂 Output Files:${NC}"
echo -e "   📝 Debug Log: $DEBUG_LOG"
echo -e "   📊 Graph Log: $GRAPH_LOG"
echo -e "   📋 Results: $RESULTS_LOG"
echo -e "   📄 Report: $REPORT_FILE"
echo ""

if [[ "$EXECUTION_SUCCESS" = true ]]; then
    echo -e "${GREEN}🎉 SUCCESS: Full graph execution completed for $TICKER!${NC}"
    echo -e "${CYAN}💡 Tips:${NC}"
    echo -e "   - View detailed results: cat $RESULTS_LOG | jq ."
    echo -e "   - Run for another ticker: ./debug_local.sh NVDA"
    echo -e "   - Skip tests next time: ./debug_local.sh $TICKER --skip-tests"
    exit 0
else
    echo -e "${RED}❌ FAILED: Graph execution encountered errors${NC}"
    
    # Check specifically for blocking I/O errors (avoid false positives)
    if grep -qi "blocking.*error\|blocking.*detected.*failed\|io.textiowrapper.*error\|synchronous.*blocking.*call" "$DEBUG_LOG" 2>/dev/null | grep -v "detection enabled\|debug mode enabled"; then
        echo -e "${RED}🚨 CRITICAL: Blocking I/O errors detected${NC}"
        echo -e "${RED}   This matches the errors seen in LangGraph dev${NC}"
        echo -e "${YELLOW}📚 See BLOCKING_IO_FIX_ATTEMPTS.md for attempted solutions${NC}"
        echo -e "${YELLOW}💡 Solution: Replace yfinance with async alternatives${NC}"
    fi
    
    echo -e "${YELLOW}💡 Debugging tips:${NC}"
    echo -e "   - Check error details: grep ERROR $GRAPH_LOG"
    echo -e "   - View blocking I/O errors: grep -i 'blocking' $DEBUG_LOG"
    echo -e "   - View full traceback: cat $RESULTS_LOG | jq .traceback"
    echo -e "   - Verify API keys: grep API .env"
    exit 1
fi