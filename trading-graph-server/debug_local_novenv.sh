#!/bin/bash
# Modified debug_local.sh to run without virtual environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Enhanced LangGraph Debug Script (No venv)${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo "📂 Working Directory: $(pwd)"

# Check Python version
echo -e "\n${PURPLE}📋 Phase 1: Environment Verification${NC}"
echo "========================================"

# Use Python 3.11 which has the dependencies
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo -e "${GREEN}✅ Python 3.11 found${NC}"
else
    PYTHON_CMD="python3"
    echo -e "${YELLOW}⚠️  Using default python3${NC}"
fi

$PYTHON_CMD --version

# Check .env file
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file found${NC}"
    if grep -q "OPENAI_API_KEY" .env; then
        echo -e "${GREEN}✅ OpenAI API key configured${NC}"
    else
        echo -e "${RED}❌ OpenAI API key not found in .env${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Set environment variables
echo -e "${CYAN}🔄 Setting debug environment variables...${NC}"
export LANGGRAPH_DEBUG=true
export LANGCHAIN_VERBOSE=true
export PYTHONPATH="${PWD}/src:${PYTHONPATH:-}"

# Phase 2: Code Verification
echo -e "\n${PURPLE}📋 Phase 2: Code Verification${NC}"
echo "================================"

echo -e "${CYAN}🔄 Testing core imports${NC}"
$PYTHON_CMD -c 'from agent.graph.trading_graph import TradingAgentsGraph; print("✅ Core imports working")' 2>&1 || echo -e "${RED}❌ Core import failed${NC}"

echo -e "${CYAN}🔄 Testing debug logging imports${NC}"
$PYTHON_CMD -c 'from agent.utils.debug_logging import debug_node; print("✅ Debug logging imports working")' 2>&1 || echo -e "${RED}❌ Debug logging import failed${NC}"

echo -e "${CYAN}🔄 Testing LangChain imports${NC}"
$PYTHON_CMD -c 'from langchain_openai import ChatOpenAI; print("✅ LangChain imports working")' 2>&1 || echo -e "${RED}❌ LangChain import failed${NC}"

# Phase 3: Run simple test
echo -e "\n${PURPLE}📋 Phase 3: Simple Test${NC}"
echo "================================"

# Create a simple test script
cat > test_simple.py << 'EOF'
import os
import sys
sys.path.insert(0, 'src')

try:
    from agent.graph.trading_graph import TradingAgentsGraph
    from langchain_openai import ChatOpenAI
    print("✅ All imports successful")
    
    # Test basic instantiation
    graph = TradingAgentsGraph(
        quick_thinking_model="gpt-4o-mini",
        reasoning_model="gpt-4o-mini",
        provider="openai"
    )
    print("✅ Graph instantiation successful")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
EOF

echo -e "${CYAN}🔄 Running simple test...${NC}"
$PYTHON_CMD test_simple.py

# Cleanup
rm -f test_simple.py

echo -e "\n${PURPLE}📋 Debug Session Complete${NC}"
echo "=========================="
echo -e "${GREEN}✅ Debug session completed${NC}"