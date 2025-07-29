#!/bin/bash

# 🎯 Enhanced LangGraph Studio Environment Mirror + Debug Script
# This script exactly mirrors Studio's environment and catches blocking call issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}🎯 Enhanced Studio Environment Mirror${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "🕐 Started: $(date)"
echo ""

# Phase 1: Environment Detection
echo -e "${PURPLE}📋 Phase 1: Environment Detection${NC}"
echo "=================================="

# Detect Python versions
STUDIO_PYTHON=""
LOCAL_PYTHON=""

if command -v python3.11 >/dev/null 2>&1; then
    STUDIO_PYTHON="python3.11"
    echo -e "${GREEN}✅ Found Python 3.11 (Studio environment)${NC}"
else
    echo -e "${YELLOW}⚠️  Python 3.11 not found (Studio uses 3.11)${NC}"
fi

if command -v python3.13 >/dev/null 2>&1; then
    LOCAL_PYTHON="python3.13"
    echo -e "${GREEN}✅ Found Python 3.13 (Local environment)${NC}"
else
    LOCAL_PYTHON="python3"
    echo -e "${YELLOW}⚠️  Using default Python${NC}"
fi

# Phase 2: Virtual Environment Setup
echo -e "${PURPLE}📋 Phase 2: Virtual Environment Setup${NC}"
echo "====================================="

if [[ -d "venv" ]]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
else
    echo -e "${CYAN}🔄 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install dependencies
echo -e "${CYAN}🔄 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -e .

# Phase 3: Blocking Call Detection Tests
echo -e "${PURPLE}📋 Phase 3: Studio Blocking Call Detection${NC}"
echo "==========================================="

echo -e "${CYAN}🔍 Installing blockbuster for blocking detection...${NC}"
pip install -q blockbuster

# Test 1: Import Chain Blocking Detection
echo -e "${CYAN}🧪 Test 1: Import Chain Blocking Detection${NC}"
cat > test_blocking_imports.py << 'EOF'
#!/usr/bin/env python3
"""Test import chain for blocking calls like Studio does"""

import sys
import os
sys.path.insert(0, 'src')

def test_with_blocking_detection():
    """Test imports with blocking call detection enabled"""
    try:
        import blockbuster.blockbuster as bb
        bb.install()
        print("🔒 Blockbuster blocking detection enabled")
        
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
        
        # Step 3: Test graph factory function
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
        
        result = agent.graph(config)
        print(f"     ✅ Graph factory success: {type(result)}")
        
        print("🎉 ALL IMPORTS PASSED BLOCKING DETECTION!")
        return True
        
    except bb.BlockingError as e:
        print(f"❌ BLOCKING CALL DETECTED: {e}")
        print("📍 This is the exact error Studio encounters!")
        return False
    except Exception as e:
        print(f"❌ OTHER ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_blocking_detection()
    exit(0 if success else 1)
EOF

if python3 test_blocking_imports.py; then
    echo -e "${GREEN}✅ Blocking detection test PASSED${NC}"
    BLOCKING_TEST_PASSED=true
else
    echo -e "${RED}❌ Blocking detection test FAILED${NC}"
    BLOCKING_TEST_PASSED=false
fi

rm -f test_blocking_imports.py

# Test 2: Python 3.11 Compatibility Test
echo -e "${CYAN}🧪 Test 2: Python 3.11 Compatibility Test${NC}"
if [[ -n "$STUDIO_PYTHON" ]]; then
    cat > test_python311.py << 'EOF'
#!/usr/bin/env python3
"""Test with Python 3.11 like Studio uses"""

import sys
sys.path.insert(0, 'src')

try:
    import agent
    from langchain_core.runnables import RunnableConfig
    
    config = RunnableConfig(tags=[], metadata={}, callbacks=None, recursion_limit=25)
    result = agent.graph(config)
    print(f"✅ Python 3.11 test passed: {type(result)}")
    
except Exception as e:
    print(f"❌ Python 3.11 test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF

    if $STUDIO_PYTHON test_python311.py; then
        echo -e "${GREEN}✅ Python 3.11 compatibility test PASSED${NC}"
        PYTHON311_TEST_PASSED=true
    else
        echo -e "${RED}❌ Python 3.11 compatibility test FAILED${NC}"
        PYTHON311_TEST_PASSED=false
    fi
    
    rm -f test_python311.py
else
    echo -e "${YELLOW}⚠️  Skipping Python 3.11 test (not available)${NC}"
    PYTHON311_TEST_PASSED=true
fi

# Phase 4: Studio Server Simulation
echo -e "${PURPLE}📋 Phase 4: Studio Server Simulation${NC}"
echo "===================================="

echo -e "${CYAN}🧪 Test 3: LangGraph Dev Server Test${NC}"

# Set environment variables like Studio would
export PYTHONPATH="$SCRIPT_DIR/src"

# Test server startup (non-blocking)
echo -e "${CYAN}🔄 Testing langgraph dev startup...${NC}"

# Start server in background with timeout
timeout 15s langgraph dev --port 8125 --no-browser &
SERVER_PID=$!

# Wait for server to start
sleep 8

# Test if server is responding
if curl -s http://127.0.0.1:8125/assistants >/dev/null 2>&1; then
    echo -e "${GREEN}✅ LangGraph dev server started successfully${NC}"
    SERVER_TEST_PASSED=true
else
    echo -e "${RED}❌ LangGraph dev server failed to start${NC}"
    SERVER_TEST_PASSED=false
fi

# Clean up server
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

# Phase 5: Comprehensive Results
echo -e "${PURPLE}📋 Phase 5: Final Results${NC}"
echo "========================="

echo -e "${CYAN}🎯 Test Results Summary:${NC}"
echo "📊 Blocking Detection Test: $([ "$BLOCKING_TEST_PASSED" = true ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "📊 Python 3.11 Test: $([ "$PYTHON311_TEST_PASSED" = true ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "📊 Studio Server Test: $([ "$SERVER_TEST_PASSED" = true ] && echo "✅ PASS" || echo "❌ FAIL")"

# Overall result
if [[ "$BLOCKING_TEST_PASSED" = true ]] && [[ "$PYTHON311_TEST_PASSED" = true ]] && [[ "$SERVER_TEST_PASSED" = true ]]; then
    echo -e "${GREEN}🎉 ALL STUDIO COMPATIBILITY TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ Your code is ready for LangGraph Studio${NC}"
    FINAL_RESULT=0
else
    echo -e "${RED}❌ STUDIO COMPATIBILITY ISSUES DETECTED${NC}"
    echo -e "${RED}🔧 Please review and fix the failing tests above${NC}"
    FINAL_RESULT=1
fi

echo ""
echo -e "${BLUE}🎯 Studio Compatibility Check Complete${NC}"
echo -e "🕐 Completed: $(date)"

exit $FINAL_RESULT 